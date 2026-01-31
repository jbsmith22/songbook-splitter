#!/usr/bin/env python3
"""
Fuzzy match SheetMusic PDFs to ProcessedSongs folders.
Use best matching to create 1:1 mapping.
"""

from pathlib import Path
from difflib import SequenceMatcher
from collections import defaultdict

SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def normalize_name(name):
    """Normalize a name for comparison."""
    # Remove common variations
    name = name.lower()
    # Remove brackets and their contents
    import re
    name = re.sub(r'\[.*?\]', '', name)
    name = re.sub(r'\(.*?\)', '', name)
    # Remove common words
    name = name.replace(' - ', ' ')
    name = name.replace('  ', ' ').strip()
    return name

def similarity(a, b):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, normalize_name(a), normalize_name(b)).ratio()

print("=" * 80)
print("FUZZY MATCHING: SheetMusic PDFs -> ProcessedSongs Folders")
print("=" * 80)
print()

# Step 1: Get all source PDFs (excluding _Fake Books)
print("Step 1: Loading source PDFs...")
source_pdfs = []  # [(artist, book_name, pdf_path)]

for pdf_path in SHEET_MUSIC_PATH.rglob("*.pdf"):
    if "_Fake Books" in str(pdf_path):
        continue
    
    relative = pdf_path.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        book_name = pdf_path.stem
        source_pdfs.append((artist, book_name, pdf_path))

print(f"✓ Found {len(source_pdfs)} source PDFs")

# Step 2: Get all processed folders
print("Step 2: Loading processed folders...")
processed_folders = []  # [(artist, book_name, folder_path)]

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

print(f"✓ Found {len(processed_folders)} processed folders")
print()

# Step 3: Create best matches
print("Step 3: Finding best matches...")
print()

matched_pdfs = set()
matched_folders = set()
matches = []  # [(pdf_info, folder_info, score)]

# For each PDF, find best matching folder
for pdf_artist, pdf_book, pdf_path in source_pdfs:
    best_score = 0
    best_folder = None
    
    for i, (folder_artist, folder_book, folder_path) in enumerate(processed_folders):
        if i in matched_folders:
            continue
        
        # Calculate similarity
        # Weight artist match heavily
        artist_match = similarity(pdf_artist, folder_artist)
        book_match = similarity(pdf_book, folder_book)
        
        # Combined score: 40% artist, 60% book name
        score = (artist_match * 0.4) + (book_match * 0.6)
        
        if score > best_score:
            best_score = score
            best_folder = i
    
    # Accept match if score is above threshold
    if best_score > 0.5:  # 50% similarity threshold (lowered from 60%)
        folder_info = processed_folders[best_folder]
        matches.append(((pdf_artist, pdf_book, pdf_path), folder_info, best_score))
        matched_pdfs.add((pdf_artist, pdf_book))
        matched_folders.add(best_folder)

print(f"✓ Found {len(matches)} matches (threshold: 50% similarity)")
print()

# Step 4: Identify unmatched
unmatched_pdfs = [(a, b, p) for a, b, p in source_pdfs if (a, b) not in matched_pdfs]
unmatched_folders = [processed_folders[i] for i in range(len(processed_folders)) if i not in matched_folders]

print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"Matched: {len(matches)}")
print(f"Unmatched PDFs: {len(unmatched_pdfs)}")
print(f"Unmatched Folders: {len(unmatched_folders)}")
print()

# Verification
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print(f"Source PDFs (excluding _Fake Books): {len(source_pdfs)}")
print(f"Processed Folders: {len(processed_folders)}")
print(f"Matched: {len(matches)}")
print(f"Unmatched PDFs: {len(unmatched_pdfs)}")
print(f"Unmatched Folders: {len(unmatched_folders)}")
print()
print(f"Expected unmatched PDFs: 20")
print(f"Actual unmatched PDFs: {len(unmatched_pdfs)}")
print(f"Match: {'✓ YES' if len(unmatched_pdfs) == 20 else '✗ NO'}")
print()

# Show unmatched PDFs
if unmatched_pdfs:
    print("=" * 80)
    print(f"UNMATCHED PDFs ({len(unmatched_pdfs)} books not yet processed)")
    print("=" * 80)
    by_artist = defaultdict(list)
    for artist, book, path in sorted(unmatched_pdfs):
        by_artist[artist].append(book)
    
    for artist in sorted(by_artist.keys()):
        print(f"\n{artist}:")
        for book in sorted(by_artist[artist]):
            print(f"  - {book}")

# Show unmatched folders (should be 0)
if unmatched_folders:
    print()
    print("=" * 80)
    print(f"UNMATCHED FOLDERS ({len(unmatched_folders)} folders without source PDF)")
    print("=" * 80)
    by_artist = defaultdict(list)
    for artist, book, path in sorted(unmatched_folders):
        by_artist[artist].append(book)
    
    for artist in sorted(by_artist.keys()):
        print(f"\n{artist}:")
        for book in sorted(by_artist[artist]):
            print(f"  - {book}")

# Show some sample matches for verification
print()
print("=" * 80)
print("SAMPLE MATCHES (first 10)")
print("=" * 80)
for i, ((pdf_artist, pdf_book, pdf_path), (folder_artist, folder_book, folder_path), score) in enumerate(matches[:10]):
    print(f"\n{i+1}. Score: {score:.2%}")
    print(f"   PDF:    {pdf_artist} / {pdf_book}")
    print(f"   Folder: {folder_artist} / {folder_book}")
