#!/usr/bin/env python3
"""
Find files that exist in S3 but not locally, accounting for Songs/ subfolder structure.
"""
import boto3
from pathlib import Path
import csv

def normalize_s3_key(key):
    """
    Normalize S3 key by removing Songs/ subfolder.
    E.g., "America/Greatest Hits/Songs/America - Song.pdf" 
       -> "America/Greatest Hits/America - Song.pdf"
    """
    return key.replace('/Songs/', '/')

def s3_to_local_path(key):
    """Convert S3 key to local Windows path."""
    normalized = normalize_s3_key(key)
    return normalized.replace('/', '\\')

def main():
    print("Finding missing files...")
    print()
    
    # Get all S3 files
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print("Listing S3 files...")
    s3_files = {}
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.pdf') and not key.startswith(('artifacts/', 'output/', 's3:/')):
                    s3_files[key] = obj['Size']
    
    print(f"Found {len(s3_files)} S3 files")
    
    # Get all local files
    local_dir = Path('ProcessedSongs_Reorganized')
    print(f"Scanning {local_dir}...")
    
    local_files = set()
    for pdf_file in local_dir.rglob('*.pdf'):
        rel_path = str(pdf_file.relative_to(local_dir))
        local_files.add(rel_path)
    
    print(f"Found {len(local_files)} local files")
    print()
    
    # Find missing files
    print("Comparing...")
    missing = []
    
    for s3_key, size in s3_files.items():
        local_path = s3_to_local_path(s3_key)
        
        if local_path not in local_files:
            missing.append({
                's3_key': s3_key,
                'expected_local_path': local_path,
                'size': size,
                'in_songs_subfolder': '/Songs/' in s3_key
            })
    
    print(f"Missing files: {len(missing)}")
    print()
    
    # Separate by location
    in_songs = [m for m in missing if m['in_songs_subfolder']]
    at_root = [m for m in missing if not m['in_songs_subfolder']]
    
    print(f"  In Songs/ subfolder: {len(in_songs)}")
    print(f"  At book root: {len(at_root)}")
    print()
    
    # Write to CSV
    if missing:
        output_file = 'files-to-download.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['s3_key', 'expected_local_path', 'size', 'in_songs_subfolder'])
            writer.writeheader()
            writer.writerows(missing)
        
        print(f"Missing files written to: {output_file}")
        print()
        
        # Show examples
        print("First 10 missing files:")
        for item in missing[:10]:
            print(f"  S3: {item['s3_key']}")
            print(f"  Local: {item['expected_local_path']}")
            print(f"  Size: {item['size']} bytes")
            print()
        
        # Count by artist
        by_artist = {}
        for item in missing:
            artist = item['s3_key'].split('/')[0]
            by_artist[artist] = by_artist.get(artist, 0) + 1
        
        print("Missing files by artist (top 10):")
        for artist, count in sorted(by_artist.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {artist}: {count}")
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  S3 total: {len(s3_files)}")
    print(f"  Local total: {len(local_files)}")
    print(f"  Missing: {len(missing)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
