#!/usr/bin/env python3
"""
Count files in S3 that are in 'Songs/' subfolders (old structure).
"""
import boto3
import csv

def main():
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print("Finding files in 'Songs/' subfolders...")
    
    songs_subfolder_files = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.pdf') and '/Songs/' in key:
                    songs_subfolder_files.append(key)
    
    print(f"\nFound {len(songs_subfolder_files)} files in 'Songs/' subfolders")
    
    if songs_subfolder_files:
        # Write to CSV
        output_file = 'songs-subfolder-files.csv'
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['s3_key'])
            for key in songs_subfolder_files:
                writer.writerow([key])
        
        print(f"Written to: {output_file}")
        
        # Show first 20
        print("\nFirst 20 files:")
        for key in songs_subfolder_files[:20]:
            print(f"  {key}")
        
        # Count by artist
        by_artist = {}
        for key in songs_subfolder_files:
            artist = key.split('/')[0]
            by_artist[artist] = by_artist.get(artist, 0) + 1
        
        print(f"\nBy artist (top 10):")
        for artist, count in sorted(by_artist.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {artist}: {count}")

if __name__ == '__main__':
    main()
