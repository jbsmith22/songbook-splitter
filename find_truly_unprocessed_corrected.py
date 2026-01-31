#!/usr/bin/env python3
"""
Find PDFs that truly don't have a corresponding folder in ProcessedSongs.
Takes into account that PDFs have artist prefix but folders don't.

PDF structure: SheetMusic\{Artist}\Books\{Artist} - {BookName}.pdf
Folder structure: ProcessedSongs\{Artist}\{BookName}\
"""

from pathlib import Path
import csv

print("=" * 80)
print("FINDING TRULY UNPROCESSED PDFs (CORRECTED)")
print("=" * 80)
print()

# Get all PDF names (excluding _Fake Books)
sheet_music_path = Path("SheetMusic")
pdf_books = []

for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if "_Fake Books" in str(pdf_file):
        continue
    
    # Get artist from folder structure
    rel_path = pdf_file.relative_to(sheet_music_path)
    parts = rel_path.parts
    
    if len(parts) < 3:  # Should be Artist\Books\filename.pdf
        continue
    
    artist = parts[0]
    pdf_stem = pdf_file.stem
    
    # Try to extract book name by removing artist prefix
    # Format is usually: "{Artist} - {BookName}"
    if " - " in pdf_stem:
        # Remove artist prefix
        book_name = pdf_stem.split(" - ", 1)[1]
    else:
        # No artist prefix, use full stem
        book_name = pdf_stem
    
    pdf_books.append({
        'pdf_path': pdf_file,
        'artist': artist,
        'pdf_stem': pdf_stem,
        'book_name': book_name
    })

print(f"Total PDFs in SheetMusic: {len(pdf_books)}")

# Check which ones have corresponding folders
processed_songs_path = Path("ProcessedSongs")
unprocessed = []
processed = []

for pdf_info in pdf_books:
    artist = pdf_info['artist']
    book_name = pdf_info['book_name']
    
    # Check if folder exists: ProcessedSongs\{Artist}\{BookName}\
    expected_folder = processed_songs_path / artist / book_name
    
    if expected_folder.exists() and expected_folder.is_dir():
        # Check if it has PDFs
        has_pdfs = any(expected_folder.glob("*.pdf"))
        if has_pdfs:
            processed.append(pdf_info)
        else:
            unprocessed.append(pdf_info)
    else:
        unprocessed.append(pdf_info)

print(f"Processed PDFs (have matching folder): {len(processed)}")
print(f"Unprocessed PDFs (no matching folder): {len(unprocessed)}")
print()

# Display the unprocessed PDFs
print("=" * 80)
print("UNPROCESSED PDFs (No matching folder)")
print("=" * 80)
for i, pdf_info in enumerate(unprocessed, 1):
    rel_path = pdf_info['pdf_path'].relative_to(sheet_music_path)
    expected_folder = processed_songs_path / pdf_info['artist'] / pdf_info['book_name']
    print(f"{i}. {rel_path}")
    print(f"   Expected folder: {expected_folder}")
    print()

# Save to CSV
output_file = Path("truly_unprocessed_pdfs_corrected.csv")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_Path', 'Artist', 'PDF_Stem', 'Book_Name', 'Expected_Folder'])
    
    for pdf_info in unprocessed:
        expected_folder = processed_songs_path / pdf_info['artist'] / pdf_info['book_name']
        writer.writerow([
            str(pdf_info['pdf_path']),
            pdf_info['artist'],
            pdf_info['pdf_stem'],
            pdf_info['book_name'],
            str(expected_folder)
        ])

print(f"✓ Saved list to: {output_file}")
