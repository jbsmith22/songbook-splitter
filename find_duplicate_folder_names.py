#!/usr/bin/env python3
from pathlib import Path
from collections import defaultdict

processed_songs_path = Path("ProcessedSongs")
folder_names = defaultdict(list)

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir() or artist_folder.name.startswith('.'):
        continue
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir() or book_folder.name.startswith('.'):
            continue
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            folder_names[book_folder.name].append(str(book_folder))

# Find duplicates
duplicates = {name: paths for name, paths in folder_names.items() if len(paths) > 1}

if duplicates:
    print(f"Found {len(duplicates)} duplicate folder names:")
    print()
    for name, paths in sorted(duplicates.items()):
        print(f"Folder name: {name}")
        for path in paths:
            print(f"  - {path}")
        print()
else:
    print("No duplicate folder names found")
