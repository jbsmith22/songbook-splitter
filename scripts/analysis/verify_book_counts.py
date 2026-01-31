#!/usr/bin/env python3
"""Verify book counts and identify discrepancies."""

from pathlib import Path

SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

# Count all PDFs in SheetMusic
all_pdfs = list(SHEET_MUSIC_PATH.rglob("*.pdf"))
print(f"Total PDFs in SheetMusic: {len(all_pdfs)}")

# Count PDFs in _Fake Books
fake_books = list((SHEET_MUSIC_PATH / "_Fake Books").glob("*.pdf")) if (SHEET_MUSIC_PATH / "_Fake Books").exists() else []
print(f"PDFs in _Fake Books (excluded): {len(fake_books)}")

# Count PDFs excluding _Fake Books
non_fake_pdfs = [p for p in all_pdfs if "_Fake Books" not in str(p)]
print(f"PDFs excluding _Fake Books: {len(non_fake_pdfs)}")
print()

# Count processed books
processed_count = 0
for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            processed_count += 1

print(f"Book folders in ProcessedSongs: {processed_count}")
print()
print(f"Difference: {len(non_fake_pdfs)} - {processed_count} = {len(non_fake_pdfs) - processed_count} books not yet processed")
