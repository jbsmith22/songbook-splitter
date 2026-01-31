#!/usr/bin/env python3
"""
Verify what files exist in S3 vs locally with proper Unicode handling.
"""
import boto3
import os
from pathlib import Path
import csv

def get_s3_files():
    """Get all files from S3 bucket with proper Unicode handling."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print(f"Listing all files in s3://{bucket}/...")
    
    s3_files = []
    paginator = s3.get_paginator('list_objects_v2')
    
    # List all objects in bucket (no prefix filter)
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                # Only include PDF files, exclude special prefixes
                if key.endswith('.pdf') and not key.startswith(('artifacts/', 'output/', 's3:/')):
                    s3_files.append(key)
    
    print(f"Found {len(s3_files)} PDF files in S3")
    return s3_files

def get_local_files():
    """Get all local files from ProcessedSongs_Reorganized."""
    local_dir = Path('ProcessedSongs_Reorganized')
    
    if not local_dir.exists():
        print(f"ERROR: {local_dir} does not exist")
        return []
    
    print(f"Scanning {local_dir}...")
    
    local_files = []
    for pdf_file in local_dir.rglob('*.pdf'):
        # Get relative path from ProcessedSongs_Reorganized
        rel_path = pdf_file.relative_to(local_dir)
        local_files.append(str(rel_path))
    
    print(f"Found {len(local_files)} PDF files locally")
    return local_files

def s3_key_to_local_path(s3_key):
    """Convert S3 key to expected local path format."""
    # S3 format: Artist/Book/Artist - Song.pdf
    # Local format: Artist\Book\Artist - Song.pdf
    
    # Convert forward slashes to backslashes for Windows comparison
    path = s3_key.replace('/', '\\')
    
    return path

def main():
    print("=" * 80)
    print("S3 vs Local File Verification")
    print("=" * 80)
    print()
    
    # Get files from both sources
    s3_files = get_s3_files()
    local_files = set(get_local_files())
    
    print()
    print("=" * 80)
    print("Comparing...")
    print("=" * 80)
    print()
    
    # Find files in S3 but not local
    missing_locally = []
    
    for s3_key in s3_files:
        local_path = s3_key_to_local_path(s3_key)
        if local_path and local_path not in local_files:
            missing_locally.append({
                's3_key': s3_key,
                'expected_local_path': local_path
            })
    
    print(f"Files in S3 but NOT local: {len(missing_locally)}")
    print()
    
    if missing_locally:
        # Write to CSV with UTF-8 encoding
        output_file = 'missing-files-verified.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['s3_key', 'expected_local_path'])
            writer.writeheader()
            writer.writerows(missing_locally)
        
        print(f"Missing files written to: {output_file}")
        print()
        
        # Show first 10 examples
        print("First 10 missing files:")
        for item in missing_locally[:10]:
            print(f"  S3: {item['s3_key']}")
            print(f"  Expected: {item['expected_local_path']}")
            print()
    
    print("=" * 80)
    print("Summary:")
    print(f"  Total S3 files: {len(s3_files)}")
    print(f"  Total local files: {len(local_files)}")
    print(f"  Missing locally: {len(missing_locally)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
