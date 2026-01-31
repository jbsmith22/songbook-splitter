#!/usr/bin/env python3
"""
Final comprehensive verification after case mismatch fixes.
"""

from pathlib import Path

print("=" * 80)
print("FINAL VERIFICATION - POST CASE-MISMATCH FIX")
print("=" * 80)
print()

# Get all PDFs (excluding Fake Books)
sheet_music_path = Path("SheetMusic")
pdf_books = []

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    pdf_books.append(pdf_file.stem)

print(f"Total PDFs in SheetMusic: {len(pdf_books)}")

# Get all folders with PDFs
processed_songs_path = Path("ProcessedSongs")
processed_folders = []

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir() or artist_folder.name.startswith('.'):
        continue
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir() or book_folder.name.startswith('.'):
            continue
        
        # Check if folder has PDFs
        pdfs = list(book_folder.glob("*.pdf"))
        if pdfs:
            processed_folders.append(book_folder.name)

print(f"Total folders with PDFs: {len(processed_folders)}")
print()

# Check for exact matches (case-sensitive)
exact_matches = 0
case_mismatches = 0
unprocessed = 0

for pdf_name in pdf_books:
    if pdf_name in processed_folders:
        exact_matches += 1
    elif pdf_name.lower() in [f.lower() for f in processed_folders]:
        case_mismatches += 1
    else:
        unprocessed += 1

print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"✓ Exact matches (PDF == Folder):    {exact_matches}")
print(f"⚠ Case mismatches (PDF ≈ Folder):   {case_mismatches}")
print(f"✗ Unprocessed (no folder):          {unprocessed}")
print()

if case_mismatches == 0:
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
print(f"  - Processed:           {exact_matches}")
print(f"  - Unprocessed:         {unprocessed}")
print()
print(f"Completion: {exact_matches}/{len(pdf_books)} ({100*exact_matches/len(pdf_books):.1f}%)")
print()
print(f"Expected unprocessed: 20")
print(f"Actual unprocessed:   {unprocessed}")
print()

if unprocessed == 20:
    print("✓ Unprocessed count matches expectations!")
else:
    print(f"⚠ Unprocessed count mismatch (expected 20, got {unprocessed})")
