"""
Match POOR and NO_MATCH books by folder name similarity.
Uses string similarity to find the best S3 folder match for each local folder.
"""
import pandas as pd
import boto3
from difflib import SequenceMatcher
from pathlib import Path

def get_similarity(str1, str2):
    """Calculate similarity ratio between two strings (0.0 to 1.0)."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def get_all_s3_folders():
    """Get all unique S3 folder paths (artist/book)."""
    s3 = boto3.client('s3', region_name='us-east-1')
    folders = set()
    
    print("Fetching all S3 folders...")
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
            
            # Parse the path to get artist/book
            parts = key.split('/')
            if len(parts) >= 3:
                artist = parts[0]
                book = parts[1]
                folders.add(f"{artist}|||{book}")
    
    return folders

def find_best_folder_match(local_artist, local_book, s3_folders, used_s3_folders):
    """Find the S3 folder with the most similar name."""
    local_full = f"{local_artist}/{local_book}"
    
    best_match = None
    best_score = 0.0
    
    for s3_folder in s3_folders:
        # Skip if already used
        if s3_folder in used_s3_folders:
            continue
        
        s3_artist, s3_book = s3_folder.split('|||')
        s3_full = f"{s3_artist}/{s3_book}"
        
        # Calculate similarity
        score = get_similarity(local_full, s3_full)
        
        if score > best_score:
            best_score = score
            best_match = {
                's3_folder': s3_folder,
                's3_artist': s3_artist,
                's3_book': s3_book,
                'similarity': score
            }
    
    return best_match

def main():
    # Load POOR and NO_MATCH cases
    poor_df = pd.read_csv('s3_matches_poor.csv')
    no_match_df = pd.read_csv('s3_matches_no_match.csv')
    
    # Combine them
    to_rematch = pd.concat([poor_df, no_match_df], ignore_index=True)
    
    print(f"REMATCHING BY FOLDER NAME SIMILARITY")
    print("="*80)
    print(f"Books to rematch: {len(to_rematch)}")
    print(f"  POOR: {len(poor_df)}")
    print(f"  NO_MATCH: {len(no_match_df)}")
    print()
    
    # Get all S3 folders
    s3_folders = get_all_s3_folders()
    print(f"Total S3 folders: {len(s3_folders)}")
    print()
    
    # Load already confirmed matches to exclude them
    confirmed_df = pd.read_csv('s3_matches_confirmed.csv')
    used_s3_folders = set()
    for idx, row in confirmed_df.iterrows():
        used_s3_folders.add(f"{row['s3_artist']}|||{row['s3_book']}")
    
    print(f"Excluding {len(used_s3_folders)} already matched S3 folders")
    print()
    
    # Find best matches
    results = []
    
    print("FINDING BEST MATCHES BY NAME SIMILARITY")
    print("="*80)
    
    for idx, row in to_rematch.iterrows():
        local_artist = row['local_artist']
        local_book = row['local_book']
        local_count = row['local_count']
        
        match = find_best_folder_match(local_artist, local_book, s3_folders, used_s3_folders)
        
        if match:
            similarity_pct = match['similarity'] * 100
            
            # Classify by similarity
            if match['similarity'] >= 0.90:
                quality = 'EXCELLENT'
                marker = '✓✓'
            elif match['similarity'] >= 0.80:
                quality = 'GOOD'
                marker = '✓'
            elif match['similarity'] >= 0.70:
                quality = 'FAIR'
                marker = '~'
            else:
                quality = 'WEAK'
                marker = '?'
            
            print(f"{marker} {local_artist}/{local_book}")
            print(f"   -> {match['s3_artist']}/{match['s3_book']}")
            print(f"   Similarity: {similarity_pct:.1f}% [{quality}]")
            
            results.append({
                'local_artist': local_artist,
                'local_book': local_book,
                'local_count': local_count,
                's3_artist': match['s3_artist'],
                's3_book': match['s3_book'],
                'similarity': f"{match['similarity']:.3f}",
                'similarity_pct': f"{similarity_pct:.1f}%",
                'quality': quality,
                'original_quality': row['quality']
            })
        else:
            print(f"✗ {local_artist}/{local_book} - NO MATCH FOUND")
            results.append({
                'local_artist': local_artist,
                'local_book': local_book,
                'local_count': local_count,
                's3_artist': '',
                's3_book': '',
                'similarity': '0.000',
                'similarity_pct': '0.0%',
                'quality': 'NO_MATCH',
                'original_quality': row['quality']
            })
    
    # Save results
    results_df = pd.DataFrame(results)
    results_df.to_csv('s3_matches_by_name_similarity.csv', index=False)
    
    # Print summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    quality_counts = results_df['quality'].value_counts()
    
    print(f"\nTotal rematched: {len(results_df)}")
    for quality in ['EXCELLENT', 'GOOD', 'FAIR', 'WEAK', 'NO_MATCH']:
        count = quality_counts.get(quality, 0)
        if count > 0:
            print(f"  {quality}: {count}")
    
    print("\n" + "="*80)
    print("Results saved to: s3_matches_by_name_similarity.csv")
    print("="*80)

if __name__ == '__main__':
    main()
