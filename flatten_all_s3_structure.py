"""
Flatten all S3 bucket structure to: <artist>/<artist> - <book>/Songs/<filename>
Generates a CSV plan showing what will be moved and what will be deleted.
"""
import boto3
import csv
from collections import defaultdict

def parse_path(key):
    """Parse S3 key into components."""
    parts = key.split('/')
    if len(parts) < 2:
        return None
    
    # Expected: Artist/Artist - Book/Songs/filename.pdf
    # Or variations that need fixing
    artist = parts[0]
    
    # Find the filename (last part)
    filename = parts[-1]
    
    # Everything between artist and filename
    middle_parts = parts[1:-1]
    
    return {
        'artist': artist,
        'middle': middle_parts,
        'filename': filename,
        'full_path': key
    }

def determine_target_book_folder(artist, all_keys_for_artist):
    """
    Determine the preferred book folder name for an artist.
    Prefer: <Artist> - <Book> format over just <Book>
    """
    book_folders = set()
    
    for key in all_keys_for_artist:
        parts = key.split('/')
        if len(parts) >= 2:
            book_folder = parts[1]
            book_folders.add(book_folder)
    
    # Prefer folders with " - " (Artist - Book format)
    preferred = [f for f in book_folders if ' - ' in f and f.lower().startswith(artist.lower())]
    
    if preferred:
        # If multiple, pick the shortest (likely the main one)
        return sorted(preferred, key=len)[0]
    
    # Otherwise, pick any folder with " - "
    with_dash = [f for f in book_folders if ' - ' in f]
    if with_dash:
        return sorted(with_dash, key=len)[0]
    
    # Fallback: pick the most common one
    if book_folders:
        return sorted(book_folders)[0]
    
    return None

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    print("🔍 Scanning entire S3 bucket...")
    print("   This may take a few minutes...\n")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    all_keys = []
    for page in pages:
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            key = obj['Key']
            # Only process PDF files
            if key.endswith('.pdf'):
                all_keys.append(key)
    
    print(f"📊 Found {len(all_keys)} PDF files\n")
    
    # Group by artist
    by_artist = defaultdict(list)
    for key in all_keys:
        parsed = parse_path(key)
        if parsed:
            by_artist[parsed['artist']].append(key)
    
    print(f"📁 Found {len(by_artist)} artists\n")
    
    # Analyze each artist
    moves = []
    already_correct = []
    
    for artist, keys in sorted(by_artist.items()):
        # Determine target book folder
        target_book = determine_target_book_folder(artist, keys)
        
        if not target_book:
            print(f"⚠️  Skipping {artist}: No book folder found")
            continue
        
        target_prefix = f"{artist}/{target_book}/Songs/"
        
        for key in keys:
            parsed = parse_path(key)
            filename = parsed['filename']
            
            # Target path
            target_path = f"{target_prefix}{filename}"
            
            # Check if already correct
            if key == target_path:
                already_correct.append({
                    'artist': artist,
                    'book': target_book,
                    'filename': filename,
                    'current_path': key,
                    'status': 'correct'
                })
            else:
                # Needs to be moved
                moves.append({
                    'artist': artist,
                    'book': target_book,
                    'filename': filename,
                    'source_path': key,
                    'target_path': target_path,
                    'action': 'move'
                })
    
    print(f"✅ Already correct: {len(already_correct)} files")
    print(f"🔄 Need to move: {len(moves)} files\n")
    
    # Write CSV
    csv_file = 's3_flatten_plan.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'artist', 'book', 'filename', 'source_path', 'target_path', 'action'
        ])
        writer.writeheader()
        writer.writerows(moves)
    
    print(f"📄 Plan written to: {csv_file}")
    
    # Show summary by artist
    print(f"\n📊 Summary by Artist:")
    print(f"{'Artist':<30} {'Files to Move':<15} {'Target Book Folder'}")
    print("-" * 80)
    
    artist_summary = defaultdict(lambda: {'count': 0, 'book': ''})
    for move in moves:
        artist_summary[move['artist']]['count'] += 1
        artist_summary[move['artist']]['book'] = move['book']
    
    for artist in sorted(artist_summary.keys()):
        info = artist_summary[artist]
        print(f"{artist:<30} {info['count']:<15} {info['book']}")
    
    # Show sample moves
    if moves:
        print(f"\n📋 Sample moves (first 10):")
        for move in moves[:10]:
            print(f"\n   {move['filename']}")
            print(f"   FROM: {move['source_path']}")
            print(f"   TO:   {move['target_path']}")
    
    print(f"\n✅ Test run complete. Review {csv_file} before executing.")

if __name__ == '__main__':
    main()
