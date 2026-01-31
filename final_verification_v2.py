#!/usr/bin/env python3
"""
Final comprehensive verification - handles duplicate folder names properly.
"""

from pathlib import Path
from collections import defaultdict

print("=" * 80)
print("FINAL VERIFICATION - POST CASE-MISMATCH FIX")
print("=" * 80)
print()

# Get all PDFs (excluding Fake Books) with their full paths
sheet_music_path = Path("SheetMusic")
pdf_books = {}  # pdf_name -> pdf_path

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    pdf_books[pdf_file.stem] = pdf_file

print(f"Total PDFs in SheetMusic: {len(pdf_books)}")

# Get all folders with PDFs - store all occurrences
processed_songs_path = Path("ProcessedSongs")
processed_folders = defaultdict(list)  # folder_name -> list of folder paths

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir() or artist_folder.name.startswith('.'):
        continue
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir() or book_folder.name.startswith('.'):
            continue
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            processed_folders[book_folder.name].append(book_folder)

total_folders = sum(len(paths) for paths in processed_folders.values())
print(f"Total folders with PDFs: {total_folders}")
print(f"Unique folder names: {len(processed_folders)}")
print()

# Check for exact matches (case-sensitive)
exact_matches = []
case_mismatches = []
unprocessed = []

for pdf_name, pdf_path in pdf_books.items():
    if pdf_name in processed_folders:
        # Exact match (including case)
        exact_matches.append(pdf_name)
    else:
        # Check for case mismatch
        found_case_mismatch = False
        for folder_name in processed_folders.keys():
            if folder_name.lower() == pdf_name.lower():
                case_mismatches.append({
                    'pdf_name': pdf_name,
                    'folder_name': folder_name
                })
                found_case_mismatch = True
                break
        
        if not found_case_mismatch:
            unprocessed.append(pdf_name)

print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"✓ Exact matches (PDF == Folder):    {len(exact_matches)}")
print(f"⚠ Case mismatches (PDF ≈ Folder):   {len(case_mismatches)}")
print(f"✗ Unprocessed (no folder):          {len(unprocessed)}")
print()

if case_mismatches:
    print("Remaining case mismatches:")
    for item in case_mismatches[:10]:
        print(f"  PDF:    {item['pdf_name']}")
        print(f"  Folder: {item['folder_name']}")
    if len(case_mismatches) > 10:
        print(f"  ... and {len(case_mismatches) - 10} more")
    print()
else:
    print("=" * 80)
    print("✓✓✓ SUCCESS ✓✓✓")
    print("=" * 80)
    print("All processed PDFs have folders with EXACTLY matching names!")
    print("(including case)")
    print()

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total PDFs:              {len(pdf_books)}")
print(f"  - Processed:           {len(exact_matches)}")
print(f"  - Unprocessed:         {len(unprocessed)}")
print()
print(f"Total folders:           {total_folders}")
print(f"Unique folder names:     {len(processed_folders)}")
print()
print(f"Completion: {len(exact_matches)}/{len(pdf_books)} ({100*len(exact_matches)/len(pdf_books):.1f}%)")
print()
print(f"Expected unprocessed: 20")
print(f"Actual unprocessed:   {len(unprocessed)}")
print()

if len(unprocessed) == 20:
    print("✓ Unprocessed count matches expectations!")
    print()
    print("These 20 PDFs are ready for AWS processing:")
    for i, pdf_name in enumerate(sorted(unprocessed), 1):
        print(f"  {i}. {pdf_name}")
else:
    print(f"⚠ Unprocessed count mismatch (expected 20, got {len(unprocessed)})")
