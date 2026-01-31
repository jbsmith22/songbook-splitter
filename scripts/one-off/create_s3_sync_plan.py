"""
Create a plan to sync S3 with local structure:
1. Identify correct S3 folders (those matching local)
2. Rename them to match new naming conventions
3. Delete duplicate/incorrect folders
4. Fix the 7 Billy Joel path duplication files
"""
import csv
import boto3
from collections import defaultdict

def load_matches():
    """Load the S3-to-local matches."""
    matches = []
    
    with open('s3_local_matches.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    
    return matches

def load_s3_structure():
    """Load complete S3 structure."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    print("Loading S3 structure...")
    paginator = s3.get_paginator('list_objects_v2')
    
    all_objects = []
    for page in paginator.paginate(Bucket='jsmith-output'):
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    
    # Group by artist/book
    structure = defaultdict(lambda: defaultdict(list))
    
    for obj in all_objects:
        key = obj['Key']
        
        # Skip artifacts
        if key.startswith('artifacts/'):
            continue
        
        # Parse path
        parts = key.split('/')
        if len(parts) < 2:
            continue
        
        artist = parts[0]
        book = parts[1]
        
        structure[artist][book].append({
            'key': key,
            'size': obj['Size']
        })
    
    return structure

def create_sync_plan(matches, s3_structure):
    """Create sync plan based on matches."""
    
    # Track which S3 folders to keep
    folders_to_keep = set()
    folders_to_delete = set()
    
    # Track rename operations
    rename_operations = []
    
    # Track delete operations
    delete_operations = []
    
    for match in matches:
        local_artist = match['local_artist']
        local_book = match['local_book']
        s3_artist = match['s3_artist']
        s3_book = match['s3_book']
        match_quality = match['match_quality']
        
        # Skip if no match or poor match
        if match_quality in ['NO MATCH', 'POOR']:
            continue
        
        # This is the correct S3 folder
        correct_folder = f"{s3_artist}/{s3_book}"
        folders_to_keep.add(correct_folder)
        
        # Check if it needs renaming
        expected_folder = f"{local_artist}/{local_book}"
        
        if correct_folder != expected_folder:
            # Need to rename
            rename_operations.append({
                'from_artist': s3_artist,
                'from_book': s3_book,
                'to_artist': local_artist,
                'to_book': local_book,
                'match_quality': match_quality,
                'song_count': match['s3_song_count']
            })
    
    # Find all folders to delete (not in keep list)
    for artist, books in s3_structure.items():
        for book in books.keys():
            folder = f"{artist}/{book}"
            if folder not in folders_to_keep:
                # Check if it's a duplicate of a kept folder
                is_duplicate = False
                for kept_folder in folders_to_keep:
                    kept_artist, kept_book = kept_folder.split('/', 1)
                    if artist == kept_artist and book.lower().replace(' ', '') == kept_book.lower().replace(' ', ''):
                        is_duplicate = True
                        break
                
                delete_operations.append({
                    'artist': artist,
                    'book': book,
                    'is_duplicate': is_duplicate,
                    'file_count': len(s3_structure[artist][book])
                })
    
    return rename_operations, delete_operations

def main():
    print("Creating S3 Sync Plan")
    print("="*80)
    
    # Load matches
    matches = load_matches()
    print(f"Loaded {len(matches)} local books")
    
    # Load S3 structure
    s3_structure = load_s3_structure()
    s3_folder_count = sum(len(books) for books in s3_structure.values())
    print(f"Loaded {s3_folder_count} S3 folders")
    
    # Create sync plan
    rename_ops, delete_ops = create_sync_plan(matches, s3_structure)
    
    print("\n" + "="*80)
    print("SYNC PLAN SUMMARY")
    print("="*80)
    
    print(f"\nFolders to rename:  {len(rename_ops)}")
    print(f"Folders to delete:  {len(delete_ops)}")
    print(f"Folders to keep:    {s3_folder_count - len(delete_ops)}")
    
    # Calculate file counts
    total_files_to_delete = sum(int(op['file_count']) for op in delete_ops)
    print(f"\nFiles to delete:    {total_files_to_delete}")
    
    # Save rename operations
    with open('s3_rename_plan.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'from_artist', 'from_book', 'to_artist', 'to_book',
            'match_quality', 'song_count'
        ])
        writer.writeheader()
        writer.writerows(rename_ops)
    
    print(f"\nRename plan saved to: s3_rename_plan.csv")
    
    # Save delete operations
    with open('s3_delete_plan.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'artist', 'book', 'is_duplicate', 'file_count'
        ])
        writer.writeheader()
        writer.writerows(delete_ops)
    
    print(f"Delete plan saved to: s3_delete_plan.csv")
    
    # Show examples
    print("\n" + "="*80)
    print("EXAMPLE RENAME OPERATIONS (first 10)")
    print("="*80)
    
    for op in rename_ops[:10]:
        print(f"\n{op['from_artist']}/{op['from_book']}")
        print(f"  → {op['to_artist']}/{op['to_book']}")
        print(f"  Quality: {op['match_quality']}, Songs: {op['song_count']}")
    
    print("\n" + "="*80)
    print("EXAMPLE DELETE OPERATIONS (first 10)")
    print("="*80)
    
    for op in delete_ops[:10]:
        dup_status = "DUPLICATE" if op['is_duplicate'] else "NO MATCH"
        print(f"{op['artist']}/{op['book']} ({op['file_count']} files) - {dup_status}")
    
    # Special handling for Billy Joel path duplication bug
    print("\n" + "="*80)
    print("SPECIAL: Billy Joel Path Duplication Bug")
    print("="*80)
    print("7 files with 's3://jsmith-output/' prefix need special handling")
    print("These will be moved separately")

if __name__ == '__main__':
    main()
