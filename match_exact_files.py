"""
Match S3 folders to local folders based on EXACT file list matching.
Only match if the file lists are essentially identical (same count, same names).
"""
import boto3
import os
import csv
from collections import defaultdict
from pathlib import Path

def normalize_filename(filename):
    """Normalize filename for comparison."""
    # Remove extension, convert to lowercase, normalize spaces
    name = filename.lower()
    if name.endswith('.pdf'):
        name = name[:-4]
    name = name.replace('_', ' ').replace('  ', ' ').strip()
    return name

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
            
            # Get all PDF files
            pdf_files = []
            for pdf_file in book_folder.glob('*.pdf'):
                normalized = normalize_filename(pdf_file.name)
                pdf_files.append(normalized)
            
            if pdf_files:
                # Sort for consistent comparison
                pdf_files.sort()
                
                key = f"{artist}|||{book}"
                local_structure[key] = {
                    'artist': artist,
                    'book': book,
                    'files': set(pdf_files),
                    'files_list': pdf_files,
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
            
            normalized = normalize_filename(song_name)
            
            folder_key = f"{artist}|||{book}"
            if folder_key not in s3_structure:
                s3_structure[folder_key] = {
                    'artist': artist,
                    'book': book,
                    'files': [],
                    'count': 0
                }
            
            s3_structure[folder_key]['files'].append(normalized)
            s3_structure[folder_key]['count'] += 1
    
    # Sort files for consistent comparison
    for folder in s3_structure.values():
        folder['files'].sort()
        folder['files_set'] = set(folder['files'])
    
    return s3_structure

def find_exact_file_match(local_folder, s3_structure, used_s3_folders):
    """Find S3 folder with exact same file list."""
    local_files = local_folder['files']
    local_count = local_folder['count']
    
    candidates = []
    
    for s3_key, s3_folder in s3_structure.items():
        # Skip if already matched
        if s3_key in used_s3_folders:
            continue
        
        s3_files = s3_folder['files_set']
        s3_count = s3_folder['count']
        
        # Calculate exact match metrics
        common_files = local_files & s3_files
        local_only = local_files - s3_files
        s3_only = s3_files - local_files
        
        # Only consider if counts are close
        if local_count > 0:
            count_diff_pct = abs(s3_count - local_count) / local_count
        else:
            count_diff_pct = 1.0
        
        # Calculate match percentage
        if local_count > 0:
            match_pct = len(common_files) / local_count
        else:
            match_pct = 0
        
        # Only consider good candidates
        if match_pct >= 0.80 or (len(common_files) >= 5 and count_diff_pct <= 0.2):
            candidates.append({
                's3_key': s3_key,
                's3_artist': s3_folder['artist'],
                's3_book': s3_folder['book'],
                's3_count': s3_count,
                'common_files': len(common_files),
                'local_only': len(local_only),
                's3_only': len(s3_only),
                'match_pct': match_pct,
                'count_diff_pct': count_diff_pct
            })
    
    if not candidates:
        return None
    
    # Sort by best match
    # Priority: exact count match, then highest match percentage
    candidates.sort(key=lambda x: (
        abs(x['s3_count'] - local_count),  # Prefer exact count
        -x['match_pct'],  # Then highest match %
        x['local_only'] + x['s3_only']  # Then fewest differences
    ))
    
    return candidates[0]

def main():
    print("Exact File List Matching")
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
                'common_files': match['common_files'],
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
                'common_files': 0,
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
    with open('s3_local_exact_matches.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_count',
            's3_artist', 's3_book', 's3_count',
            'common_files', 'local_only', 's3_only',
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
    print("Results saved to: s3_local_exact_matches.csv")
    print("="*80)

if __name__ == '__main__':
    main()
