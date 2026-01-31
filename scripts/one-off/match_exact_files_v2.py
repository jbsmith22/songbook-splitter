"""
Match S3 folders to local folders based on EXACT file list matching.
Match on song titles (the part after "Artist - " in the filename).
Files were renamed locally to use book-level artist, so we need to extract song titles.
"""
import boto3
import os
import csv
from collections import defaultdict
from pathlib import Path

def extract_song_title(filename):
    """
    Extract song title from filename.
    Format: "Artist - Song Title.pdf" -> "song title"
    Returns lowercase song title for matching.
    """
    # Remove .pdf extension
    if filename.lower().endswith('.pdf'):
        filename = filename[:-4]
    
    # Split on " - " to get song title
    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        song_title = parts[1]
    else:
        # No artist prefix, use whole filename
        song_title = filename
    
    return song_title.lower().strip()

def get_local_structure():
    """Get all local processed songs organized by artist/book."""
    local_structure = {}
    
    processed_songs_path = Path('ProcessedSongs')
    
    if not processed_songs_path.exists():
        print(f"ERROR: ProcessedSongs folder not found")
        return local_structure
    
    print(f"Scanning local files...")
    
    for artist_folder in processed_songs_path.iterdir():
        if not artist_folder.is_dir():
            continue
        
        artist = artist_folder.name
        
        for book_folder in artist_folder.iterdir():
            if not book_folder.is_dir():
                continue
            
            book = book_folder.name
            
            # Get all PDF files - extract song titles for matching
            pdf_files = []
            song_titles = []
            for pdf_file in book_folder.glob('*.pdf'):
                pdf_files.append(pdf_file.name)
                song_title = extract_song_title(pdf_file.name)
                song_titles.append(song_title)
            
            if pdf_files:
                # Sort for consistent comparison
                pdf_files.sort()
                song_titles.sort()
                
                # Create a set of song titles for matching
                song_titles_set = set(song_titles)
                
                key = f"{artist}|||{book}"
                local_structure[key] = {
                    'artist': artist,
                    'book': book,
                    'files': pdf_files,  # Original filenames
                    'song_titles': song_titles_set,  # Song titles for matching
                    'count': len(pdf_files)
                }
    
    return local_structure

def get_s3_structure():
    """Get all S3 songs organized by artist/book."""
    s3 = boto3.client('s3', region_name='us-east-1')
    s3_structure = {}
    
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
            
            # Extract song title for matching
            song_title = extract_song_title(song_name)
            
            folder_key = f"{artist}|||{book}"
            if folder_key not in s3_structure:
                s3_structure[folder_key] = {
                    'artist': artist,
                    'book': book,
                    'files': [],
                    'song_titles': [],
                    'count': 0
                }
            
            s3_structure[folder_key]['files'].append(song_name)
            s3_structure[folder_key]['song_titles'].append(song_title)
            s3_structure[folder_key]['count'] += 1
    
    # Sort files and create song title sets for matching
    for folder in s3_structure.values():
        folder['files'].sort()
        folder['song_titles'].sort()
        folder['song_titles_set'] = set(folder['song_titles'])
    
    return s3_structure

def find_exact_file_match(local_folder, s3_structure, used_s3_folders):
    """Find S3 folder with exact same song titles."""
    local_song_titles = local_folder['song_titles']
    local_count = local_folder['count']
    
    candidates = []
    
    for s3_key, s3_folder in s3_structure.items():
        # Skip if already matched
        if s3_key in used_s3_folders:
            continue
        
        s3_song_titles = s3_folder['song_titles_set']
        s3_count = s3_folder['count']
        
        # Calculate exact match metrics based on song titles
        common_songs = local_song_titles & s3_song_titles
        local_only = local_song_titles - s3_song_titles
        s3_only = s3_song_titles - local_song_titles
        
        # Only consider if counts are close
        if local_count > 0:
            count_diff_pct = abs(s3_count - local_count) / local_count
        else:
            count_diff_pct = 1.0
        
        # Calculate match percentage
        if local_count > 0:
            match_pct = len(common_songs) / local_count
        else:
            match_pct = 0
        
        # Only consider good candidates (at least 80% match OR exact count with 5+ files)
        if match_pct >= 0.80 or (s3_count == local_count and local_count >= 5):
            candidates.append({
                's3_key': s3_key,
                's3_artist': s3_folder['artist'],
                's3_book': s3_folder['book'],
                's3_count': s3_count,
                'common_songs': len(common_songs),
                'local_only': len(local_only),
                's3_only': len(s3_only),
                'match_pct': match_pct,
                'count_diff_pct': count_diff_pct
            })
    
    if not candidates:
        return None
    
    # Sort by best match
    # Priority: 1) Exact song list match, 2) Exact count, 3) Highest match %
    candidates.sort(key=lambda x: (
        -(x['local_only'] == 0 and x['s3_only'] == 0),  # Perfect match first
        abs(x['s3_count'] - local_count),  # Then exact count
        -x['match_pct'],  # Then highest match %
        x['local_only'] + x['s3_only']  # Then fewest differences
    ))
    
    return candidates[0]

def main():
    print("Exact File List Matching v2")
    print("Matching on song titles (extracted from filenames)")
    print("="*80)
    
    # Get structures
    local_structure = get_local_structure()
    s3_structure = get_s3_structure()
    
    print(f"\nLocal: {len(local_structure)} book folders")
    print(f"S3: {len(s3_structure)} book folders")
    
    # Match each local folder to S3 (enforcing 1:1)
    matches = []
    used_s3_folders = set()
    
    print("\n" + "="*80)
    print("MATCHING (showing first 100)")
    print("="*80)
    
    count = 0
    for local_key in sorted(local_structure.keys()):
        local_folder = local_structure[local_key]
        
        match = find_exact_file_match(local_folder, s3_structure, used_s3_folders)
        
        if match:
            # Mark S3 folder as used
            used_s3_folders.add(match['s3_key'])
            
            # Determine quality based on exact criteria
            if match['local_only'] == 0 and match['s3_only'] == 0:
                quality = 'PERFECT'
            elif match['match_pct'] >= 0.95 and match['count_diff_pct'] <= 0.05:
                quality = 'EXCELLENT'
            elif match['match_pct'] >= 0.90 and match['count_diff_pct'] <= 0.10:
                quality = 'GOOD'
            elif match['match_pct'] >= 0.80:
                quality = 'PARTIAL'
            else:
                quality = 'POOR'
            
            matches.append({
                'local_artist': local_folder['artist'],
                'local_book': local_folder['book'],
                'local_count': local_folder['count'],
                's3_artist': match['s3_artist'],
                's3_book': match['s3_book'],
                's3_count': match['s3_count'],
                'common_songs': match['common_songs'],
                'local_only': match['local_only'],
                's3_only': match['s3_only'],
                'match_pct': f"{match['match_pct']:.3f}",
                'count_diff_pct': f"{match['count_diff_pct']:.3f}",
                'quality': quality
            })
            
            if count < 100:
                if quality == 'PERFECT':
                    status = 'OK'
                elif quality in ['EXCELLENT', 'GOOD']:
                    status = '~~'
                else:
                    status = '??'
                
                print(f"{status} {local_folder['artist']}/{local_folder['book']} ({local_folder['count']}) -> {match['s3_book']} ({match['s3_count']}) [{quality}]")
                count += 1
        else:
            matches.append({
                'local_artist': local_folder['artist'],
                'local_book': local_folder['book'],
                'local_count': local_folder['count'],
                's3_artist': '',
                's3_book': '',
                's3_count': 0,
                'common_songs': 0,
                'local_only': local_folder['count'],
                's3_only': 0,
                'match_pct': '0.000',
                'count_diff_pct': '1.000',
                'quality': 'NO_MATCH'
            })
            
            if count < 100:
                print(f"XX {local_folder['artist']}/{local_folder['book']} ({local_folder['count']}) -> NO MATCH")
                count += 1
    
    if count >= 100:
        print(f"... and {len(matches) - 100} more")
    
    # Save results
    with open('s3_local_exact_matches_v2.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_count',
            's3_artist', 's3_book', 's3_count',
            'common_songs', 'local_only', 's3_only',
            'match_pct', 'count_diff_pct', 'quality'
        ])
        writer.writeheader()
        writer.writerows(matches)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    quality_counts = defaultdict(int)
    for match in matches:
        quality_counts[match['quality']] += 1
    
    print(f"\nTotal local books: {len(matches)}")
    print(f"  PERFECT:    {quality_counts['PERFECT']:4} (exact file list match)")
    print(f"  EXCELLENT:  {quality_counts['EXCELLENT']:4} (95%+ match, counts within 5%)")
    print(f"  GOOD:       {quality_counts['GOOD']:4} (90%+ match, counts within 10%)")
    print(f"  PARTIAL:    {quality_counts['PARTIAL']:4} (80%+ match)")
    print(f"  POOR:       {quality_counts['POOR']:4} (<80% match)")
    print(f"  NO_MATCH:   {quality_counts['NO_MATCH']:4} (no S3 folder found)")
    
    matched = len(matches) - quality_counts['NO_MATCH']
    print(f"\nMatched: {matched}/{len(matches)} ({matched/len(matches)*100:.1f}%)")
    print(f"S3 folders used: {len(used_s3_folders)}/{len(s3_structure)}")
    print(f"S3 folders unused: {len(s3_structure) - len(used_s3_folders)} (duplicates/old versions)")
    
    print("\n" + "="*80)
    print("Results saved to: s3_local_exact_matches_v2.csv")
    print("="*80)

if __name__ == '__main__':
    main()
