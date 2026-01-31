#!/usr/bin/env python3
"""
Verify that PDF names and folder names match EXACTLY (including case).
Checks actual filesystem, not CSV data.
Uses case-insensitive search to find folders, then checks exact match.
"""

from pathlib import Path

print("=" * 80)
print("EXACT MATCH VERIFICATION")
print("=" * 80)
print()

# Get all PDFs (excluding Fake Books)
sheet_music_path = Path("SheetMusic")
pdf_books = {}

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    # The book name is the PDF stem
    book_name = pdf_file.stem
    pdf_books[book_name] = pdf_file

print(f"Total PDFs in SheetMusic: {len(pdf_books)}")

# Get all folder names in ProcessedSongs
# Build a map: lowercase name -> actual folder object
processed_songs_path = Path("ProcessedSongs")
processed_folders = {}  # actual name -> folder path
processed_folders_lower = {}  # lowercase name -> actual name

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
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            folder_name = book_folder.name
            processed_folders[folder_name] = book_folder
            processed_folders_lower[folder_name.lower()] = folder_name

print(f"Total book folders in ProcessedSongs: {len(processed_folders)}")
print()

# Check for exact matches
exact_matches = []
case_mismatches = []
unprocessed = []

for pdf_name, pdf_path in pdf_books.items():
    if pdf_name in processed_folders:
        # Exact match (including case)
        exact_matches.append(pdf_name)
    elif pdf_name.lower() in processed_folders_lower:
        # Case mismatch - folder exists but with different case
        actual_folder_name = processed_folders_lower[pdf_name.lower()]
        case_mismatches.append({
            'pdf_name': pdf_name,
            'folder_name': actual_folder_name
        })
    else:
        # No folder at all
        unprocessed.append(pdf_name)

print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"✓ Exact matches (PDF == Folder):    {len(exact_matches)}")
print(f"⚠ Case mismatches (PDF ≈ Folder):   {len(case_mismatches)}")
print(f"✗ Unprocessed (no folder):          {len(unprocessed)}")
print()

if case_mismatches:
    print("=" * 80)
    print(f"REMAINING CASE MISMATCHES ({len(case_mismatches)})")
    print("=" * 80)
    for item in case_mismatches:
        print(f"PDF:    {item['pdf_name']}")
        print(f"Folder: {item['folder_name']}")
        print()
else:
    print("=" * 80)
    print("✓✓✓ PERFECT 1:1 MAPPING ✓✓✓")
    print("=" * 80)
    print("All PDF names match folder names EXACTLY (including case)!")
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total PDFs:              {len(pdf_books)}")
print(f"  - With exact folders:  {len(exact_matches)}")
print(f"  - With case mismatch:  {len(case_mismatches)}")
print(f"  - Unprocessed:         {len(unprocessed)}")
print()
print(f"Processed: {len(exact_matches) + len(case_mismatches)}/{len(pdf_books)} ({100*(len(exact_matches) + len(case_mismatches))/len(pdf_books):.1f}%)")
print(f"Exact match: {len(exact_matches)}/{len(pdf_books)} ({100*len(exact_matches)/len(pdf_books):.1f}%)")
