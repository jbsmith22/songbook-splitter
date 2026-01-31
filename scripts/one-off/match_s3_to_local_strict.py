"""
Strict matching: S3 folders to local folders based on exact file list matching.
Enforces 1:1 relationship and requires very close song counts.
"""
import boto3
import os
import csv
from collections import defaultdict
from pathlib import Path

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
            
            # Get all PDF files in this book folder
            pdf_files = set()
            for pdf_file in book_folder.glob('*.pdf'):
                # Normalize filename for comparison
                normalized = pdf_file.name.lower().replace('_', ' ').replace('  ', ' ').strip()
                pdf_files.add(normalized)
            
            if pdf_files:
                key = f"{artist}|||{book}"
                local_structure[key] = {
                    'artist': artist,
                    'book': book,
                    'files': pdf_files,
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
            
            # Normalize filename for comparison
            normalized = song_name.lower().replace('_', ' ').replace('  ', ' ').strip()
            
            folder_key = f"{artist}|||{book}"
            if folder_key not in s3_structure:
                s3_structure[folder_key] = {
                    'artist': artist,
                    'book': book,
                    'files': set(),
                    'count': 0
                }
            
            s3_structure[folder_key]['files'].add(normalized)
            s3_structure[folder_key]['count'] += 1
    
    return s3_structure

def find_exact_match(local_folder, s3_structure, used_s3_folders):
    """Find exact matching S3 folder for a local folder."""
    local_files = local_folder['files']
    local_count = local_folder['count']
    
    best_match = None
    best_score = 0
    
    for s3_key, s3_folder in s3_structure.items():
        # Skip if already matched
        if s3_key in used_s3_folders:
            continue
        
        s3_files = s3_folder['files']
        s3_count = s3_folder['count']
        
        # Calculate match metrics
        common_files = local_files & s3_files
        local_only = local_files - s3_files
        s3_only = s3_files - local_files
        
        # Calculate match percentage (bidirectional)
        if local_count > 0 and s3_count > 0:
            local_match_pct = len(common_files) / local_count
            s3_match_pct = len(common_files) / s3_count
            
            # Both must be high for a good match
            match_score = min(local_match_pct, s3_match_pct)
        else:
            match_score = 0
        
        # Calculate count similarity
        if local_count > 0:
            count_diff = abs(s3_count - local_count) / local_count
        else:
            count_diff = 1.0
        
        # Combined score (heavily weight exact matches)
        if len(local_only) == 0 and len(s3_only) == 0:
            # Perfect match - all files match exactly
            score = 1.0
        elif match_score >= 0.95 and count_diff <= 0.1:
            # Near perfect - 95%+ match and counts within 10%
            score = 0.95
        elif match_score >= 0.90 and count_diff <= 0.2:
            # Excellent - 90%+ match and counts within 20%
            score = 0.90
        elif match_score >= 0.80:
            # Good - 80%+ match
            score = 0.80
        else:
            # Not good enough
            score = match_score
        
        if score > best_score:
            best_score = score
            best_match = {
                's3_key': s3_key,
                's3_artist': s3_folder['artist'],
                's3_book': s3_folder['book'],
                's3_count': s3_count,
                'common_files': len(common_files),
                'local_only': len(local_only),
                's3_only': len(s3_only),
                'match_score': match_score,
                'count_diff': count_diff,
                'final_score': score
            }
    
    return best_match

def main():
    print("Strict S3-to-Local Matching")
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
    print("MATCHING")
    print("="*80)
    
    for local_key in sorted(local_structure.keys()):
        local_folder = local_structure[local_key]
        
        match = find_exact_match(local_folder, s3_structure, used_s3_folders)
        
        if match:
            # Mark S3 folder as used
            used_s3_folders.add(match['s3_key'])
            
            # Determine quality
            if match['final_score'] >= 1.0:
                quality = 'PERFECT'
            elif match['final_score'] >= 0.95:
                quality = 'NEAR_PERFECT'
            elif match['final_score'] >= 0.90:
                quality = 'EXCELLENT'
            elif match['final_score'] >= 0.80:
                quality = 'GOOD'
            elif match['final_score'] >= 0.50:
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
                'match_score': f"{match['match_score']:.3f}",
                'count_diff': f"{match['count_diff']:.3f}",
                'quality': quality
            })
            
            if quality in ['PERFECT', 'NEAR_PERFECT']:
                status = 'OK'
            elif quality in ['EXCELLENT', 'GOOD']:
                status = '~~'
            else:
                status = '??'
            
            print(f"{status} {local_folder['artist']}/{local_folder['book']} ({local_folder['count']}) -> {match['s3_book']} ({match['s3_count']}) [{quality}]")
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
                'match_score': '0.000',
                'count_diff': '1.000',
                'quality': 'NO_MATCH'
            })
            
            print(f"XX {local_folder['artist']}/{local_folder['book']} ({local_folder['count']}) -> NO MATCH")
    
    # Save results
    with open('s3_local_matches_strict.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'local_artist', 'local_book', 'local_count',
            's3_artist', 's3_book', 's3_count',
            'common_files', 'local_only', 's3_only',
            'match_score', 'count_diff', 'quality'
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
    print(f"  PERFECT:      {quality_counts['PERFECT']:4} (100% match, exact counts)")
    print(f"  NEAR_PERFECT: {quality_counts['NEAR_PERFECT']:4} (95%+ match, counts within 10%)")
    print(f"  EXCELLENT:    {quality_counts['EXCELLENT']:4} (90%+ match, counts within 20%)")
    print(f"  GOOD:         {quality_counts['GOOD']:4} (80%+ match)")
    print(f"  PARTIAL:      {quality_counts['PARTIAL']:4} (50-80% match)")
    print(f"  POOR:         {quality_counts['POOR']:4} (<50% match)")
    print(f"  NO_MATCH:     {quality_counts['NO_MATCH']:4} (no S3 folder found)")
    
    print(f"\nS3 folders used: {len(used_s3_folders)}")
    print(f"S3 folders unused: {len(s3_structure) - len(used_s3_folders)}")
    
    print("\n" + "="*80)
    print("Results saved to: s3_local_matches_strict.csv")
    print("="*80)

if __name__ == '__main__':
    main()
