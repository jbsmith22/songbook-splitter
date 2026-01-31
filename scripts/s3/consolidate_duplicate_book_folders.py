"""
Consolidate duplicate book folders in S3.
Find pairs: <artist>/<book>/ and <artist>/<artist> - <book>/
Consolidate into the <artist>/<artist> - <book>/ folder (preferred format).
"""
import boto3
import csv
from collections import defaultdict
import os

def normalize_book_name(book_folder, artist):
    """Remove artist prefix from book folder name for comparison."""
    # Remove artist prefix if present
    if book_folder.lower().startswith(artist.lower() + ' - '):
        return book_folder[len(artist) + 3:]  # Remove "Artist - "
    return book_folder

def find_duplicate_book_folders(all_keys):
    """
    Find pairs of book folders:
    - <artist>/<book>/
    - <artist>/<artist> - <book>/
    """
    # Group files by artist and book
    by_artist_book = defaultdict(lambda: defaultdict(list))
    
    for key in all_keys:
        parts = key.split('/')
        if len(parts) < 3:
            continue
        
        artist = parts[0]
        book_folder = parts[1]
        
        # Normalize book name for grouping
        normalized_book = normalize_book_name(book_folder, artist)
        
        by_artist_book[artist][normalized_book].append({
            'key': key,
            'book_folder': book_folder,
            'filename': parts[-1],
            'has_artist_prefix': book_folder.lower().startswith(artist.lower() + ' - ')
        })
    
    # Find artists with duplicate book folders
    duplicates = {}
    
    for artist, books in by_artist_book.items():
        for normalized_book, files in books.items():
            # Check if we have both versions
            has_with_prefix = any(f['has_artist_prefix'] for f in files)
            has_without_prefix = any(not f['has_artist_prefix'] for f in files)
            
            if has_with_prefix and has_without_prefix:
                # Get the actual folder names
                with_prefix = next(f['book_folder'] for f in files if f['has_artist_prefix'])
                without_prefix = next(f['book_folder'] for f in files if not f['has_artist_prefix'])
                
                if artist not in duplicates:
                    duplicates[artist] = []
                
                duplicates[artist].append({
                    'normalized_book': normalized_book,
                    'preferred_folder': with_prefix,
                    'other_folder': without_prefix,
                    'files': files
                })
    
    return duplicates

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    print("🔍 Scanning S3 for duplicate book folders...")
    print("   Looking for pairs: <artist>/<book>/ and <artist>/<artist> - <book>/\n")
    
    # Get all PDF files
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    all_keys = []
    for page in pages:
        if 'Contents' not in page:
            continue
        for obj in page['Contents']:
            key = obj['Key']
            if key.endswith('.pdf'):
                all_keys.append(key)
    
    print(f"📊 Found {len(all_keys)} PDF files\n")
    
    # Find duplicate book folders
    duplicates = find_duplicate_book_folders(all_keys)
    
    print(f"📁 Found {len(duplicates)} artists with duplicate book folders\n")
    
    # Build consolidation plan
    moves = []
    deletes = []
    
    for artist, book_pairs in sorted(duplicates.items()):
        for pair in book_pairs:
            preferred = pair['preferred_folder']
            other = pair['other_folder']
            
            # Group files by filename
            files_by_name = defaultdict(list)
            for file_info in pair['files']:
                filename = file_info['filename']
                files_by_name[filename].append(file_info)
            
            # Analyze each filename
            for filename, versions in files_by_name.items():
                # Get file sizes
                preferred_version = next((v for v in versions if v['book_folder'] == preferred), None)
                other_version = next((v for v in versions if v['book_folder'] == other), None)
                
                if other_version and not preferred_version:
                    # File only in other folder - move it
                    source = other_version['key']
                    target = f"{artist}/{preferred}/{filename}"
                    
                    # Get size
                    try:
                        obj = s3.head_object(Bucket=bucket, Key=source)
                        size = obj['ContentLength']
                    except:
                        size = 0
                    
                    moves.append({
                        'artist': artist,
                        'preferred_book': preferred,
                        'other_book': other,
                        'filename': filename,
                        'source_path': source,
                        'target_path': target,
                        'reason': 'unique_in_other',
                        'size': size
                    })
                    
                    deletes.append(source)
                
                elif other_version and preferred_version:
                    # File in both - compare sizes
                    try:
                        obj_other = s3.head_object(Bucket=bucket, Key=other_version['key'])
                        obj_preferred = s3.head_object(Bucket=bucket, Key=preferred_version['key'])
                        
                        size_other = obj_other['ContentLength']
                        size_preferred = obj_preferred['ContentLength']
                        
                        if size_other < size_preferred:
                            # Other is smaller - move it (replace preferred)
                            moves.append({
                                'artist': artist,
                                'preferred_book': preferred,
                                'other_book': other,
                                'filename': filename,
                                'source_path': other_version['key'],
                                'target_path': preferred_version['key'],
                                'reason': 'smaller_in_other',
                                'size_other': size_other,
                                'size_preferred': size_preferred,
                                'size_diff': size_preferred - size_other
                            })
                            
                            deletes.append(other_version['key'])
                        else:
                            # Preferred is smaller or same - just delete other
                            deletes.append(other_version['key'])
                    except Exception as e:
                        print(f"⚠️  Error comparing {filename}: {e}")
    
    print(f"🔄 Files to move: {len(moves)}")
    print(f"🗑️  Files to delete: {len(deletes)}\n")
    
    # Write CSV
    csv_file = 's3_consolidate_plan.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['artist', 'preferred_book', 'other_book', 'filename', 
                     'source_path', 'target_path', 'reason', 'size', 
                     'size_other', 'size_preferred', 'size_diff']
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(moves)
    
    print(f"📄 Plan written to: {csv_file}")
    
    # Summary by artist
    print(f"\n📊 Summary by Artist:")
    print(f"{'Artist':<30} {'Files to Move':<15} {'Preferred Book'}")
    print("-" * 100)
    
    artist_summary = defaultdict(lambda: {'count': 0, 'book': ''})
    for move in moves:
        artist_summary[move['artist']]['count'] += 1
        artist_summary[move['artist']]['book'] = move['preferred_book']
    
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
            print(f"   Reason: {move['reason']}")
            if 'size_diff' in move:
                print(f"   Size diff: {move['size_diff']} bytes (other is smaller)")
    
    print(f"\n✅ Test run complete. Review {csv_file}")

if __name__ == '__main__':
    main()
