"""
Migrate DynamoDB ledger preserving old book_ids for artifact lookup.

This script:
1. Finds best matches between CSV and DynamoDB
2. Creates new entries with new book_ids
3. Preserves old book_ids in 'previous_book_id' field
4. Optionally renames S3 artifacts to new book_id paths
"""

import boto3
import hashlib
import json
import csv
from typing import Dict, List, Tuple
from difflib import SequenceMatcher
from datetime import datetime

DYNAMODB_TABLE = 'jsmith-processing-ledger'
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
CSV_FILE = 'book_reconciliation_validated.csv'


def generate_book_id(s3_uri: str) -> str:
    """Generate book_id from S3 URI."""
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def normalize_for_comparison(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    import re
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity between two strings."""
    norm1 = normalize_for_comparison(str1)
    norm2 = normalize_for_comparison(str2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def load_csv_books() -> List[Dict]:
    """Load CSV books."""
    books = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'] == 'COMPLETE':
                books.append(row)
    return books


def load_dynamodb_entries() -> List[Dict]:
    """Load all DynamoDB entries."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    return entries


def find_best_match(csv_book: Dict, dynamodb_entries: List[Dict]) -> Tuple[Dict, float]:
    """Find best matching DynamoDB entry for a CSV book."""
    csv_artist = csv_book['Artist']
    csv_book_name = csv_book['BookName']
    csv_source_path = csv_book['SourcePath']
    
    best_match = None
    best_score = 0.0
    
    for db_entry in dynamodb_entries:
        db_artist = db_entry.get('artist', '')
        db_book_name = db_entry.get('book_name', '')
        db_source_uri = db_entry.get('source_pdf_uri', '')
        
        db_path = db_source_uri.replace('s3://jsmith-input/SheetMusic/', '').replace('/', '\\')
        
        artist_sim = similarity_score(csv_artist, db_artist)
        book_name_sim = similarity_score(csv_book_name, db_book_name)
        path_sim = similarity_score(csv_source_path, db_path)
        
        combined_score = (
            artist_sim * 0.3 +
            book_name_sim * 0.5 +
            path_sim * 0.2
        )
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = db_entry
    
    return best_match, best_score


def create_migration_plan():
    """Create migration plan with old and new book_ids."""
    print("Loading data...")
    csv_books = load_csv_books()
    dynamodb_entries = load_dynamodb_entries()
    
    print(f"CSV books: {len(csv_books)}")
    print(f"DynamoDB entries: {len(dynamodb_entries)}")
    
    print("\nCreating migration plan...")
    
    migration_plan = []
    matched_db_ids = set()
    
    for i, csv_book in enumerate(csv_books, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(csv_books)}...")
        
        csv_artist = csv_book['Artist']
        csv_book_name = csv_book['BookName']
        csv_source_path = csv_book['SourcePath']
        csv_songs = int(csv_book['FileCount'])
        
        # Generate new book_id from current CSV path
        csv_s3_uri = f"s3://{INPUT_BUCKET}/SheetMusic/{csv_source_path.replace(chr(92), '/')}"
        new_book_id = generate_book_id(csv_s3_uri)
        
        # Find best match in DynamoDB
        best_match, score = find_best_match(csv_book, dynamodb_entries)
        
        if best_match:
            old_book_id = best_match['book_id']
            old_source_uri = best_match.get('source_pdf_uri', '')
            matched_db_ids.add(old_book_id)
            
            action = 'keep' if old_book_id == new_book_id else 'migrate'
            
            migration_plan.append({
                'action': action,
                'csv_artist': csv_artist,
                'csv_book_name': csv_book_name,
                'csv_source_path': csv_source_path,
                'new_book_id': new_book_id,
                'new_source_uri': csv_s3_uri,
                'old_book_id': old_book_id,
                'old_source_uri': old_source_uri,
                'match_score': f"{score:.3f}",
                'songs_extracted': csv_songs,
                'db_status': best_match.get('status', ''),
                'has_artifacts': f"s3://{OUTPUT_BUCKET}/artifacts/{old_book_id}/",
                'needs_artifact_rename': 'YES' if action == 'migrate' else 'NO'
            })
        else:
            # No match found (shouldn't happen with fuzzy matching)
            migration_plan.append({
                'action': 'create',
                'csv_artist': csv_artist,
                'csv_book_name': csv_book_name,
                'csv_source_path': csv_source_path,
                'new_book_id': new_book_id,
                'new_source_uri': csv_s3_uri,
                'old_book_id': '',
                'old_source_uri': '',
                'match_score': '0.000',
                'songs_extracted': csv_songs,
                'db_status': '',
                'has_artifacts': '',
                'needs_artifact_rename': 'NO'
            })
    
    # Find orphaned DynamoDB entries
    for db_entry in dynamodb_entries:
        db_book_id = db_entry['book_id']
        if db_book_id not in matched_db_ids:
            migration_plan.append({
                'action': 'delete',
                'csv_artist': '',
                'csv_book_name': '',
                'csv_source_path': '',
                'new_book_id': '',
                'new_source_uri': '',
                'old_book_id': db_book_id,
                'old_source_uri': db_entry.get('source_pdf_uri', ''),
                'match_score': '',
                'songs_extracted': 0,
                'db_status': db_entry.get('status', ''),
                'has_artifacts': f"s3://{OUTPUT_BUCKET}/artifacts/{db_book_id}/",
                'needs_artifact_rename': 'NO'
            })
    
    # Save migration plan
    output_file = 'dynamodb_migration_plan.csv'
    print(f"\nSaving migration plan to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if migration_plan:
            writer = csv.DictWriter(f, fieldnames=migration_plan[0].keys())
            writer.writeheader()
            writer.writerows(migration_plan)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("MIGRATION STATISTICS")
    print("=" * 80)
    
    actions = {}
    for item in migration_plan:
        action = item['action']
        actions[action] = actions.get(action, 0) + 1
    
    for action, count in sorted(actions.items()):
        print(f"  {action}: {count}")
    
    migrate_count = sum(1 for item in migration_plan if item['action'] == 'migrate')
    print(f"\n  Books needing book_id change: {migrate_count}")
    print(f"  Books with artifacts to preserve: {migrate_count}")
    
    return migration_plan


def apply_migration(migration_plan: List[Dict], dry_run: bool = True, rename_artifacts: bool = False):
    """
    Apply migration plan to DynamoDB.
    
    Args:
        migration_plan: List of migration records
        dry_run: If True, only print what would be done
        rename_artifacts: If True, also rename S3 artifacts to new book_id
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    s3 = boto3.client('s3')
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Applying migration...")
    
    actions_taken = {
        'keep': 0,
        'migrate': 0,
        'create': 0,
        'delete': 0,
        'artifacts_renamed': 0
    }
    
    for item in migration_plan:
        action = item['action']
        
        if action == 'keep':
            # Entry is correct, no action needed
            actions_taken['keep'] += 1
        
        elif action == 'migrate':
            # Update entry with new book_id, preserve old book_id
            old_book_id = item['old_book_id']
            new_book_id = item['new_book_id']
            
            actions_taken['migrate'] += 1
            
            if not dry_run:
                # Delete old entry
                table.delete_item(Key={'book_id': old_book_id})
                
                # Create new entry with previous_book_id field
                table.put_item(Item={
                    'book_id': new_book_id,
                    'previous_book_id': old_book_id,  # PRESERVE OLD ID
                    'processing_timestamp': int(datetime.now().timestamp()),
                    'status': 'success',
                    'source_pdf_uri': item['new_source_uri'],
                    'artist': item['csv_artist'],
                    'book_name': item['csv_book_name'],
                    'songs_extracted': item['songs_extracted'],
                    'manifest_uri': f"s3://{OUTPUT_BUCKET}/{item['csv_artist']}/books/{item['csv_book_name']}/manifest.json",
                    'migration_note': f"Migrated from {old_book_id} on {datetime.now().isoformat()}"
                })
                
                # Optionally rename artifacts
                if rename_artifacts:
                    try:
                        # List artifacts with old book_id
                        old_prefix = f"artifacts/{old_book_id}/"
                        new_prefix = f"artifacts/{new_book_id}/"
                        
                        response = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=old_prefix)
                        
                        if 'Contents' in response:
                            for obj in response['Contents']:
                                old_key = obj['Key']
                                new_key = old_key.replace(old_prefix, new_prefix)
                                
                                # Copy to new location
                                s3.copy_object(
                                    Bucket=OUTPUT_BUCKET,
                                    CopySource={'Bucket': OUTPUT_BUCKET, 'Key': old_key},
                                    Key=new_key
                                )
                                
                                # Delete old location
                                s3.delete_object(Bucket=OUTPUT_BUCKET, Key=old_key)
                            
                            actions_taken['artifacts_renamed'] += 1
                    except Exception as e:
                        print(f"  Warning: Failed to rename artifacts for {old_book_id}: {e}")
        
        elif action == 'create':
            # Create new entry (shouldn't happen with fuzzy matching)
            new_book_id = item['new_book_id']
            
            actions_taken['create'] += 1
            
            if not dry_run:
                table.put_item(Item={
                    'book_id': new_book_id,
                    'processing_timestamp': int(datetime.now().timestamp()),
                    'status': 'success',
                    'source_pdf_uri': item['new_source_uri'],
                    'artist': item['csv_artist'],
                    'book_name': item['csv_book_name'],
                    'songs_extracted': item['songs_extracted'],
                    'manifest_uri': f"s3://{OUTPUT_BUCKET}/{item['csv_artist']}/books/{item['csv_book_name']}/manifest.json"
                })
        
        elif action == 'delete':
            # Delete orphaned entry
            old_book_id = item['old_book_id']
            
            actions_taken['delete'] += 1
            
            if not dry_run:
                table.delete_item(Key={'book_id': old_book_id})
    
    print(f"\n{'Would perform' if dry_run else 'Performed'} the following actions:")
    print(f"  - Keep (no change): {actions_taken['keep']}")
    print(f"  - Migrate (preserve old book_id): {actions_taken['migrate']}")
    print(f"  - Create (new): {actions_taken['create']}")
    print(f"  - Delete (orphaned): {actions_taken['delete']}")
    if rename_artifacts:
        print(f"  - Artifacts renamed: {actions_taken['artifacts_renamed']}")
    
    print(f"\nFinal state: {actions_taken['keep'] + actions_taken['migrate'] + actions_taken['create']} entries (should be 559)")
    
    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Review dynamodb_migration_plan.csv and run with dry_run=False to apply changes.")


def main():
    """Main execution."""
    print("=" * 80)
    print("DynamoDB Migration with book_id History Preservation")
    print("=" * 80)
    
    # Create migration plan
    migration_plan = create_migration_plan()
    
    # Apply migration (dry run)
    apply_migration(migration_plan, dry_run=True, rename_artifacts=False)
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Review dynamodb_migration_plan.csv")
    print("2. Decide if you want to rename S3 artifacts (rename_artifacts=True)")
    print("3. Run with dry_run=False to apply changes")
    print("\nNOTE: Old book_ids will be preserved in 'previous_book_id' field")
    print("      Artifacts will remain at old paths unless rename_artifacts=True")
    print("=" * 80)


if __name__ == '__main__':
    main()
