import boto3
import os
from pathlib import Path

# Initialize S3 client
s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'jsmith-output'

# Mapping of local empty folders to S3 folders with files
folders_to_download = [
    {
        'local': r'ProcessedSongs\Night Ranger\Night Ranger - Seven Wishes _Jap Score_',
        's3': 'Night Ranger/Night Ranger - Seven Wishes _jap Score_/Songs'
    },
    {
        'local': r'ProcessedSongs\Robbie Robertson\Robbie Robertson - Songbook _Guitar Tab_',
        's3': 'Robbie Robertson/Robbie Robertson - Songbook [guitar Tab]/Songs'
    },
    {
        'local': r'ProcessedSongs\Various Artists\Various Artists - Ultimate 80s Songs',
        's3': "Various Artists/Various Artists - Ultimate 80's Songs/Songs"
    },
    {
        'local': r'ProcessedSongs\_broadway Shows\Various Artists - Little Shop Of Horrors Script',
        's3': '_broadway Shows/Various Artists - Little Shop Of Horrors (original)/Songs'
    },
    {
        'local': r'ProcessedSongs\Crosby Stills And Nash\Crosby Stills Nash And Young - The Guitar Collection',
        's3': 'Crosby Stills And Nash/Crosby Stills Nash & Young - Deja Vu [pvg Book]/Songs'
    },
    {
        'local': r'ProcessedSongs\Dire Straits\Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_',
        's3': 'Dire Straits/Dire Straits - Mark Knopfler Guitar Styles Vol 1 [guitar Book]/Songs'
    }
]

print("DOWNLOADING FILES FROM S3 TO EMPTY LOCAL FOLDERS")
print("=" * 80)

total_downloaded = 0

for mapping in folders_to_download:
    local_folder = mapping['local']
    s3_prefix = mapping['s3']
    
    print(f"\n{local_folder}")
    print(f"  S3: {s3_prefix}")
    
    # Create local folder if it doesn't exist
    os.makedirs(local_folder, exist_ok=True)
    
    # List all files in S3 folder
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=s3_prefix + '/')
    
    files_downloaded = 0
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            s3_key = obj['Key']
            
            # Skip if it's just the folder itself
            if s3_key.endswith('/'):
                continue
            
            # Get filename from S3 key
            filename = os.path.basename(s3_key)
            local_path = os.path.join(local_folder, filename)
            
            # Download file
            try:
                s3.download_file(bucket, s3_key, local_path)
                files_downloaded += 1
                print(f"    ✓ {filename}")
            except Exception as e:
                print(f"    ✗ Failed to download {filename}: {e}")
    
    print(f"  Downloaded: {files_downloaded} files")
    total_downloaded += files_downloaded

print("\n" + "=" * 80)
print(f"TOTAL FILES DOWNLOADED: {total_downloaded}")
