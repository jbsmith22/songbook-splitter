"""
Flatten S3 structure to: <artist>/<artist> - <book>/<filename>
NO Songs folder - files directly under the book folder.
"""
import boto3
import csv
from collections import defaultdict

def is_correct_structure(key):
    """
    Check if file is in correct structure: <artist>/<book>/<filename>.pdf
    Returns True if correct, False if needs fixing.
    """
    parts = key.split('/')
    
    # Correct structure has exactly 3 parts: artist, book, filename
    if len(parts) == 3 and parts[2].endswith('.pdf'):
        return True
    
    return False

def parse_incorrect_path(key):
    """Parse an incorrect path to extract artist, book, and filename."""
    parts = key.split('/')
    
    if len(parts) < 3:
        return None
    
    artist = parts[0]
    filename = parts[-1]  # Last part is always the filename
    
    # Middle parts are the book folder(s) - may be nested
    middle_parts = parts[1:-1]
    
    return {
        'artist': artist,
        'middle_parts': middle_parts,
        'filename': filename,
        'full_path': key,
        'depth': len(parts)
    }

def determine_target_book(artist, all_incorrect_keys):
    """
    Determine the correct book folder name for an artist.
    Prefer: <Artist> - <Book> format
    """
    book_candidates = set()
    
    for key in all_incorrect_keys:
        parsed = parse_incorrect_path(key)
        if parsed:
            # Look at the first folder after artist (the book folder)
            if parsed['middle_parts']:
                book_candidates.add(parsed['middle_parts'][0])
    
    # Prefer folders with " - " that start with artist name
    preferred = [b for b in book_candidates if ' - ' in b and b.lower().startswith(artist.lower())]
    if preferred:
        return sorted(preferred, key=len)[0]
    
    # Otherwise, prefer any folder with " - "
    with_dash = [b for b in book_candidates if ' - ' in b]
    if with_dash:
        return sorted(with_dash, key=len)[0]
    
    # Fallback to most common
    if book_candidates:
        return sorted(book_candidates)[0]
    
    return None

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    print("🔍 Scanning S3 bucket for incorrect structure...")
    print("   Target: <artist>/<book>/<filename>.pdf (NO Songs folder)\n")
    
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    correct_files = []
    incorrect_files = []
    
    for page in pages:
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            key = obj['Key']
            if key.endswith('.pdf'):
                if is_correct_structure(key):
                    correct_files.append(key)
                else:
                    incorrect_files.append(key)
    
    print(f"✅ Already correct: {len(correct_files)} files")
    print(f"❌ Need fixing: {len(incorrect_files)} files\n")
    
    if len(incorrect_files) == 0:
        print("🎉 All files are already in correct structure!")
        return
    
    # Group incorrect files by artist
    by_artist = defaultdict(list)
    for key in incorrect_files:
        parsed = parse_incorrect_path(key)
        if parsed:
            by_artist[parsed['artist']].append(key)
    
    # Build move plan
    moves = []
    
    for artist, keys in sorted(by_artist.items()):
        target_book = determine_target_book(artist, keys)
        
        if not target_book:
            print(f"⚠️  Skipping {artist}: Cannot determine book folder")
            continue
        
        for key in keys:
            parsed = parse_incorrect_path(key)
            if not parsed:
                continue
            
            filename = parsed['filename']
            target_path = f"{artist}/{target_book}/{filename}"
            
            # Only add if actually different
            if key != target_path:
                moves.append({
                    'artist': artist,
                    'book': target_book,
                    'filename': filename,
                    'source_path': key,
                    'target_path': target_path,
                    'source_depth': parsed['depth'],
                    'issue': 'nested' if parsed['depth'] > 3 else 'has_songs_folder'
                })
    
    print(f"🔄 Files to move: {len(moves)}\n")
    
    # Write CSV
    csv_file = 's3_flatten_plan_no_songs.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'artist', 'book', 'filename', 'source_path', 'target_path', 'source_depth', 'issue'
        ])
        writer.writeheader()
        writer.writerows(moves)
    
    print(f"📄 Plan written to: {csv_file}")
    
    # Summary by artist
    print(f"\n📊 Summary by Artist:")
    print(f"{'Artist':<30} {'Files to Move':<15} {'Target Book'}")
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
            print(f"   Issue: {move['issue']} (depth: {move['source_depth']})")
    
    print(f"\n✅ Test run complete. Review {csv_file}")

if __name__ == '__main__':
    main()
