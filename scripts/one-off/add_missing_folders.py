#!/usr/bin/env python3
"""
Add the 22 missing folders back to the CSV and try to match them with source PDFs.
"""

import csv
from pathlib import Path
from difflib import SequenceMatcher
import re

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
input_csv = Path("book_reconciliation_verified.csv")
output_csv = Path("book_reconciliation_complete.csv")

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

print("Finding missing folders and their source PDFs...")
print()

# Get all folders from ProcessedSongs
all_folders = []
for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            all_folders.append((artist_dir.name, book_dir.name, str(book_dir)))

# Get folders already in CSV
csv_folders = set()
with open(input_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['Folder_Path']:
            csv_folders.add(row['Folder_Path'])

# Find missing folders
missing_folders = [(a, b, p) for a, b, p in all_folders if p not in csv_folders]

print(f"Found {len(missing_folders)} folders not in CSV")

# Get all source PDFs
source_pdfs = []
for pdf_path in SHEET_MUSIC_PATH.rglob("*.pdf"):
    if "_Fake Books" in str(pdf_path):
        continue
    
    relative = pdf_path.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        book_name = pdf_path.stem
        source_pdfs.append((artist, book_name, str(pdf_path)))

# Get PDFs already matched in CSV
csv_pdfs = set()
with open(input_csv, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['PDF_Path']:
            csv_pdfs.add(row['PDF_Path'])

# Available PDFs for matching
available_pdfs = [(a, b, p) for a, b, p in source_pdfs if p not in csv_pdfs]

print(f"Found {len(available_pdfs)} unmatched PDFs available")
print()

# Try to match missing folders with available PDFs
new_rows = []
for folder_artist, folder_book, folder_path in missing_folders:
    best_score = 0
    best_pdf = None
    
    for pdf_artist, pdf_book, pdf_path in available_pdfs:
        artist_match = similarity(folder_artist, pdf_artist)
        book_match = similarity(folder_book, pdf_book)
        score = (artist_match * 0.4) + (book_match * 0.6)
        
        if score > best_score:
            best_score = score
            best_pdf = (pdf_artist, pdf_book, pdf_path)
    
    # Create new row
    if best_pdf and best_score > 0.5:
        pdf_artist, pdf_book, pdf_path = best_pdf
        new_rows.append({
            'Status': 'MATCHED',
            'Match_Score': f'{best_score:.2%}',
            'PDF_Artist': pdf_artist,
            'PDF_Book': pdf_book,
            'PDF_Path': pdf_path,
            'Folder_Artist': folder_artist,
            'Folder_Book': folder_book,
            'Folder_Path': folder_path,
            'PDF_Exists': 'YES',
            'Folder_Exists': 'YES'
        })
        # Remove from available
        available_pdfs.remove(best_pdf)
    else:
        # No good match found
        new_rows.append({
            'Status': 'UNMATCHED_FOLDER',
            'Match_Score': '',
            'PDF_Artist': '',
            'PDF_Book': '',
            'PDF_Path': '',
            'Folder_Artist': folder_artist,
            'Folder_Book': folder_book,
            'Folder_Path': folder_path,
            'PDF_Exists': '',
            'Folder_Exists': 'YES'
        })

print(f"Matched {sum(1 for r in new_rows if r['Status'] == 'MATCHED')} folders to PDFs")
print(f"Left {sum(1 for r in new_rows if r['Status'] == 'UNMATCHED_FOLDER')} folders unmatched")
print()

# Read existing CSV and append new rows
with open(input_csv, 'r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = reader.fieldnames
    existing_rows = list(reader)

# Write combined output
with open(output_csv, 'w', newline='', encoding='utf-8') as f_out:
    writer = csv.DictWriter(f_out, fieldnames=fieldnames)
    writer.writeheader()
    
    # Write existing rows
    for row in existing_rows:
        writer.writerow(row)
    
    # Write new rows
    for row in new_rows:
        writer.writerow(row)

print(f"✓ Output saved to: {output_csv}")
print()
print("SUMMARY:")
print(f"  Original rows: {len(existing_rows)}")
print(f"  Added rows: {len(new_rows)}")
print(f"  Total rows: {len(existing_rows) + len(new_rows)}")
