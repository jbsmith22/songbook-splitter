"""
Match S3 folders to local folders by comparing file contents.
The local copy is the source of truth - find which S3 folder matches each local folder.
"""
import boto3
import os
import csv
from collections import defaultdict
from pathlib import Path

def get_local_structure():
    """Get all local processed songs organized by artist/book."""
    local_structure = defaultdict(lambda: defaultdict(list))
    
    processed_songs_path = Path('ProcessedSongs')
    
    if not processed_songs_path.exists():
        print(f"ERROR: ProcessedSongs folder not found at {processed_songs_path.absolute()}")
        return local_structure
    
    print(f"Scanning local files in: {processed_songs_path.absolute()}")
    
    for artist_folder in processed_songs_path.iterdir():
        if not artist_folder.is_dir():
            continue
        
        artist = artist_folder.name
        
        for book_folder in artist_folder.iterdir():
            if not book_folder.is_dir():
                continue
            
            book = book_folder.name
            
            # Get all PDF files in this book folder
            pdf_files = []
            for pdf_file in book_folder.glob('*.pdf'):
                pdf_files.append({
                    'name': pdf_file.name,
                    'size': pdf_file.stat().st_size
                })
            
            if pdf_files:
                local_structure[artist][book] = pdf_files
    
    return local_structure

def get_s3_structure():
    """Get all S3 songs organized by artist/book."""
    s3 = boto3.client('s3', region_name='us-east-1')
    s3_structure = defaultdict(lambda: defaultdict(list))
    
    print("Fetching S3 objects...")
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket='jsmith-output'):
        if 'Contents' not in page:
            continue
        
        for obj in page['Contents']:
            key = obj['Key']
            
            # Skip non-PDF files
            if not key.endswith('.pdf'):
                continue
            
            # Skip artifacts
            if key.startswith('artifacts/'):
                continue
            
            # Skip broken paths
            if key.startswith('s3:/'):
                continue
            
            # Parse the path
            parts = key.split('/')
            if len(parts) < 3:
                continue
            
            artist = parts[0]
            book = parts[1]
            
            # Handle paths with extra "Songs" subfolder
            if len(parts) == 4 and parts[2].lower() == 'songs':
                song_name = parts[3]
            else:
                song_name = parts[-1]
            
            s3_structure[artist][book].append({
                'name': song_name,
                'size': obj['Size'],
                'key': key
            })
    
    return s3_structure

def normalize_filename(filename):
    """Normalize filename for comparison."""
    # Remove common variations
    name = filename.lower()
    name = name.replace('_', ' ')
    name = name.replace('  ', ' ')
    name = name.strip()
    return name

def compare_file_lists(local_files, s3_files):
    """Compare two file lists and return match score."""
    # Create normalized sets
    local_names = {normalize_filename(f['name']) for f in local_files}
    s3_names = {normalize_filename(f['name']) for f in s3_files}
    
    # Count matches
    matches = len(local_names & s3_names)
    local_only = len(local_names - s3_names)
    s3_only = len(s3_names - local_names)
    
    # Calculate match percentage
    if len(local_names) == 0:
        return 0.0, matches, local_only, s3_only
    
    match_pct = matches / len(local_names)
    
    return match_pct, matches, local_only, s3_only

def find_best_s3_match(local_artist, local_book, local_files, s3_structure):
    """Find the best matching S3 folder for a local book."""
    best_match = None
    best_score = 0.0
    all_candidates = []
    
    # Look for matching artist in S3
    s3_artist_variations = [
        local_artist,
        local_artist.lower(),
        local_artist.title(),
        local_artist.replace(' ', ''),
    ]
    
    for s3_artist in s3_structure.keys():
        # Check if S3 artist matches local artist
        if s3_artist not in s3_artist_variations and \
           s3_artist.lower() not in [v.lower() for v in s3_artist_variations]:
            continue
        
        # Check all books under this artist
        for s3_book, s3_files in s3_structure[s3_artist].items():
            # Compare file lists
            match_pct, matches, local_only, s3_only = compare_file_lists(local_files, s3_files)
            
            candidate = {
                's3_artist': s3_artist,
                's3_book': s3_book,
                'match_pct': match_pct,
                'matches': matches,
                'local_only': local_only,
                's3_only': s3_only,
                'local_count': len(local_files),
                's3_count': len(s3_files)
            }
            
            all_candidates.append(candidate)
            
            if match_pct > best_score:
                best_score = match_pct
                best_match = candidate
    
    return best_match, all_candidates

def main():
    print("Matching S3 Folders to Local Folders")
    print("="*80)
    
    # Get local structure
    local_structure = get_local_structure()
    
    if not local_structure:
        print("ERROR: No local files found!")
        return
    
    local_artist_count = len(local_structure)
    local_book_count = sum(len(books) for books in local_structure.values())
    local_song_count = sum(len(songs) for books in local_structure.values() for songs in books.values())
    
    print(f"\nLocal structure:")
    print(f"  Artists: {local_artist_count}")
    print(f"  Books:   {local_book_count}")
    print(f"  Songs:   {local_song_count}")
    
    # Get S3 structure
    s3_structure = get_s3_structure()
    
    s3_artist_count = len(s3_structure)
    s3_book_count = sum(len(books) for books in s3_structure.values())
    s3_song_count = sum(len(songs) for books in s3_structure.values() for songs in books.values())
    
    print(f"\nS3 structure:")
    print(f"  Artists: {s3_artist_count}")
    print(f"  Books:   {s3_book_count}")
    print(f"  Songs:   {s3_song_count}")
    
    # Match each local book to S3
    print("\n" + "="*80)
    print("MATCHING LOCAL TO S3")
    print("="*80)
    
    matches = []
    
    for local_artist, books in sorted(local_structure.items()):
        for local_book, local_files in sorted(books.items()):
            print(f"\nMatching: {local_artist}/{local_book} ({len(local_files)} songs)")
            
            best_match, all_candidates = find_best_s3_match(
                local_artist, local_book, local_files, s3_structure
            )
            
            if best_match:
                match_quality = "PERFECT" if best_match['match_pct'] == 1.0 else \
                               "EXCELLENT" if best_match['match_pct'] >= 0.95 else \
                               "GOOD" if best_match['match_pct'] >= 0.80 else \
                               "PARTIAL" if best_match['match_pct'] >= 0.50 else \
                               "POOR"
                
                print(f"  ✓ Best match: {best_match['s3_artist']}/{best_match['s3_book']}")
                print(f"    Quality: {match_quality} ({best_match['match_pct']*100:.1f}%)")
                print(f"    Matches: {best_match['matches']}/{best_match['local_count']}")
                
                if best_match['local_only'] > 0:
                    print(f"    Local only: {best_match['local_only']} files")
                if best_match['s3_only'] > 0:
                    print(f"    S3 only: {best_match['s3_only']} files")
                
                # Show other candidates if there are multiple good matches
                other_good = [c for c in all_candidates if c != best_match and c['match_pct'] >= 0.80]
                if other_good:
                    print(f"    Other candidates: {len(other_good)}")
                    for candidate in other_good[:3]:
                        print(f"      - {candidate['s3_artist']}/{candidate['s3_book']} ({candidate['match_pct']*100:.1f}%)")
                
                matches.append({
                    'local_artist': local_artist,
                    'local_book': local_book,
                    'local_song_count': len(local_files),
                    's3_artist': best_match['s3_artist'],
                    's3_book': best_match['s3_book'],
                    's3_song_count': best_match['s3_count'],
                    'match_pct': best_match['match_pct'],
                    'match_quality': match_quality,
                    'matches': best_match['matches'],
                    'local_only': best_match['local_only'],
                    's3_only': best_match['s3_only'],
                    'other_candidates': len([c for c in all_candidates if c != best_match and c['match_pct'] >= 0.50])
                })
            else:
                print(f"  ✗ No match found in S3")
                matches.append({
                    'local_artist': local_artist,
                    'local_book': local_book,
                    'local_song_count': len(local_files),
                    's3_artist': '',
                    's3_book': '',
                    's3_song_count': 0,
                    'match_pct': 0.0,
                    'match_quality': 'NO MATCH',
                    'matches': 0,
                    'local_only': len(local_files),
                    's3_only': 0,
                    'other_candidates': 0
                })
    
    # Save results
    with open('s3_local_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_song_count',
            's3_artist', 's3_book', 's3_song_count',
            'match_pct', 'match_quality', 'matches', 'local_only', 's3_only',
            'other_candidates'
        ])
        writer.writeheader()
        writer.writerows(matches)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    perfect = len([m for m in matches if m['match_quality'] == 'PERFECT'])
    excellent = len([m for m in matches if m['match_quality'] == 'EXCELLENT'])
    good = len([m for m in matches if m['match_quality'] == 'GOOD'])
    partial = len([m for m in matches if m['match_quality'] == 'PARTIAL'])
    poor = len([m for m in matches if m['match_quality'] == 'POOR'])
    no_match = len([m for m in matches if m['match_quality'] == 'NO MATCH'])
    
    print(f"Total local books: {len(matches)}")
    print(f"  PERFECT (100%):     {perfect}")
    print(f"  EXCELLENT (95%+):   {excellent}")
    print(f"  GOOD (80-95%):      {good}")
    print(f"  PARTIAL (50-80%):   {partial}")
    print(f"  POOR (<50%):        {poor}")
    print(f"  NO MATCH:           {no_match}")
    
    print("\n" + "="*80)
    print("Results saved to: s3_local_matches.csv")
    print("="*80)

if __name__ == '__main__':
    main()
