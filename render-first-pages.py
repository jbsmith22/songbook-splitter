#!/usr/bin/env python3
"""
Render first few pages of Billy Joel Anthology as images to check for TOC.
"""
import fitz  # PyMuPDF
from pathlib import Path

pdf_path = Path("SheetMusic/Billy Joel/Books/Billy Joel - Anthology.pdf")
output_dir = Path("temp_anthology_pages")
output_dir.mkdir(exist_ok=True)

print(f"Opening: {pdf_path}")
print(f"Rendering first 10 pages to: {output_dir}")
print()

doc = fitz.open(pdf_path)

for page_num in range(min(10, len(doc))):
    page = doc[page_num]
    
    # Render at 150 DPI
    mat = fitz.Matrix(150/72, 150/72)
    pix = page.get_pixmap(matrix=mat)
    
    output_file = output_dir / f"page_{page_num + 1:03d}.png"
    pix.save(output_file)
    
    print(f"Rendered page {page_num + 1} -> {output_file}")

doc.close()

print()
print(f"Images saved to: {output_dir}")
print("Please check the images to see if there's a table of contents.")
