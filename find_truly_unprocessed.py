#!/usr/bin/env python3
"""
Find PDFs that truly don't have a corresponding folder in ProcessedSongs.
After normalization, names should match exactly.
"""

from pathlib import Path
import csv

print("=" * 80)
print("FINDING TRULY UNPROCESSED PDFs")
print("=" * 80)
print()

# Get all PDF names (excluding _Fake Books)
sheet_music_path = Path("SheetMusic")
pdf_books = {}

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    # The book name is the PDF stem
    book_name = pdf_file.stem
    pdf_books[book_name] = pdf_file

print(f"Total PDFs in SheetMusic: {len(pdf_books)}")

# Get all folder names in ProcessedSongs
processed_songs_path = Path("ProcessedSongs")
processed_folders = {}

for folder in processed_songs_path.rglob("*"):
    if not folder.is_dir():
        continue
    if folder.name.startswith('.'):
        continue
    # Skip artist-level folders
    if folder.parent == processed_songs_path:
        continue
    
    # Check if folder has PDFs
    has_pdfs = any(folder.glob("*.pdf"))
    if has_pdfs:
        processed_folders[folder.name] = folder

print(f"Total book folders in ProcessedSongs: {len(processed_folders)}")
print()

# Find unprocessed: PDFs that don't have a matching folder name
unprocessed = []

for pdf_name, pdf_path in pdf_books.items():
    if pdf_name not in processed_folders:
        unprocessed.append((pdf_name, pdf_path))

print(f"Unprocessed PDFs: {len(unprocessed)}")
print()

# Display the unprocessed PDFs
print("=" * 80)
print("UNPROCESSED PDFs (No matching folder)")
print("=" * 80)
for i, (name, pdf_path) in enumerate(unprocessed, 1):
    rel_path = pdf_path.relative_to(sheet_music_path)
    print(f"{i}. {rel_path}")

print()

# Save to CSV
output_file = Path("truly_unprocessed_pdfs.csv")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_Name', 'PDF_Path', 'Artist'])
    
    for name, pdf_path in unprocessed:
        rel_path = pdf_path.relative_to(sheet_music_path)
        parts = rel_path.parts
        artist = parts[0] if len(parts) > 0 else ""
        
        writer.writerow([name, str(pdf_path), artist])

print(f"✓ Saved list to: {output_file}")
