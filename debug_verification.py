#!/usr/bin/env python3
from pathlib import Path

processed_songs_path = Path("ProcessedSongs")
processed_folders = {}
processed_folders_lower = {}

artist_count = 0
book_count = 0

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir():
        print(f"Skipping non-dir: {artist_folder}")
        continue
    if artist_folder.name.startswith('.'):
        print(f"Skipping hidden: {artist_folder}")
        continue
    
    artist_count += 1
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir():
            continue
        if book_folder.name.startswith('.'):
            continue
        
        book_count += 1
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            folder_name = book_folder.name
            processed_folders[folder_name] = book_folder
            processed_folders_lower[folder_name.lower()] = folder_name

print(f"Artist folders scanned: {artist_count}")
print(f"Book folders scanned: {book_count}")
print(f"Folders added to dict: {len(processed_folders)}")
print(f"Folders in lowercase dict: {len(processed_folders_lower)}")

# Check for duplicates
if len(processed_folders) != len(processed_folders_lower):
    print(f"\n⚠ WARNING: Duplicate folder names with different cases!")
    print(f"  Unique names: {len(processed_folders)}")
    print(f"  Unique lowercase: {len(processed_folders_lower)}")
