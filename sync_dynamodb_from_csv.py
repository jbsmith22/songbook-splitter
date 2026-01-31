"""
Sync DynamoDB ledger with book_reconciliation_validated.csv (source of truth).

This script:
1. Reads book_reconciliation_validated.csv (559 books)
2. Exports current DynamoDB entries (1250 entries)
3. Maps CSV entries to DynamoDB entries
4. Identifies what needs to be updated/deleted/created
"""

import boto3
import hashlib
import json
import csv
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Configuration
DYNAMODB_TABLE = 'jsmith-processing-ledger'
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
CSV_FILE = 'book_reconciliation_validated.csv'
NORMALIZATION_FILE = 'normalization_plan_fixed.csv'
LOCAL_SHEETMUSIC_BASE = r'C:\Work\AWSMusic\SheetMusic'
LOCAL_PROCESSED_BASE = r'C:\Work\AWSMusic\ProcessedSongs'


def generate_book_id(s3_uri: str) -> str:
    """Generate book_id from S3 URI (same as pipeline)."""
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def load_normalization_mapping() -> Dict[str, str]:
    """
    Load normalization_plan_fixed.csv to map old names to new names.
    
    Returns:
        Dict mapping old_path -> new_path for both PDFs and folders
    """
    print(f"Loading normalization mapping from {NORMALIZATION_FILE}...")
    
    mapping = {}
    with open(NORMALIZATION_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Needs_Rename'] == 'YES':
                old_path = row['Old_Path']
                new_path = row['New_Path']
                
                # Normalize paths for comparison
                old_path_norm = old_path.lower().replace('\\', '/')
                new_path_norm = new_path.lower().replace('\\', '/')
                
                mapping[old_path_norm] = new_path_norm
    
    print(f"Loaded {len(mapping)} path mappings")
    return mapping


def load_csv_source_of_truth() -> List[Dict]:
    """
    Load book_reconciliation_validated.csv as source of truth.
    
    Returns:
        List of 559 book records
    """
    print(f"Loading source of truth from {CSV_FILE}...")
    
    books = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only include COMPLETE books
            if row['Status'] == 'COMPLETE':
                books.append(row)
    
    print(f"Loaded {len(books)} books from CSV")
    return books


def csv_to_s3_paths(csv_row: Dict) -> Dict:
    """
    Convert CSV row to S3 paths.
    
    CSV has:
    - Artist: "Billy Joel"
    - BookName: "Billy Joel - 52nd Street"
    - SourcePath: "Billy Joel\Billy Joel - 52nd Street.pdf"
    - ProcessedPath: "Billy Joel\Billy Joel - 52nd Street"
    
    Need to generate:
    - source_pdf_s3_uri: "s3://jsmith-input/SheetMusic/Billy Joel/Billy Joel - 52nd Street.pdf"
    - output_s3_path: "s3://jsmith-output/Billy Joel/books/Billy Joel - 52nd Street/"
    """
    artist = csv_row['Artist']
    book_name = csv_row['BookName']
    source_path = csv_row['SourcePath']  # e.g., "Billy Joel\Billy Joel - 52nd Street.pdf"
    
    # Convert Windows path to S3 path
    source_s3_key = source_path.replace('\\', '/')
    source_pdf_s3_uri = f"s3://{INPUT_BUCKET}/SheetMusic/{source_s3_key}"
    
    # Output path (note: design says books/ subfolder, but actual may differ)
    # Let's check the processed path from CSV
    processed_path = csv_row['ProcessedPath']  # e.g., "Billy Joel\Billy Joel - 52nd Street"
    processed_s3_key = processed_path.replace('\\', '/')
    
    return {
        'artist': artist,
        'book_name': book_name,
        'source_pdf_s3_uri': source_pdf_s3_uri,
        'output_s3_path': f"s3://{OUTPUT_BUCKET}/{processed_s3_key}/",
        'manifest_s3_uri': f"s3://{OUTPUT_BUCKET}/{processed_s3_key}/manifest.json",
        'songs_extracted': int(csv_row['FileCount']),
        'book_id': generate_book_id(source_pdf_s3_uri)
    }


def export_current_dynamodb() -> List[Dict]:
    """Export all current DynamoDB entries."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print("\nExporting current DynamoDB ledger...")
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    print(f"Exported {len(entries)} DynamoDB entries")
    
    # Save backup
    backup_file = f'dynamodb_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w') as f:
        json.dump(entries, f, indent=2, default=str)
    print(f"Backup saved to {backup_file}")
    
    return entries


def create_mapping(csv_books: List[Dict], dynamodb_entries: List[Dict], normalization_map: Dict[str, str]) -> List[Dict]:
    """
    Map CSV books (source of truth) to DynamoDB entries.
    Uses normalization_map to match old paths to new paths.
    
    Returns:
        List of mapping records showing what needs to be done
    """
    print("\nCreating mapping between CSV and DynamoDB...")
    
    # Convert CSV to expected format
    csv_with_s3 = [csv_to_s3_paths(row) for row in csv_books]
    
    # Index DynamoDB entries by book_id
    dynamodb_by_id = {entry['book_id']: entry for entry in dynamodb_entries}
    
    # Also index by (artist, book_name) for fuzzy matching
    dynamodb_by_name = {}
    for entry in dynamodb_entries:
        key = (entry.get('artist', ''), entry.get('book_name', ''))
        if key not in dynamodb_by_name:
            dynamodb_by_name[key] = []
        dynamodb_by_name[key].append(entry)
    
    # Create reverse normalization map (new -> old) for finding old DynamoDB entries
    reverse_norm_map = {v: k for k, v in normalization_map.items()}
    
    mappings = []
    
    # For each CSV book (source of truth), find matching DynamoDB entry
    for csv_book in csv_with_s3:
        csv_book_id = csv_book['book_id']
        csv_artist = csv_book['artist']
        csv_book_name = csv_book['book_name']
        csv_source_uri = csv_book['source_pdf_s3_uri']
        
        # Try exact book_id match first
        if csv_book_id in dynamodb_by_id:
            db_entry = dynamodb_by_id[csv_book_id]
            mappings.append({
                'match_type': 'exact_id',
                'action': 'keep',
                'csv_book_id': csv_book_id,
                'csv_artist': csv_artist,
                'csv_book_name': csv_book_name,
                'csv_source_uri': csv_source_uri,
                'db_book_id': db_entry['book_id'],
                'db_artist': db_entry.get('artist', ''),
                'db_book_name': db_entry.get('book_name', ''),
                'db_source_uri': db_entry.get('source_pdf_uri', ''),
                'db_status': db_entry.get('status', ''),
                'songs_extracted': csv_book['songs_extracted'],
                'needs_update': False
            })
            continue
        
        # Try to find old path using normalization map
        # Current CSV has new path, need to find what the old path was
        csv_path_norm = csv_source_uri.lower().replace('s3://jsmith-input/sheetmusic/', '').replace('/', '\\')
        csv_full_path_norm = f"c:\\work\\awsmusic\\sheetmusic\\{csv_path_norm}".lower()
        
        # Check if this new path came from an old path
        old_path_candidate = None
        for new_path, old_path in reverse_norm_map.items():
            if csv_full_path_norm in new_path or new_path in csv_full_path_norm:
                old_path_candidate = old_path
                break
        
        # If we found an old path, generate the old book_id
        if old_path_candidate:
            # Convert old local path to old S3 URI
            old_s3_key = old_path_candidate.replace('c:\\work\\awsmusic\\sheetmusic\\', '').replace('\\', '/')
            old_s3_uri = f"s3://{INPUT_BUCKET}/SheetMusic/{old_s3_key}"
            old_book_id = generate_book_id(old_s3_uri)
            
            # Check if this old book_id exists in DynamoDB
            if old_book_id in dynamodb_by_id:
                db_entry = dynamodb_by_id[old_book_id]
                mappings.append({
                    'match_type': 'renamed_path',
                    'action': 'update',
                    'csv_book_id': csv_book_id,
                    'csv_artist': csv_artist,
                    'csv_book_name': csv_book_name,
                    'csv_source_uri': csv_source_uri,
                    'db_book_id': old_book_id,
                    'db_artist': db_entry.get('artist', ''),
                    'db_book_name': db_entry.get('book_name', ''),
                    'db_source_uri': db_entry.get('source_pdf_uri', ''),
                    'db_status': db_entry.get('status', ''),
                    'songs_extracted': csv_book['songs_extracted'],
                    'needs_update': True,
                    'reason': f'path renamed: {old_s3_uri} -> {csv_source_uri}'
                })
                continue
        
        # Try name match (artist + book_name)
        name_key = (csv_artist, csv_book_name)
        if name_key in dynamodb_by_name:
            # Found match by name but different book_id (path changed)
            db_entries = dynamodb_by_name[name_key]
            
            # Take the first one (or the one with status='success')
            db_entry = next((e for e in db_entries if e.get('status') == 'success'), db_entries[0])
            
            mappings.append({
                'match_type': 'name_match',
                'action': 'update',
                'csv_book_id': csv_book_id,
                'csv_artist': csv_artist,
                'csv_book_name': csv_book_name,
                'csv_source_uri': csv_source_uri,
                'db_book_id': db_entry['book_id'],
                'db_artist': db_entry.get('artist', ''),
                'db_book_name': db_entry.get('book_name', ''),
                'db_source_uri': db_entry.get('source_pdf_uri', ''),
                'db_status': db_entry.get('status', ''),
                'songs_extracted': csv_book['songs_extracted'],
                'needs_update': True,
                'reason': 'book_id changed (path changed)'
            })
            continue
        
        # No match found - need to create new entry
        mappings.append({
            'match_type': 'no_match',
            'action': 'create',
            'csv_book_id': csv_book_id,
            'csv_artist': csv_artist,
            'csv_book_name': csv_book_name,
            'csv_source_uri': csv_source_uri,
            'db_book_id': '',
            'db_artist': '',
            'db_book_name': '',
            'db_source_uri': '',
            'db_status': '',
            'songs_extracted': csv_book['songs_extracted'],
            'needs_update': True,
            'reason': 'not in DynamoDB'
        })
    
    # Find DynamoDB entries not in CSV (should be deleted)
    matched_db_ids = {m['db_book_id'] for m in mappings if m['db_book_id']}
    
    for db_entry in dynamodb_entries:
        db_book_id = db_entry['book_id']
        
        # Skip if already matched
        if db_book_id in matched_db_ids:
            continue
        
        # This DynamoDB entry is not in CSV - should be deleted
        mappings.append({
            'match_type': 'orphan',
            'action': 'delete',
            'csv_book_id': '',
            'csv_artist': '',
            'csv_book_name': '',
            'csv_source_uri': '',
            'db_book_id': db_book_id,
            'db_artist': db_entry.get('artist', ''),
            'db_book_name': db_entry.get('book_name', ''),
            'db_source_uri': db_entry.get('source_pdf_uri', ''),
            'db_status': db_entry.get('status', ''),
            'songs_extracted': 0,
            'needs_update': False,
            'reason': 'not in CSV (orphaned/duplicate)'
        })
    
    # Print statistics
    print(f"\nMapping statistics:")
    print(f"  Total CSV books (source of truth): {len(csv_books)}")
    print(f"  Total DynamoDB entries: {len(dynamodb_entries)}")
    print(f"  Exact ID matches (keep): {sum(1 for m in mappings if m['match_type'] == 'exact_id')}")
    print(f"  Renamed path matches (update): {sum(1 for m in mappings if m['match_type'] == 'renamed_path')}")
    print(f"  Name matches (update): {sum(1 for m in mappings if m['match_type'] == 'name_match')}")
    print(f"  No matches (create): {sum(1 for m in mappings if m['match_type'] == 'no_match')}")
    print(f"  Orphaned entries (delete): {sum(1 for m in mappings if m['match_type'] == 'orphan')}")
    
    return mappings


def save_mapping_to_csv(mappings: List[Dict], filename: str = 'dynamodb_sync_plan.csv'):
    """Save mapping to CSV for review."""
    print(f"\nSaving sync plan to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if mappings:
            writer = csv.DictWriter(f, fieldnames=mappings[0].keys())
            writer.writeheader()
            writer.writerows(mappings)
    
    print(f"Sync plan saved. Please review before applying!")


def apply_sync_plan(mappings: List[Dict], csv_books: List[Dict], dry_run: bool = True):
    """
    Apply sync plan to DynamoDB.
    
    Args:
        mappings: List of mapping records
        csv_books: Original CSV books for reference
        dry_run: If True, only print what would be done
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Applying sync plan to DynamoDB...")
    
    actions_taken = {
        'keep': 0,
        'create': 0,
        'update': 0,
        'delete': 0
    }
    
    # Convert CSV to dict for easy lookup
    csv_dict = {csv_to_s3_paths(row)['book_id']: csv_to_s3_paths(row) for row in csv_books}
    
    for mapping in mappings:
        action = mapping['action']
        
        if action == 'keep':
            # Entry is correct, no action needed
            actions_taken['keep'] += 1
        
        elif action == 'create':
            # Create new DynamoDB entry
            csv_book_id = mapping['csv_book_id']
            csv_book = csv_dict[csv_book_id]
            
            actions_taken['create'] += 1
            
            if not dry_run:
                table.put_item(Item={
                    'book_id': csv_book_id,
                    'processing_timestamp': int(datetime.now().timestamp()),
                    'status': 'success',
                    'source_pdf_uri': csv_book['source_pdf_s3_uri'],
                    'artist': csv_book['artist'],
                    'book_name': csv_book['book_name'],
                    'songs_extracted': csv_book['songs_extracted'],
                    'manifest_uri': csv_book['manifest_s3_uri']
                })
        
        elif action == 'update':
            # Delete old entry, create new one with correct book_id
            old_book_id = mapping['db_book_id']
            new_book_id = mapping['csv_book_id']
            csv_book = csv_dict[new_book_id]
            
            actions_taken['update'] += 1
            
            if not dry_run:
                # Delete old
                table.delete_item(Key={'book_id': old_book_id})
                
                # Create new
                table.put_item(Item={
                    'book_id': new_book_id,
                    'processing_timestamp': int(datetime.now().timestamp()),
                    'status': 'success',
                    'source_pdf_uri': csv_book['source_pdf_s3_uri'],
                    'artist': csv_book['artist'],
                    'book_name': csv_book['book_name'],
                    'songs_extracted': csv_book['songs_extracted'],
                    'manifest_uri': csv_book['manifest_s3_uri']
                })
        
        elif action == 'delete':
            # Delete orphaned entry
            db_book_id = mapping['db_book_id']
            
            actions_taken['delete'] += 1
            
            if not dry_run:
                table.delete_item(Key={'book_id': db_book_id})
    
    print(f"\n{'Would perform' if dry_run else 'Performed'} the following actions:")
    print(f"  - Keep (no change): {actions_taken['keep']}")
    print(f"  - Create (new): {actions_taken['create']}")
    print(f"  - Update (path changed): {actions_taken['update']}")
    print(f"  - Delete (orphaned): {actions_taken['delete']}")
    print(f"\nFinal state: {actions_taken['keep'] + actions_taken['create'] + actions_taken['update']} entries (should be 559)")
    
    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Review dynamodb_sync_plan.csv and run with dry_run=False to apply changes.")


def main():
    """Main execution."""
    print("=" * 80)
    print("DynamoDB Sync from book_reconciliation_validated.csv")
    print("=" * 80)
    
    # Step 1: Load normalization mapping
    normalization_map = load_normalization_mapping()
    
    # Step 2: Load CSV (source of truth)
    csv_books = load_csv_source_of_truth()
    
    # Step 3: Export current DynamoDB
    dynamodb_entries = export_current_dynamodb()
    
    # Step 4: Create mapping
    mappings = create_mapping(csv_books, dynamodb_entries, normalization_map)
    
    # Step 5: Save mapping for review
    save_mapping_to_csv(mappings)
    
    # Step 6: Apply sync plan (dry run first)
    apply_sync_plan(mappings, csv_books, dry_run=True)
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Review dynamodb_sync_plan.csv to verify the sync plan")
    print("2. If everything looks good, edit this script and change:")
    print("   apply_sync_plan(mappings, csv_books, dry_run=False)")
    print("3. Run the script again to apply changes")
    print("=" * 80)


if __name__ == '__main__':
    main()
