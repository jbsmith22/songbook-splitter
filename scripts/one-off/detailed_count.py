#!/usr/bin/env python3
"""Detailed count of ProcessedSongs folders."""

from pathlib import Path

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

total_book_folders = 0
folders_with_pdfs = 0
folders_without_pdfs = 0

for artist_dir in sorted(PROCESSED_SONGS_PATH.iterdir()):
    if not artist_dir.is_dir():
        continue
    
    artist_books = 0
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        total_book_folders += 1
        pdf_files = list(book_dir.glob("*.pdf"))
        
        if pdf_files:
            folders_with_pdfs += 1
            artist_books += 1
        else:
            folders_without_pdfs += 1

print(f"Total book folders (directories): {total_book_folders}")
print(f"Folders WITH PDFs: {folders_with_pdfs}")
print(f"Folders WITHOUT PDFs (empty): {folders_without_pdfs}")
print()
print(f"So the correct count is: {folders_with_pdfs} books with songs")
