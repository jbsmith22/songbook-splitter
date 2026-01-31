#!/usr/bin/env python3
"""Count actual book directories in ProcessedSongs."""

from pathlib import Path

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

book_count = 0
artist_count = 0

for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    
    artist_count += 1
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        # Check if it has PDF files
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            book_count += 1

print(f"Artists: {artist_count}")
print(f"Books (directories with PDFs): {book_count}")
