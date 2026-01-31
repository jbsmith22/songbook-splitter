"""
Download missing files from S3 for PARTIAL matches.
This will make local folders complete so they match S3.
"""
import pandas as pd
import boto3
from pathlib import Path

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
        return set(), path
    
    songs = {}
    for pdf in path.glob('*.pdf'):
        title = extract_song_title(pdf.name)
        songs[title] = pdf.name
    
    return songs, path

def get_s3_songs(artist, book):
    """Get song files from S3 folder."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    prefix = f"{artist}/{book}/"
    songs = {}
    
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
                songs[title] = key
    except Exception as e:
        print(f"  ERROR fetching S3: {e}")
        return None
    
    return songs

def download_file(s3_key, local_path, artist_name):
    """Download a file from S3 and rename it with the book-level artist."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    # Get the original filename
    original_filename = s3_key.split('/')[-1]
    
    # Extract song title
    song_title = extract_song_title(original_filename)
    
    # Create new filename with book-level artist
    new_filename = f"{artist_name} - {song_title}.pdf"
    
    # Download
    local_file = local_path / new_filename
    
    try:
        s3.download_file('jsmith-output', s3_key, str(local_file))
        return new_filename
    except Exception as e:
        print(f"    ERROR downloading {s3_key}: {e}")
        return None

def main():
    df = pd.read_csv('s3_matches_partial.csv')
    
    print(f"PARTIAL MATCHES: {len(df)} books")
    print("="*80)
    print("Downloading missing files from S3...\n")
    
    total_downloaded = 0
    
    for idx, row in df.iterrows():
        local_artist = row['local_artist']
        local_book = row['local_book']
        s3_artist = row['s3_artist']
        s3_book = row['s3_book']
        
        print(f"{local_artist} / {local_book}")
        print(f"  S3: {s3_artist} / {s3_book}")
        
        # Get local and S3 songs
        local_songs, local_path = get_local_songs(local_artist, local_book)
        s3_songs = get_s3_songs(s3_artist, s3_book)
        
        if s3_songs is None:
            print("  ❌ Could not fetch S3 songs")
            continue
        
        # Find missing songs
        local_titles = set(local_songs.keys())
        s3_titles = set(s3_songs.keys())
        
        missing = s3_titles - local_titles
        
        if not missing:
            print(f"  ✓ No missing files (local has all S3 songs)")
            continue
        
        print(f"  📥 Downloading {len(missing)} missing files...")
        
        # Ensure local directory exists
        local_path.mkdir(parents=True, exist_ok=True)
        
        downloaded = 0
        for song_title in sorted(missing):
            s3_key = s3_songs[song_title]
            filename = download_file(s3_key, local_path, local_artist)
            if filename:
                print(f"    ✓ {filename}")
                downloaded += 1
            else:
                print(f"    ❌ Failed: {song_title}")
        
        print(f"  ✓ Downloaded {downloaded}/{len(missing)} files")
        total_downloaded += downloaded
        print()
    
    print("="*80)
    print(f"COMPLETE: Downloaded {total_downloaded} files total")
    print("="*80)

if __name__ == '__main__':
    main()
