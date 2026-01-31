#!/usr/bin/env python3
"""
Find files that are truly missing locally, accounting for folder name variations.
"""
import boto3
from pathlib import Path
import csv
import re

def normalize_path(path_str, artist):
    """
    Normalize a path by removing artist prefix from book folder name.
    E.g., "Acdc/Acdc - Anthology/song.pdf" -> "Acdc/Anthology/song.pdf"
    """
    parts = path_str.replace('\\', '/').split('/')
    
    if len(parts) >= 3:
        artist_folder = parts[0]
        book_folder = parts[1]
        filename = '/'.join(parts[2:])
        
        # Remove "Artist - " prefix from book folder if present
        book_normalized = book_folder
        prefix = f"{artist} - "
        if book_folder.startswith(prefix):
            book_normalized = book_folder[len(prefix):]
        
        return f"{artist_folder}/{book_normalized}/{filename}"
    
    return path_str

def get_s3_files():
    """Get all PDF files from S3."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print("Listing S3 files...")
    
    s3_files = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.pdf') and not key.startswith(('artifacts/', 'output/', 's3:/')):
                    s3_files.append(key)
    
    print(f"Found {len(s3_files)} PDF files in S3")
    return s3_files

def get_local_files():
    """Get all local PDF files."""
    local_dir = Path('ProcessedSongs_Reorganized')
    
    print("Scanning local files...")
    
    local_files = []
    for pdf_file in local_dir.rglob('*.pdf'):
        rel_path = pdf_file.relative_to(local_dir)
        local_files.append(str(rel_path))
    
    print(f"Found {len(local_files)} PDF files locally")
    return local_files

def main():
    print("=" * 80)
    print("Finding Truly Missing Files")
    print("=" * 80)
    print()
    
    s3_files = get_s3_files()
    local_files = get_local_files()
    
    # Normalize all paths
    print("\nNormalizing paths...")
    
    # Create normalized lookup for local files
    local_normalized = {}
    for local_path in local_files:
        # Extract artist from path
        parts = local_path.split('\\')
        if len(parts) >= 1:
            artist = parts[0]
            normalized = normalize_path(local_path, artist)
            local_normalized[normalized] = local_path
    
    print(f"Normalized {len(local_normalized)} local paths")
    
    # Check which S3 files are missing
    missing = []
    for s3_key in s3_files:
        parts = s3_key.split('/')
        if len(parts) >= 1:
            artist = parts[0]
            normalized = normalize_path(s3_key, artist)
            
            if normalized not in local_normalized:
                missing.append({
                    's3_key': s3_key,
                    'normalized': normalized,
                    'artist': artist
                })
    
    print(f"\nTruly missing files: {len(missing)}")
    
    if missing:
        # Write to CSV
        output_file = 'truly-missing-files.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['s3_key', 'normalized', 'artist'])
            writer.writeheader()
            writer.writerows(missing)
        
        print(f"Written to: {output_file}")
        
        # Show first 20
        print("\nFirst 20 missing files:")
        for item in missing[:20]:
            print(f"  {item['s3_key']}")
        
        # Count by artist
        by_artist = {}
        for item in missing:
            artist = item['artist']
            by_artist[artist] = by_artist.get(artist, 0) + 1
        
        print(f"\nMissing files by artist (top 10):")
        for artist, count in sorted(by_artist.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {artist}: {count}")
    
    print("\n" + "=" * 80)
    print(f"Summary:")
    print(f"  S3 total: {len(s3_files)}")
    print(f"  Local total: {len(local_files)}")
    print(f"  Truly missing: {len(missing)}")
    print(f"  Duplicates in S3: {len(s3_files) - len(local_files) - len(missing)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
