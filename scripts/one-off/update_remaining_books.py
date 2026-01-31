#!/usr/bin/env python3
"""Remove Steely Dan from the remaining books CSV."""

import csv

# Read the updated CSV
books = []
with open("ready_for_aws_processing_updated.csv", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Skip Steely Dan
        if "Steely Dan" not in row["Artist"]:
            books.append(row)

# Write updated CSV
with open("ready_for_aws_processing_remaining_19.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["PDF_Name", "PDF_Path", "Artist", "Book_Name"])
    writer.writeheader()
    writer.writerows(books)

print(f"✓ Updated CSV written: ready_for_aws_processing_remaining_19.csv")
print(f"  Remaining books: {len(books)}")
