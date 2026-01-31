#!/usr/bin/env python3
"""
Download missing files from S3, handling Songs/ subfolder and creating proper local structure.
"""
import boto3
from pathlib import Path
import csv
import sys

def normalize_s3_key(key):
    """Remove Songs/ subfolder from S3 key."""
    return key.replace('/Songs/', '/')

def s3_to_local_path(key, base_dir='ProcessedSongs_Reorganized'):
    """Convert S3 key to local Windows path."""
    normalized = normalize_s3_key(key)
    local_path = Path(base_dir) / normalized.replace('/', '\\')
    return local_path

def main():
    # Read missing files CSV
    csv_file = 'files-to-download.csv'
    
    print(f"Reading {csv_file}...")
    missing_files = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                missing_files.append(row)
    except FileNotFoundError:
        print(f"ERROR: {csv_file} not found. Run find-missing-files.py first.")
        sys.exit(1)
    
    print(f"Found {len(missing_files)} files to download")
    print()
    
    # Ask for confirmation
    print("This will download files from S3 to ProcessedSongs_Reorganized/")
    response = input("Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Download files
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, item in enumerate(missing_files, 1):
        s3_key = item['s3_key']
        local_path = s3_to_local_path(s3_key)
        
        # Create parent directory
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            print(f"[{i}/{len(missing_files)}] Downloading: {s3_key}")
            s3.download_file(bucket, s3_key, str(local_path))
            success_count += 1
        except Exception as e:
            error_count += 1
            error_msg = str(e)
            errors.append({
                's3_key': s3_key,
                'local_path': str(local_path),
                'error': error_msg
            })
            print(f"  ERROR: {error_msg}")
    
    print()
    print("=" * 80)
    print("Download Summary:")
    print(f"  Total files: {len(missing_files)}")
    print(f"  Successfully downloaded: {success_count}")
    print(f"  Errors: {error_count}")
    print("=" * 80)
    
    if errors:
        error_file = 'download-errors.csv'
        with open(error_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['s3_key', 'local_path', 'error'])
            writer.writeheader()
            writer.writerows(errors)
        print(f"\nErrors written to: {error_file}")

if __name__ == '__main__':
    main()
