#!/usr/bin/env python3
"""
Verify that files in Songs/ subfolders are duplicates of files at book root level.
"""
import boto3
import csv

def main():
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print("Analyzing S3 structure for duplicates...")
    print()
    
    # Get all PDF files with their sizes
    all_files = {}
    paginator = s3.get_paginator('list_objects_v2')
    
    print("Listing all S3 files...")
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('.pdf') and not key.startswith(('artifacts/', 'output/', 's3:/')):
                    all_files[key] = obj['Size']
    
    print(f"Found {len(all_files)} total PDF files")
    print()
    
    # Separate files in Songs/ subfolder vs root of book folder
    songs_subfolder = {}
    book_root = {}
    
    for key, size in all_files.items():
        if '/Songs/' in key:
            songs_subfolder[key] = size
        else:
            book_root[key] = size
    
    print(f"Files in Songs/ subfolders: {len(songs_subfolder)}")
    print(f"Files at book root level: {len(book_root)}")
    print()
    
    # Check for duplicates
    print("Checking for duplicates...")
    duplicates = []
    unique_to_songs = []
    
    for songs_key, songs_size in songs_subfolder.items():
        # Convert Songs/ path to expected root path
        # E.g., "America/Greatest Hits/Songs/America - Song.pdf" 
        #    -> "America/Greatest Hits/America - Song.pdf"
        root_key = songs_key.replace('/Songs/', '/')
        
        if root_key in book_root:
            root_size = book_root[root_key]
            duplicates.append({
                'songs_path': songs_key,
                'root_path': root_key,
                'songs_size': songs_size,
                'root_size': root_size,
                'size_match': songs_size == root_size
            })
        else:
            unique_to_songs.append({
                'songs_path': songs_key,
                'size': songs_size
            })
    
    print(f"Confirmed duplicates: {len(duplicates)}")
    print(f"Unique to Songs/ folder: {len(unique_to_songs)}")
    print()
    
    # Check size matches
    size_matches = sum(1 for d in duplicates if d['size_match'])
    size_mismatches = len(duplicates) - size_matches
    
    print(f"Duplicates with matching sizes: {size_matches}")
    print(f"Duplicates with different sizes: {size_mismatches}")
    print()
    
    # Write results
    if duplicates:
        with open('confirmed-duplicates.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['songs_path', 'root_path', 'songs_size', 'root_size', 'size_match'])
            writer.writeheader()
            writer.writerows(duplicates)
        print("Confirmed duplicates written to: confirmed-duplicates.csv")
    
    if unique_to_songs:
        with open('unique-to-songs-folder.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['songs_path', 'size'])
            writer.writeheader()
            writer.writerows(unique_to_songs)
        print("Unique files written to: unique-to-songs-folder.csv")
    
    print()
    
    # Show examples
    if duplicates:
        print("First 5 confirmed duplicates:")
        for dup in duplicates[:5]:
            print(f"  Songs: {dup['songs_path']}")
            print(f"  Root:  {dup['root_path']}")
            print(f"  Sizes: {dup['songs_size']} vs {dup['root_size']} - {'MATCH' if dup['size_match'] else 'MISMATCH'}")
            print()
    
    if unique_to_songs:
        print("First 5 files unique to Songs/ folder:")
        for item in unique_to_songs[:5]:
            print(f"  {item['songs_path']} ({item['size']} bytes)")
    
    print()
    print("=" * 80)
    print("Summary:")
    print(f"  Total S3 files: {len(all_files)}")
    print(f"  Files in Songs/ subfolder: {len(songs_subfolder)}")
    print(f"  Files at book root: {len(book_root)}")
    print(f"  Confirmed duplicates: {len(duplicates)} ({size_matches} size matches)")
    print(f"  Unique to Songs/ folder: {len(unique_to_songs)}")
    print("=" * 80)

if __name__ == '__main__':
    main()
