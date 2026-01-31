"""
Rebuild DynamoDB ledger with path mapping for reorganized files.

This script:
1. Exports current DynamoDB entries
2. Maps old paths to new paths
3. Updates or recreates entries with new book_ids
"""

import boto3
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
from datetime import datetime

# Configuration
DYNAMODB_TABLE = 'jsmith-processing-ledger'
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
LOCAL_SHEETMUSIC = r'C:\Work\AWSMusic\SheetMusic'
LOCAL_PROCESSED = r'C:\Work\AWSMusic\ProcessedSongs'


def generate_book_id(s3_uri: str) -> str:
    """Generate book_id from S3 URI (same as pipeline)."""
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def export_current_ledger() -> List[Dict]:
    """Export all current DynamoDB entries."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print("Exporting current DynamoDB ledger...")
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    print(f"Exported {len(entries)} entries")
    
    # Save to file for backup
    backup_file = f'dynamodb_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(backup_file, 'w') as f:
        json.dump(entries, f, indent=2, default=str)
    print(f"Backup saved to {backup_file}")
    
    return entries


def scan_local_files() -> Dict[str, Dict]:
    """
    Scan local SheetMusic and ProcessedSongs folders.
    
    Returns:
        Dict mapping (artist, book_name) -> file info
    """
    print("\nScanning local files...")
    
    local_books = {}
    
    # Scan SheetMusic for source PDFs
    sheetmusic_path = Path(LOCAL_SHEETMUSIC)
    if sheetmusic_path.exists():
        for artist_folder in sheetmusic_path.iterdir():
            if not artist_folder.is_dir():
                continue
            
            for pdf_file in artist_folder.glob('*.pdf'):
                book_name = pdf_file.stem  # Filename without .pdf
                
                key = (artist_folder.name, book_name)
                local_books[key] = {
                    'artist': artist_folder.name,
                    'book_name': book_name,
                    'source_pdf_path': str(pdf_file),
                    'source_pdf_s3_uri': f's3://{INPUT_BUCKET}/SheetMusic/{artist_folder.name}/{pdf_file.name}',
                    'has_source': True
                }
    
    # Scan ProcessedSongs for output folders
    processed_path = Path(LOCAL_PROCESSED)
    if processed_path.exists():
        for artist_folder in processed_path.iterdir():
            if not artist_folder.is_dir():
                continue
            
            for book_folder in artist_folder.iterdir():
                if not book_folder.is_dir():
                    continue
                
                # Count songs in folder
                song_files = list(book_folder.glob('*.pdf'))
                
                key = (artist_folder.name, book_folder.name)
                if key in local_books:
                    local_books[key]['has_output'] = True
                    local_books[key]['songs_extracted'] = len(song_files)
                    local_books[key]['output_folder'] = str(book_folder)
                else:
                    # Output exists but no source PDF
                    local_books[key] = {
                        'artist': artist_folder.name,
                        'book_name': book_folder.name,
                        'has_source': False,
                        'has_output': True,
                        'songs_extracted': len(song_files),
                        'output_folder': str(book_folder)
                    }
    
    print(f"Found {len(local_books)} unique books locally")
    return local_books


def create_path_mapping(old_entries: List[Dict], local_books: Dict) -> List[Dict]:
    """
    Create mapping between old DynamoDB entries and new local paths.
    
    Returns:
        List of mapping records with old and new information
    """
    print("\nCreating path mapping...")
    
    mappings = []
    
    # Try to match old entries to new local files
    for entry in old_entries:
        old_uri = entry.get('source_pdf_uri', '')
        old_artist = entry.get('artist', '')
        old_book_name = entry.get('book_name', '')
        old_book_id = entry.get('book_id', '')
        
        # Try exact match first
        key = (old_artist, old_book_name)
        if key in local_books:
            new_info = local_books[key]
            
            # Skip if no source PDF (output only)
            if not new_info.get('has_source') or not new_info.get('source_pdf_s3_uri'):
                # Has output but no source - keep old entry or mark for review
                mappings.append({
                    'match_type': 'output_only',
                    'old_book_id': old_book_id,
                    'old_uri': old_uri,
                    'old_artist': old_artist,
                    'old_book_name': old_book_name,
                    'new_book_id': old_book_id,  # Keep same
                    'new_uri': old_uri,  # Keep same
                    'new_artist': new_info['artist'],
                    'new_book_name': new_info['book_name'],
                    'songs_extracted': entry.get('songs_extracted', new_info.get('songs_extracted', 0)),
                    'status': entry.get('status', 'success'),
                    'book_id_changed': False
                })
                continue
            
            new_book_id = generate_book_id(new_info['source_pdf_s3_uri'])
            
            mappings.append({
                'match_type': 'exact',
                'old_book_id': old_book_id,
                'old_uri': old_uri,
                'old_artist': old_artist,
                'old_book_name': old_book_name,
                'new_book_id': new_book_id,
                'new_uri': new_info.get('source_pdf_s3_uri', ''),
                'new_artist': new_info['artist'],
                'new_book_name': new_info['book_name'],
                'songs_extracted': entry.get('songs_extracted', new_info.get('songs_extracted', 0)),
                'status': entry.get('status', 'success'),
                'book_id_changed': old_book_id != new_book_id
            })
            continue
        
        # Try fuzzy match (normalized names)
        matched = False
        for local_key, local_info in local_books.items():
            local_artist, local_book = local_key
            
            # Normalize for comparison
            if (normalize_name(old_artist) == normalize_name(local_artist) and
                normalize_name(old_book_name) == normalize_name(local_book)):
                
                # Skip if no source PDF
                if not local_info.get('has_source') or not local_info.get('source_pdf_s3_uri'):
                    mappings.append({
                        'match_type': 'output_only',
                        'old_book_id': old_book_id,
                        'old_uri': old_uri,
                        'old_artist': old_artist,
                        'old_book_name': old_book_name,
                        'new_book_id': old_book_id,
                        'new_uri': old_uri,
                        'new_artist': local_info['artist'],
                        'new_book_name': local_info['book_name'],
                        'songs_extracted': entry.get('songs_extracted', local_info.get('songs_extracted', 0)),
                        'status': entry.get('status', 'success'),
                        'book_id_changed': False
                    })
                    matched = True
                    break
                
                new_book_id = generate_book_id(local_info['source_pdf_s3_uri'])
                
                mappings.append({
                    'match_type': 'fuzzy',
                    'old_book_id': old_book_id,
                    'old_uri': old_uri,
                    'old_artist': old_artist,
                    'old_book_name': old_book_name,
                    'new_book_id': new_book_id,
                    'new_uri': local_info.get('source_pdf_s3_uri', ''),
                    'new_artist': local_info['artist'],
                    'new_book_name': local_info['book_name'],
                    'songs_extracted': entry.get('songs_extracted', local_info.get('songs_extracted', 0)),
                    'status': entry.get('status', 'success'),
                    'book_id_changed': old_book_id != new_book_id
                })
                matched = True
                break
        
        if not matched:
            # No match found - book was deleted or renamed significantly
            mappings.append({
                'match_type': 'no_match',
                'old_book_id': old_book_id,
                'old_uri': old_uri,
                'old_artist': old_artist,
                'old_book_name': old_book_name,
                'new_book_id': '',
                'new_uri': '',
                'new_artist': '',
                'new_book_name': '',
                'songs_extracted': entry.get('songs_extracted', 0),
                'status': entry.get('status', 'unknown'),
                'book_id_changed': True
            })
    
    # Find local books not in DynamoDB
    matched_keys = {(m['new_artist'], m['new_book_name']) for m in mappings if m['match_type'] not in ['no_match', 'output_only']}
    for local_key, local_info in local_books.items():
        if local_key not in matched_keys and local_info.get('has_source') and local_info.get('source_pdf_s3_uri'):
            new_book_id = generate_book_id(local_info['source_pdf_s3_uri'])
            
            mappings.append({
                'match_type': 'new_local',
                'old_book_id': '',
                'old_uri': '',
                'old_artist': '',
                'old_book_name': '',
                'new_book_id': new_book_id,
                'new_uri': local_info['source_pdf_s3_uri'],
                'new_artist': local_info['artist'],
                'new_book_name': local_info['book_name'],
                'songs_extracted': local_info.get('songs_extracted', 0),
                'status': 'success' if local_info.get('has_output') else 'not_processed',
                'book_id_changed': True
            })
    
    print(f"Created {len(mappings)} mapping records")
    print(f"  - Exact matches: {sum(1 for m in mappings if m['match_type'] == 'exact')}")
    print(f"  - Fuzzy matches: {sum(1 for m in mappings if m['match_type'] == 'fuzzy')}")
    print(f"  - Output only (no source): {sum(1 for m in mappings if m['match_type'] == 'output_only')}")
    print(f"  - No matches (deleted): {sum(1 for m in mappings if m['match_type'] == 'no_match')}")
    print(f"  - New local files: {sum(1 for m in mappings if m['match_type'] == 'new_local')}")
    print(f"  - book_id changed: {sum(1 for m in mappings if m['book_id_changed'])}")
    
    return mappings


def normalize_name(name: str) -> str:
    """Normalize name for comparison (lowercase, no spaces/punctuation)."""
    import re
    return re.sub(r'[^a-z0-9]', '', name.lower())


def save_mapping_to_csv(mappings: List[Dict], filename: str = 'path_mapping.csv'):
    """Save mapping to CSV for review."""
    print(f"\nSaving mapping to {filename}...")
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        if mappings:
            writer = csv.DictWriter(f, fieldnames=mappings[0].keys())
            writer.writeheader()
            writer.writerows(mappings)
    
    print(f"Mapping saved. Please review before applying changes!")


def apply_mapping_to_dynamodb(mappings: List[Dict], dry_run: bool = True):
    """
    Apply mapping to DynamoDB.
    
    Args:
        mappings: List of mapping records
        dry_run: If True, only print what would be done
    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Applying mapping to DynamoDB...")
    
    actions = {
        'delete': [],
        'update': [],
        'create': []
    }
    
    for mapping in mappings:
        match_type = mapping['match_type']
        old_book_id = mapping['old_book_id']
        new_book_id = mapping['new_book_id']
        book_id_changed = mapping['book_id_changed']
        
        if match_type == 'no_match':
            # Delete old entry (book was deleted locally)
            if old_book_id:
                actions['delete'].append(old_book_id)
                if not dry_run:
                    table.delete_item(Key={'book_id': old_book_id})
        
        elif match_type in ['exact', 'fuzzy', 'output_only']:
            if book_id_changed:
                # book_id changed - delete old, create new
                if old_book_id:
                    actions['delete'].append(old_book_id)
                    if not dry_run:
                        table.delete_item(Key={'book_id': old_book_id})
                
                if new_book_id and mapping['status'] == 'success':
                    actions['create'].append(new_book_id)
                    if not dry_run:
                        table.put_item(Item={
                            'book_id': new_book_id,
                            'processing_timestamp': int(datetime.now().timestamp()),
                            'status': 'success',
                            'source_pdf_uri': mapping['new_uri'],
                            'artist': mapping['new_artist'],
                            'book_name': mapping['new_book_name'],
                            'songs_extracted': mapping['songs_extracted'],
                            'manifest_uri': f"s3://{OUTPUT_BUCKET}/{mapping['new_artist']}/books/{mapping['new_book_name']}/manifest.json"
                        })
            else:
                # book_id same - just update if needed
                if mapping['status'] == 'success':
                    actions['update'].append(new_book_id)
                    # Entry is already correct, no update needed
        
        elif match_type == 'new_local':
            # New local file - create entry if it has output
            if new_book_id and mapping['status'] == 'success':
                actions['create'].append(new_book_id)
                if not dry_run:
                    table.put_item(Item={
                        'book_id': new_book_id,
                        'processing_timestamp': int(datetime.now().timestamp()),
                        'status': 'success',
                        'source_pdf_uri': mapping['new_uri'],
                        'artist': mapping['new_artist'],
                        'book_name': mapping['new_book_name'],
                        'songs_extracted': mapping['songs_extracted'],
                        'manifest_uri': f"s3://{OUTPUT_BUCKET}/{mapping['new_artist']}/books/{mapping['new_book_name']}/manifest.json"
                    })
    
    print(f"\n{'Would perform' if dry_run else 'Performed'} the following actions:")
    print(f"  - Delete: {len(actions['delete'])} entries")
    print(f"  - Update: {len(actions['update'])} entries")
    print(f"  - Create: {len(actions['create'])} entries")
    
    if dry_run:
        print("\nThis was a DRY RUN. No changes were made.")
        print("Review path_mapping.csv and run with dry_run=False to apply changes.")


def main():
    """Main execution."""
    print("=" * 80)
    print("DynamoDB Ledger Rebuild with Path Mapping")
    print("=" * 80)
    
    # Step 1: Export current ledger
    old_entries = export_current_ledger()
    
    # Step 2: Scan local files
    local_books = scan_local_files()
    
    # Step 3: Create mapping
    mappings = create_path_mapping(old_entries, local_books)
    
    # Step 4: Save mapping for review
    save_mapping_to_csv(mappings)
    
    # Step 5: Apply mapping (dry run first)
    apply_mapping_to_dynamodb(mappings, dry_run=True)
    
    print("\n" + "=" * 80)
    print("NEXT STEPS:")
    print("1. Review path_mapping.csv to verify the mappings are correct")
    print("2. If everything looks good, run:")
    print("   apply_mapping_to_dynamodb(mappings, dry_run=False)")
    print("=" * 80)


if __name__ == '__main__':
    main()
