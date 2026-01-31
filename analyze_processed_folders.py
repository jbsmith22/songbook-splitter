#!/usr/bin/env python3
"""
Analyze ProcessedSongs folder structure.
Count leaf folders (book folders) vs parent folders (artist folders).
"""

from pathlib import Path

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

print("=" * 80)
print("PROCESSEDSONGS FOLDER ANALYSIS")
print("=" * 80)
print()

artist_folders = 0
book_folders_with_pdfs = 0
book_folders_empty = 0
book_folders_with_subfolders = 0

for artist_dir in sorted(PROCESSED_SONGS_PATH.iterdir()):
    if not artist_dir.is_dir():
        continue
    
    artist_folders += 1
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        # Check if this folder has subfolders
        subfolders = [d for d in book_dir.iterdir() if d.is_dir()]
        if subfolders:
            book_folders_with_subfolders += 1
            continue
        
        # Check if it has PDF files
        pdf_files = list(book_dir.glob("*.pdf"))
        
        if pdf_files:
            book_folders_with_pdfs += 1
        else:
            book_folders_empty += 1

print(f"Artist folders (top level): {artist_folders}")
print()
print(f"Book folders (leaf level):")
print(f"  - With PDF files: {book_folders_with_pdfs}")
print(f"  - Empty (no PDFs): {book_folders_empty}")
print(f"  - With subfolders (not leaf): {book_folders_with_subfolders}")
print()
print(f"Total book folders: {book_folders_with_pdfs + book_folders_empty + book_folders_with_subfolders}")
print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Leaf folders with PDFs (actual books): {book_folders_with_pdfs}")
print(f"Empty leaf folders: {book_folders_empty}")
print(f"Non-leaf folders (have subfolders): {book_folders_with_subfolders}")
