#!/usr/bin/env python3
"""
Check for remaining unnormalized files and folders.
"""

import re
from pathlib import Path

def has_special_chars(name):
    """Check if name has characters that should be normalized."""
    # Check for brackets, parentheses, ampersands, apostrophes
    if any(char in name for char in ['[', ']', '(', ')', '&', "'"]):
        return True
    
    # Check for lowercase 'and' that should be 'And'
    if ' and ' in name:
        return True
    
    # Check for lowercase 'of' that should be 'Of'
    if ' of ' in name:
        return True
    
    # Check for lowercase 'the' that should be 'The'
    if ' the ' in name:
        return True
    
    # Check for lowercase 'in' that should be 'In'
    if ' in ' in name:
        return True
    
    # Check for lowercase 'for' that should be 'For'
    if ' for ' in name:
        return True
    
    return False

print("=" * 80)
print("CHECKING FOR REMAINING UNNORMALIZED FILES")
print("=" * 80)
print()

# Check PDFs in SheetMusic
sheet_music_path = Path("SheetMusic")
unnormalized_pdfs = []

print("Scanning SheetMusic folder...")
for pdf_file in sheet_music_path.rglob("*.pdf"):
    if pdf_file.name.startswith('.'):
        continue
    if has_special_chars(pdf_file.stem):
        unnormalized_pdfs.append(pdf_file)

print(f"Found {len(unnormalized_pdfs)} unnormalized PDFs")
print()

# Check folders in ProcessedSongs
processed_songs_path = Path("ProcessedSongs")
unnormalized_folders = []

print("Scanning ProcessedSongs folder...")
for folder in processed_songs_path.rglob("*"):
    if not folder.is_dir():
        continue
    if folder.name.startswith('.'):
        continue
    # Skip artist-level folders (direct children of ProcessedSongs)
    if folder.parent == processed_songs_path:
        continue
    if has_special_chars(folder.name):
        unnormalized_folders.append(folder)

print(f"Found {len(unnormalized_folders)} unnormalized folders")
print()

# Show examples
if unnormalized_pdfs:
    print("=" * 80)
    print("UNNORMALIZED PDFs (first 20)")
    print("=" * 80)
    for i, pdf in enumerate(unnormalized_pdfs[:20], 1):
        print(f"{i}. {pdf.relative_to(sheet_music_path)}")
    if len(unnormalized_pdfs) > 20:
        print(f"... and {len(unnormalized_pdfs) - 20} more")
    print()

if unnormalized_folders:
    print("=" * 80)
    print("UNNORMALIZED FOLDERS (first 20)")
    print("=" * 80)
    for i, folder in enumerate(unnormalized_folders[:20], 1):
        print(f"{i}. {folder.relative_to(processed_songs_path)}")
    if len(unnormalized_folders) > 20:
        print(f"... and {len(unnormalized_folders) - 20} more")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total unnormalized PDFs: {len(unnormalized_pdfs)}")
print(f"Total unnormalized folders: {len(unnormalized_folders)}")
print(f"Total unnormalized items: {len(unnormalized_pdfs) + len(unnormalized_folders)}")
print()

if len(unnormalized_pdfs) + len(unnormalized_folders) == 0:
    print("✓ ALL FILES AND FOLDERS ARE NORMALIZED!")
else:
    print("Run normalization again to fix remaining items")
