#!/usr/bin/env python3
"""
Extract first few pages of Billy Joel Anthology to check for TOC.
"""
import fitz  # PyMuPDF
from pathlib import Path

pdf_path = Path("SheetMusic/Billy Joel/Books/Billy Joel - Anthology.pdf")

print(f"Opening: {pdf_path}")
print()

doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}")
print()

# Extract first 10 pages
for page_num in range(min(10, len(doc))):
    page = doc[page_num]
    text = page.get_text()
    
    print(f"=" * 80)
    print(f"PAGE {page_num + 1}")
    print(f"=" * 80)
    print(text[:1000])  # First 1000 characters
    print()
    
    if page_num < 5:  # Show more detail for first 5 pages
        print(f"Full text length: {len(text)} characters")
        print()

doc.close()
