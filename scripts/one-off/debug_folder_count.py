#!/usr/bin/env python3
from pathlib import Path

processed_songs_path = Path("ProcessedSongs")
total_folders = 0
folders_with_pdfs = 0

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir():
        continue
    if artist_folder.name.startswith('.'):
        continue
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir():
            continue
        if book_folder.name.startswith('.'):
            continue
        
        total_folders += 1
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            folders_with_pdfs += 1

print(f"Total book folders: {total_folders}")
print(f"Folders with PDFs: {folders_with_pdfs}")
print(f"Empty folders: {total_folders - folders_with_pdfs}")
