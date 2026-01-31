"""
Update source_pdf_uri in DynamoDB to match new paths, keeping old book_ids.

This is the SIMPLEST approach:
- Keep existing book_ids (no changes to artifacts or manifests needed)
- Just update source_pdf_uri to point to new locations
- Update artist and book_name if they changed
"""

import boto3
import csv
from typing import Dict, List
from difflib import SequenceMatcher
from datetime import datetime

DYNAMODB_TABLE = 'jsmith-processing-ledger'
INPUT_BUCKET = 'jsmith-input'
CSV_FILE = 'book_reconciliation_validated.csv'


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


def find_best_match(csv_book: Dict, dynamodb_entries: List[Dict]):
    """
    Find best matching DynamoDB entry.
    
    Prioritizes entries with status='success' since CSV books are all complete.
    If multiple matches exist, prefers the successful one.
    """
    csv_artist = csv_book['Artist']
    csv_book_name = csv_book['BookName']
    csv_source_path = csv_book['SourcePath']
    
    # Find all candidates with their scores
    candidates = []
    
    for db_entry in dynamodb_entries:
        db_artist = db_entry.get('artist', '')
        db_book_name = db_entry.get('book_name', '')
        db_source_uri = db_entry.get('source_pdf_uri', '')
        db_status = db_entry.get('status', '')
        
        db_path = db_source_uri.replace('s3://jsmith-input/SheetMusic/', '').replace('/', '\\')
        
        artist_sim = similarity_score(csv_artist, db_artist)
        book_name_sim = similarity_score(csv_book_name, db_book_name)
        path_sim = similarity_score(csv_source_path, db_path)
        
        combined_score = (
            artist_sim * 0.3 +
            book_name_sim * 0.5 +
            path_sim * 0.2
        )
        
        # Only consider reasonable matches (>0.7 similarity)
        if combined_score > 0.7:
            candidates.append({
                'entry': db_entry,
                'score': combined_score,
                'status': db_status
            })
    
    if not candidates:
        return None, 0.0
    
    # Sort by score (descending)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # If top candidate is 'success', use it
    if candidates[0]['status'] == 'success':
        return candidates[0]['entry'], candidates[0]['score']
    
    # Otherwise, look for a 'success' entry among high-scoring candidates
    # (within 0.05 of the top score)
    top_score = candidates[0]['score']
    for candidate in candidates:
        if candidate['status'] == 'success' and candidate['score'] >= top_score - 0.05:
            return candidate['entry'], candidate['score']
    
    # No success entry found, return the best match regardless of status
    return candidates[0]['entry'], candidates[0]['score']


def create_update_plan():
    """Create plan to update DynamoDB paths."""
    print("Loading data...")
    csv_books = load_csv_books()
    dynamodb_entries = load_dynamodb_entries()
    
    print(f"CSV books: {len(csv_books)}")
    print(f"DynamoDB entries: {len(dynamodb_entries)}")
    
    print("\nCreating update plan...")
    
    update_plan = []
    matched_db_ids = set()
    
    for i, csv_book in enumerate(csv_books, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(csv_books)}...")
        
        csv_artist = csv_book['Artist']
        csv_book_name = csv_book['BookName']
        csv_source_path = csv_book['SourcePath']
        
        # New S3 URI from CSV
        new_s3_uri = f"s3://{INPUT_BUCKET}/SheetMusic/{csv_source_path.replace(chr(92), '/')}"
        
        # Find best match in DynamoDB
        best_match, score = find_best_match(csv_book, dynamodb_entries)
        
        if best_match:
            book_id = best_match['book_id']  # KEEP THE OLD BOOK_ID
            old_source_uri = best_match.get('source_pdf_uri', '')
            old_artist = best_match.get('artist', '')
            old_book_name = best_match.get('book_name', '')
            
            matched_db_ids.add(book_id)
            
            # Determine what needs updating
            needs_update = (
                old_source_uri != new_s3_uri or
                old_artist != csv_artist or
                old_book_name != csv_book_name or
                best_match.get('status') != 'success'  # Fix failed status
            )
            
            update_plan.append({
                'action': 'update' if needs_update else 'keep',
                'book_id': book_id,  # UNCHANGED
                'old_source_uri': old_source_uri,
                'new_source_uri': new_s3_uri,
                'old_artist': old_artist,
                'new_artist': csv_artist,
                'old_book_name': old_book_name,
                'new_book_name': csv_book_name,
                'old_status': best_match.get('status', ''),
                'new_status': 'success',  # All CSV books are complete
                'match_score': f"{score:.3f}",
                'uri_changed': 'YES' if old_source_uri != new_s3_uri else 'NO',
                'artist_changed': 'YES' if old_artist != csv_artist else 'NO',
                'book_name_changed': 'YES' if old_book_name != csv_book_name else 'NO',
                'status_changed': 'YES' if best_match.get('status') != 'success' else 'NO'
            })
    
    # Find orphaned entries
    for db_entry in dynamodb_entries:
        db_book_id = db_entry['book_id']
        if db_book_id not in matched_db_ids:
            update_plan.append({
                'action': 'delete',
                'book_id': db_book_id,
                'old_source_uri': db_entry.get('source_pdf_uri', ''),
                'new_source_uri': '',
                'old_artist': db_entry.get('artist', ''),
                'new_artist': '',
                'old_book_name': db_entry.get('book_name', ''),
                'new_book_name': '',
                'old_status': db_entry.get('status', ''),
                'new_status': '',
                'match_score': '',
                'uri_changed': '',
                'artist_changed': '',
                'book_name_changed': '',
                'status_changed': ''
            })
    
    # Save plan
    output_file = 'dynamodb_path_update_plan.csv'
    print(f"\nSaving update plan to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if update_plan:
            writer = csv.DictWriter(f, fieldnames=update_plan[0].keys())
            writer.writeheader()
            writer.writerows(update_plan)
    
    # Statistics
    print("\n" + "=" * 80)
    print("UPDATE STATISTICS")
    print("=" * 80)
    
    actions = {}
    for item in update_plan:
        action = item['action']
        actions[action] = actions.get(action, 0) + 1
    
    for action, count in sorted(actions.items()):
        print(f"  {action}: {count}")
    
    uri_changes = sum(1 for item in update_plan if item.get('uri_changed') == 'YES')
    artist_changes = sum(1 for item in update_plan if item.get('artist_changed') == 'YES')
    book_name_changes = sum(1 for item in update_plan if item.get('book_name_changed') == 'YES')
    status_changes = sum(1 for item in update_plan if item.get('status_changed') == 'YES')
    
    print(f"\n  URI changes: {uri_changes}")
    print(f"  Artist changes: {artist_changes}")
    print(f"  Book name changes: {book_name_changes}")
    print(f"  Status fixes (failed -> success): {status_changes}")
    
    return update_plan


def apply_updates(update_plan: List[Dict], dry_run: bool = True):
    """Apply updates to DynamoDB."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Applying updates...")
    
    actions_taken = {
        'keep': 0,
        'update': 0,
        'delete': 0
    }
    
    for item in update_plan:
        action = item['action']
        book_id = item['book_id']
        
        if action == 'keep':
            actions_taken['keep'] += 1
        
        elif action == 'update':
            actions_taken['update'] += 1
            
            if not dry_run:
                # Update the entry (keeping the same book_id)
                update_expr_parts = []
                expr_attr_names = {}
                expr_attr_values = {}
                
                if item['uri_changed'] == 'YES':
                    update_expr_parts.append('#uri = :uri')
                    expr_attr_names['#uri'] = 'source_pdf_uri'
                    expr_attr_values[':uri'] = item['new_source_uri']
                
                if item['artist_changed'] == 'YES':
                    update_expr_parts.append('#artist = :artist')
                    expr_attr_names['#artist'] = 'artist'
                    expr_attr_values[':artist'] = item['new_artist']
                
                if item['book_name_changed'] == 'YES':
                    update_expr_parts.append('#book_name = :book_name')
                    expr_attr_names['#book_name'] = 'book_name'
                    expr_attr_values[':book_name'] = item['new_book_name']
                
                if item.get('status_changed') == 'YES':
                    update_expr_parts.append('#status = :status')
                    expr_attr_names['#status'] = 'status'
                    expr_attr_values[':status'] = 'success'
                
                if update_expr_parts:
                    update_expr_parts.append('#updated = :updated')
                    expr_attr_names['#updated'] = 'last_updated'
                    expr_attr_values[':updated'] = datetime.now().isoformat()
                    
                    update_expr = 'SET ' + ', '.join(update_expr_parts)
                    
                    table.update_item(
                        Key={'book_id': book_id},
                        UpdateExpression=update_expr,
                        ExpressionAttributeNames=expr_attr_names,
                        ExpressionAttributeValues=expr_attr_values
                    )
        
        elif action == 'delete':
            actions_taken['delete'] += 1
            
            if not dry_run:
                table.delete_item(Key={'book_id': book_id})
    
    print(f"\n{'Would perform' if dry_run else 'Performed'} the following actions:")
    print(f"  - Keep (no change): {actions_taken['keep']}")
    print(f"  - Update (path/name changed): {actions_taken['update']}")
    print(f"  - Delete (orphaned): {actions_taken['delete']}")
    
    print(f"\nFinal state: {actions_taken['keep'] + actions_taken['update']} entries (should be 559)")
    
    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Review dynamodb_path_update_plan.csv and run with dry_run=False to apply.")


def main():
    """Main execution."""
    print("=" * 80)
    print("DynamoDB Path Update (Keep Existing book_ids)")
    print("=" * 80)
    print("\nThis approach:")
    print("  - Keeps all existing book_ids (no artifact migration needed)")
    print("  - Updates source_pdf_uri to new paths")
    print("  - Updates artist/book_name if changed")
    print("  - Artifacts remain at: s3://jsmith-output/artifacts/<old_book_id>/")
    print("=" * 80)
    
    # Create update plan
    update_plan = create_update_plan()
    
    # Apply updates (LIVE RUN)
    apply_updates(update_plan, dry_run=False)
    
    print("\n" + "=" * 80)
    print("UPDATES APPLIED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == '__main__':
    main()
