#!/usr/bin/env python3
"""
Find the 20 PDFs that haven't been processed yet.
"""

from pathlib import Path
import csv

print("=" * 80)
print("FINDING UNPROCESSED PDFs")
print("=" * 80)
print()

# Get all PDFs (excluding _Fake Books)
sheet_music_path = Path("SheetMusic")
all_pdfs = {}

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    # Store with relative path as key
    rel_path = pdf_file.relative_to(sheet_music_path)
    all_pdfs[str(rel_path)] = pdf_file

print(f"Total PDFs in SheetMusic: {len(all_pdfs)}")

# Get all folders in ProcessedSongs
processed_songs_path = Path("ProcessedSongs")
processed_books = set()

for folder in processed_songs_path.rglob("*"):
    if not folder.is_dir():
        continue
    if folder.name.startswith('.'):
        continue
    # Skip artist-level folders
    if folder.parent == processed_songs_path:
        continue
    
    # Store folder name
    processed_books.add(folder.name)

print(f"Total processed books: {len(processed_books)}")
print()

# Find unprocessed PDFs by checking if folder exists
unprocessed = []

for pdf_rel_path, pdf_path in all_pdfs.items():
    # Get the book name from the PDF
    book_name = pdf_path.stem
    
    # Check if a folder with this name exists
    found = False
    for processed_name in processed_books:
        if processed_name.lower() == book_name.lower():
            found = True
            break
    
    if not found:
        unprocessed.append(pdf_path)

print(f"Unprocessed PDFs: {len(unprocessed)}")
print()

# Display the unprocessed PDFs
print("=" * 80)
print("UNPROCESSED PDFs")
print("=" * 80)
for i, pdf in enumerate(unprocessed, 1):
    rel_path = pdf.relative_to(sheet_music_path)
    print(f"{i}. {rel_path}")

print()

# Save to CSV for processing
output_file = Path("unprocessed_pdfs.csv")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_Path', 'Artist', 'Book_Name'])
    
    for pdf in unprocessed:
        rel_path = pdf.relative_to(sheet_music_path)
        # Extract artist from path
        parts = rel_path.parts
        artist = parts[0] if len(parts) > 0 else ""
        book_name = pdf.stem
        
        writer.writerow([str(pdf), artist, book_name])

print(f"✓ Saved list to: {output_file}")
print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Review unprocessed_pdfs.csv")
print("2. Upload these PDFs to S3")
print("3. Run them through the AWS Step Functions pipeline")
