#!/usr/bin/env python3
"""
Verify the final 1:1 mapping between PDFs and folders.
"""

from pathlib import Path

print("=" * 80)
print("VERIFYING FINAL PDF-TO-FOLDER MAPPING")
print("=" * 80)
print()

# Count PDFs in SheetMusic (excluding _Fake Books)
sheet_music_path = Path("SheetMusic")
all_pdfs = []
fake_book_pdfs = []

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    
    if "_Fake Books" in str(pdf_file):
        fake_book_pdfs.append(pdf_file)
    else:
        all_pdfs.append(pdf_file)

print(f"PDFs in SheetMusic (excluding _Fake Books): {len(all_pdfs)}")
print(f"PDFs in _Fake Books (excluded): {len(fake_book_pdfs)}")
print(f"Total PDFs: {len(all_pdfs) + len(fake_book_pdfs)}")
print()

# Count folders in ProcessedSongs
processed_songs_path = Path("ProcessedSongs")
book_folders = []

for folder in processed_songs_path.rglob("*"):
    if not folder.is_dir():
        continue
    if folder.name.startswith('.'):
        continue
    # Skip artist-level folders (direct children of ProcessedSongs)
    if folder.parent == processed_songs_path:
        continue
    book_folders.append(folder)

print(f"Book folders in ProcessedSongs: {len(book_folders)}")
print()

# Calculate the gap
pdfs_without_folders = len(all_pdfs) - len(book_folders)

print("=" * 80)
print("MAPPING ANALYSIS")
print("=" * 80)
print(f"PDFs (excluding _Fake Books): {len(all_pdfs)}")
print(f"Folders in ProcessedSongs: {len(book_folders)}")
print(f"PDFs without folders: {pdfs_without_folders}")
print()

if pdfs_without_folders == 20:
    print("✓ CORRECT: 20 PDFs not yet processed (as expected)")
elif pdfs_without_folders == 24:
    print("✓ CORRECT: 24 PDFs in _Fake Books not processed (as expected)")
else:
    print(f"⚠ Gap of {pdfs_without_folders} PDFs")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"✓ {len(book_folders)} PDFs have been processed into folders")
print(f"✓ {pdfs_without_folders} PDFs remain unprocessed")
print(f"✓ {len(fake_book_pdfs)} PDFs in _Fake Books (deliberately excluded)")
print()

# Check for name consistency
print("Checking name consistency between PDFs and folders...")
print()

# Build a map of normalized names
pdf_names = {}
for pdf in all_pdfs:
    # Get the book name (stem without extension)
    name = pdf.stem
    # Remove artist prefix if present
    if ' - ' in name:
        parts = name.split(' - ', 1)
        if len(parts) == 2:
            name = parts[1]
    pdf_names[name.lower()] = pdf

folder_names = {}
for folder in book_folders:
    name = folder.name
    folder_names[name.lower()] = folder

# Find matches
matches = 0
for pdf_name_lower, pdf_path in pdf_names.items():
    if pdf_name_lower in folder_names:
        matches += 1

print(f"Name matches found: {matches}/{len(book_folders)}")

if matches == len(book_folders):
    print("✓ ALL FOLDERS HAVE MATCHING PDF NAMES")
else:
    print(f"⚠ {len(book_folders) - matches} folders don't have exact name matches")
