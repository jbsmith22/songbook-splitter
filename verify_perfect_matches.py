"""
Verify that PERFECT matches are actually perfect by checking a sample.
"""
import pandas as pd
import random
from pathlib import Path
import boto3

def extract_song_title(filename):
    """Extract song title from filename."""
    if filename.lower().endswith('.pdf'):
        filename = filename[:-4]
    
    if ' - ' in filename:
        parts = filename.split(' - ', 1)
        song_title = parts[1]
    else:
        song_title = filename
    
    return song_title.lower().strip()

def get_local_songs(artist, book):
    """Get song titles from local folder."""
    path = Path('ProcessedSongs') / artist / book
    if not path.exists():
        return None
    
    songs = []
    for pdf in path.glob('*.pdf'):
        title = extract_song_title(pdf.name)
        songs.append(title)
    
    return sorted(songs)

def get_s3_songs(artist, book):
    """Get song titles from S3 folder."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    prefix = f"{artist}/{book}/"
    songs = []
    
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket='jsmith-output', Prefix=prefix):
            if 'Contents' not in page:
                continue
            
            for obj in page['Contents']:
                key = obj['Key']
                if not key.endswith('.pdf'):
                    continue
                
                # Get filename
                parts = key.split('/')
                if len(parts) == 4 and parts[2].lower() == 'songs':
                    filename = parts[3]
                else:
                    filename = parts[-1]
                
                title = extract_song_title(filename)
                songs.append(title)
    except Exception as e:
        print(f"  ERROR: {e}")
        return None
    
    return sorted(songs)

def main():
    df = pd.read_csv('s3_local_exact_matches_v2.csv')
    perfect = df[df['quality'] == 'PERFECT']
    
    print(f"Total PERFECT matches: {len(perfect)}")
    print("\nVerifying 10 random samples...")
    print("="*80)
    
    # Sample 10 random
    sample = perfect.sample(min(10, len(perfect)))
    
    verified = 0
    failed = 0
    
    for idx, row in sample.iterrows():
        print(f"\n{row['local_artist']} / {row['local_book']}")
        print(f"  Matched to: {row['s3_artist']} / {row['s3_book']}")
        print(f"  Counts: Local={row['local_count']}, S3={row['s3_count']}")
        
        # Get actual song lists
        local_songs = get_local_songs(row['local_artist'], row['local_book'])
        s3_songs = get_s3_songs(row['s3_artist'], row['s3_book'])
        
        if local_songs is None or s3_songs is None:
            print("  ❌ ERROR: Could not fetch songs")
            failed += 1
            continue
        
        local_set = set(local_songs)
        s3_set = set(s3_songs)
        
        common = local_set & s3_set
        local_only = local_set - s3_set
        s3_only = s3_set - local_set
        
        if len(local_only) == 0 and len(s3_only) == 0:
            print(f"  ✓ VERIFIED: {len(common)} songs match perfectly")
            verified += 1
        else:
            print(f"  ❌ NOT PERFECT: {len(common)} common, {len(local_only)} local only, {len(s3_only)} S3 only")
            if local_only:
                print(f"     Local only: {list(local_only)[:3]}")
            if s3_only:
                print(f"     S3 only: {list(s3_only)[:3]}")
            failed += 1
    
    print("\n" + "="*80)
    print(f"VERIFICATION RESULTS: {verified} verified, {failed} failed")
    print("="*80)

if __name__ == '__main__':
    main()
