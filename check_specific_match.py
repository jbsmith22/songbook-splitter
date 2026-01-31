"""Check a specific match in detail."""
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

# Check Beatles - Rubber Soul (13 local, 14 S3)
print("Beatles - Rubber Soul")
print("="*80)

# Local
local_path = Path('ProcessedSongs/Beatles/Beatles - Rubber Soul')
local_songs = []
for pdf in local_path.glob('*.pdf'):
    title = extract_song_title(pdf.name)
    local_songs.append(title)

local_songs.sort()
print(f"\nLocal ({len(local_songs)} songs):")
for song in local_songs:
    print(f"  - {song}")

# S3
s3 = boto3.client('s3', region_name='us-east-1')
prefix = "Beatles/Rubber Soul/"
s3_songs = []

paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='jsmith-output', Prefix=prefix):
    if 'Contents' not in page:
        continue
    
    for obj in page['Contents']:
        key = obj['Key']
        if not key.endswith('.pdf'):
            continue
        
        parts = key.split('/')
        if len(parts) == 4 and parts[2].lower() == 'songs':
            filename = parts[3]
        else:
            filename = parts[-1]
        
        title = extract_song_title(filename)
        s3_songs.append(title)

s3_songs.sort()
print(f"\nS3 ({len(s3_songs)} songs):")
for song in s3_songs:
    print(f"  - {song}")

# Compare
local_set = set(local_songs)
s3_set = set(s3_songs)

print(f"\nComparison:")
print(f"  Common: {len(local_set & s3_set)}")
print(f"  Local only: {len(local_set - s3_set)}")
print(f"  S3 only: {len(s3_set - local_set)}")

if s3_set - local_set:
    print(f"\nS3 has these extra songs:")
    for song in sorted(s3_set - local_set):
        print(f"  + {song}")

if local_set - s3_set:
    print(f"\nLocal has these extra songs:")
    for song in sorted(local_set - s3_set):
        print(f"  + {song}")
