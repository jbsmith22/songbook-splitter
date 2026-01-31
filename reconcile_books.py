#!/usr/bin/env python3
"""
Reconcile SheetMusic source PDFs with ProcessedSongs output folders.
Identify which books are missing, extra, or mismatched.
"""

from pathlib import Path
from collections import defaultdict

SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

print("=" * 80)
print("BOOK RECONCILIATION REPORT")
print("=" * 80)
print()

# Step 1: Get all source PDFs (excluding _Fake Books)
print("Step 1: Scanning SheetMusic folder...")
source_books = {}  # (artist, book_name) -> pdf_path

for pdf_path in SHEET_MUSIC_PATH.rglob("*.pdf"):
    # Skip _Fake Books
    if "_Fake Books" in str(pdf_path):
        continue
    
    relative = pdf_path.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        book_name = pdf_path.stem  # filename without .pdf
        source_books[(artist, book_name)] = pdf_path

print(f"✓ Found {len(source_books)} source PDFs (excluding _Fake Books)")
print()

# Step 2: Get all processed book folders
print("Step 2: Scanning ProcessedSongs folder...")
processed_books = {}  # (artist, book_name) -> folder_path

for artist_dir in PROCESSED_SONGS_PATH.iterdir():
    if not artist_dir.is_dir():
        continue
    
    for book_dir in artist_dir.iterdir():
        if not book_dir.is_dir():
            continue
        
        # Check if it has PDFs
        pdf_files = list(book_dir.glob("*.pdf"))
        if pdf_files:
            artist = artist_dir.name
            book_name = book_dir.name
            processed_books[(artist, book_name)] = book_dir

print(f"✓ Found {len(processed_books)} processed book folders")
print()

# Step 3: Find matches and mismatches
print("Step 3: Comparing...")
print()

source_keys = set(source_books.keys())
processed_keys = set(processed_books.keys())

# Exact matches
exact_matches = source_keys & processed_keys
print(f"✓ Exact matches: {len(exact_matches)}")

# Books in source but not processed
missing_from_processed = source_keys - processed_keys
print(f"✗ In SheetMusic but NOT in ProcessedSongs: {len(missing_from_processed)}")

# Books in processed but not in source
extra_in_processed = processed_keys - source_keys
print(f"⚠ In ProcessedSongs but NOT in SheetMusic: {len(extra_in_processed)}")

print()
print("=" * 80)
print("DETAILED DISCREPANCIES")
print("=" * 80)
print()

# Show missing books
if missing_from_processed:
    print(f"MISSING FROM PROCESSEDSONGS ({len(missing_from_processed)} books):")
    print("-" * 80)
    by_artist = defaultdict(list)
    for artist, book in sorted(missing_from_processed):
        by_artist[artist].append(book)
    
    for artist in sorted(by_artist.keys()):
        print(f"\n{artist}:")
        for book in sorted(by_artist[artist]):
            print(f"  - {book}")
    print()

# Show extra books
if extra_in_processed:
    print(f"EXTRA IN PROCESSEDSONGS ({len(extra_in_processed)} books):")
    print("-" * 80)
    by_artist = defaultdict(list)
    for artist, book in sorted(extra_in_processed):
        by_artist[artist].append(book)
    
    for artist in sorted(by_artist.keys()):
        print(f"\n{artist}:")
        for book in sorted(by_artist[artist]):
            print(f"  - {book}")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Source PDFs (SheetMusic, excluding _Fake Books): {len(source_books)}")
print(f"Processed folders (ProcessedSongs): {len(processed_books)}")
print(f"Exact matches: {len(exact_matches)}")
print(f"Missing from ProcessedSongs: {len(missing_from_processed)}")
print(f"Extra in ProcessedSongs: {len(extra_in_processed)}")
print()

# Expected: source = processed + missing - extra
expected = len(processed_books) + len(missing_from_processed) - len(extra_in_processed)
print(f"Verification: {len(processed_books)} + {len(missing_from_processed)} - {len(extra_in_processed)} = {expected}")
print(f"Should equal source count: {len(source_books)}")
print(f"Match: {'✓ YES' if expected == len(source_books) else '✗ NO'}")
