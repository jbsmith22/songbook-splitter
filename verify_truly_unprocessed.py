#!/usr/bin/env python3
"""Verify which books in the CSV are truly unprocessed."""

import os
import csv
from pathlib import Path

# Read the updated CSV
books = []
with open("ready_for_aws_processing_updated.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    books = list(reader)

print(f"Checking {len(books)} books from CSV...\n")

truly_unprocessed = []
already_processed = []

for book in books:
    artist = book["Artist"]
    book_name = book["Book_Name"]
    
    # Check if folder exists in ProcessedSongs
    processed_path = Path(f"ProcessedSongs/{artist}/{book_name}")
    
    if processed_path.exists():
        print(f"✓ ALREADY PROCESSED: {book_name}")
        already_processed.append(book)
    else:
        print(f"✗ NOT PROCESSED: {book_name}")
        truly_unprocessed.append(book)

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Total in CSV: {len(books)}")
print(f"Already processed: {len(already_processed)}")
print(f"Truly unprocessed: {len(truly_unprocessed)}")

if truly_unprocessed:
    print(f"\nTruly unprocessed books:")
    for book in truly_unprocessed:
        print(f"  - {book['Book_Name']} ({book['Artist']})")
    
    # Write truly unprocessed to new CSV
    with open("truly_unprocessed_books.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["PDF_Name", "PDF_Path", "Artist", "Book_Name"])
        writer.writeheader()
        writer.writerows(truly_unprocessed)
    
    print(f"\n✓ Wrote truly unprocessed books to: truly_unprocessed_books.csv")
