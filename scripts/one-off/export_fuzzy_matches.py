#!/usr/bin/env python3
"""
Export fuzzy matching results to CSV for review.
"""

from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict
import csv
import re

SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def normalize_name(name):
    """Normalize a name for comparison."""
    name = name.lower()
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    name = name.replace(' - ', ' ')
    name = name.replace('  ', ' ').strip()
    return name

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

print("Generating CSV export...")

# Load source PDFs
source_pdfs = []
for pdf_path in SHEET_MUSIC_PATH.rglob("*.pdf"):
    if "_Fake Books" in str(pdf_path):
        continue
    
    relative = pdf_path.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        book_name = pdf_path.stem
        source_pdfs.append((artist, book_name, pdf_path))

# Load processed folders
processed_folders = []
for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            artist = artist_dir.name
            book_name = book_dir.name
            processed_folders.append((artist, book_name, book_dir))

# Create matches
matched_pdfs = set()
matched_folders = set()
matches = []

for pdf_artist, pdf_book, pdf_path in source_pdfs:
    best_score = 0
    best_folder = None
    
    for i, (folder_artist, folder_book, folder_path) in enumerate(processed_folders):
        if i in matched_folders:
            continue
        
        artist_match = similarity(pdf_artist, folder_artist)
        book_match = similarity(pdf_book, folder_book)
        score = (artist_match * 0.4) + (book_match * 0.6)
        
        if score > best_score:
            best_score = score
            best_folder = i
    
    if best_score > 0.5:
        folder_info = processed_folders[best_folder]
        matches.append(((pdf_artist, pdf_book, pdf_path), folder_info, best_score))
        matched_pdfs.add((pdf_artist, pdf_book))
        matched_folders.add(best_folder)

unmatched_pdfs = [(a, b, p) for a, b, p in source_pdfs if (a, b) not in matched_pdfs]
unmatched_folders = [processed_folders[i] for i in range(len(processed_folders)) if i not in matched_folders]

# Export to CSV
output_file = Path("book_reconciliation.csv")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Status', 'Match_Score', 'PDF_Artist', 'PDF_Book', 'PDF_Path', 'Folder_Artist', 'Folder_Book', 'Folder_Path'])
    
    # Write matched books
    for (pdf_artist, pdf_book, pdf_path), (folder_artist, folder_book, folder_path), score in sorted(matches, key=lambda x: -x[2]):
        writer.writerow([
            'MATCHED',
            f'{score:.2%}',
            pdf_artist,
            pdf_book,
            str(pdf_path),
            folder_artist,
            folder_book,
            str(folder_path)
        ])
    
    # Write unmatched PDFs
    for pdf_artist, pdf_book, pdf_path in sorted(unmatched_pdfs):
        writer.writerow([
            'UNMATCHED_PDF',
            '',
            pdf_artist,
            pdf_book,
            str(pdf_path),
            '',
            '',
            ''
        ])
    
    # Write unmatched folders
    for folder_artist, folder_book, folder_path in sorted(unmatched_folders):
        writer.writerow([
            'UNMATCHED_FOLDER',
            '',
            '',
            '',
            '',
            folder_artist,
            folder_book,
            str(folder_path)
        ])

print(f"✓ Exported to: {output_file}")
print()
print(f"Summary:")
print(f"  Matched: {len(matches)}")
print(f"  Unmatched PDFs: {len(unmatched_pdfs)}")
print(f"  Unmatched Folders: {len(unmatched_folders)}")
print(f"  Total rows: {len(matches) + len(unmatched_pdfs) + len(unmatched_folders)}")
