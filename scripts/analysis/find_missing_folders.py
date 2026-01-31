#!/usr/bin/env python3
"""
Find the 22 folders that exist in ProcessedSongs but aren't in the CSV.
"""

import csv
from pathlib import Path

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
csv_file = Path("book_reconciliation_verified.csv")

print("=" * 80)
print("FINDING MISSING FOLDERS")
print("=" * 80)
print()

# Get all folders from ProcessedSongs
print("Step 1: Scanning ProcessedSongs...")
all_folders = set()
for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            all_folders.add(str(book_dir))

print(f"✓ Found {len(all_folders)} folders in ProcessedSongs")

# Get all folders from CSV
print("Step 2: Reading CSV...")
csv_folders = set()
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Folder_Path']:
            csv_folders.add(row['Folder_Path'])

print(f"✓ Found {len(csv_folders)} folder paths in CSV")
print()

# Find missing folders
missing_from_csv = all_folders - csv_folders

print("=" * 80)
print(f"FOLDERS IN PROCESSEDSONGS BUT NOT IN CSV: {len(missing_from_csv)}")
print("=" * 80)

if missing_from_csv:
    from collections import defaultdict
    by_artist = defaultdict(list)
    
    for folder_path in sorted(missing_from_csv):
        path = Path(folder_path)
        artist = path.parent.name
        book = path.name
        by_artist[artist].append((book, folder_path))
    
    for artist in sorted(by_artist.keys()):
        print(f"\n{artist}:")
        for book, path in sorted(by_artist[artist]):
            print(f"  - {book}")
            print(f"    Path: {path}")
else:
    print("\n✓ All folders are accounted for in the CSV!")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total folders in ProcessedSongs: {len(all_folders)}")
print(f"Folders in CSV: {len(csv_folders)}")
print(f"Missing from CSV: {len(missing_from_csv)}")
