#!/usr/bin/env python3
"""Update ready_for_aws_processing.csv with actual normalized file paths."""

import os
import csv
from pathlib import Path

# Base directory
base_dir = Path(r"c:\Work\AWSMusic\SheetMusic")

# Read the old CSV
old_books = []
with open("ready_for_aws_processing.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        old_books.append(row)

# Find actual files and update paths
updated_books = []
not_found = []

for book in old_books:
    artist = book["Artist"]
    old_book_name = book["Book_Name"]
    
    # Build search path - try both direct Books and Others\Books
    search_dirs = [
        base_dir / artist / "Books",
        base_dir / artist / "Others" / "Books"
    ]
    
    artist_dir = None
    for search_dir in search_dirs:
        if search_dir.exists():
            artist_dir = search_dir
            break
    
    if artist_dir is None:
        print(f"WARNING: Artist directory not found for: {artist}")
        not_found.append(book)
        continue
    
    # Try to find the file by searching for similar names
    found = False
    for pdf_file in artist_dir.glob("*.pdf"):
        # Check if this might be the file we're looking for
        # Remove "Various Artists - " prefix for comparison
        file_stem = pdf_file.stem
        if file_stem.startswith("Various Artists - "):
            compare_name = file_stem
        else:
            compare_name = file_stem
        
        # Simple match: if the old book name (without special chars) is in the filename
        old_normalized = old_book_name.replace("[", "_").replace("]", "_").replace("(", "_").replace(")", "_")
        
        if old_normalized.lower() in file_stem.lower() or file_stem.lower() in old_normalized.lower():
            # Found a match
            updated_books.append({
                "PDF_Name": file_stem,
                "PDF_Path": str(pdf_file),
                "Artist": artist,
                "Book_Name": file_stem
            })
            print(f"✓ Found: {file_stem}")
            found = True
            break
    
    if not found:
        print(f"✗ NOT FOUND: {old_book_name} in {artist_dir}")
        not_found.append(book)

# Write updated CSV
with open("ready_for_aws_processing_updated.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["PDF_Name", "PDF_Path", "Artist", "Book_Name"])
    writer.writeheader()
    writer.writerows(updated_books)

print(f"\n✓ Updated CSV written: ready_for_aws_processing_updated.csv")
print(f"  Found: {len(updated_books)}")
print(f"  Not found: {len(not_found)}")

if not_found:
    print("\nNot found:")
    for book in not_found:
        print(f"  - {book['Book_Name']}")
