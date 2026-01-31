#!/usr/bin/env python3
"""
Test the 5 known error PDFs that SHOULD be flagged.
"""

from pathlib import Path
from verify_pdf_splits import PDFVerifier, OllamaVisionClient, PDFRenderer

# Initialize
ollama = OllamaVisionClient()
renderer = PDFRenderer()
verifier = PDFVerifier(ollama, renderer)

# The 5 PDFs that SHOULD be flagged
known_errors = [
    "ProcessedSongs/Various Artists/Best Of 80s Rock [pvg]/The Police - Every Breath You Take.pdf",
    "ProcessedSongs/_broadway Shows/Various Artists - The Ultimate Broadway Fakebook/Oscar Hammerstein - Climb Ev'ry Mountain.pdf",
    "ProcessedSongs/Billy Joel/Fantasies & Delusions/Billy Joel - Opus 8 Suite For Piano (star-crossed) I. Innamorato.pdf",
    "ProcessedSongs/_broadway Shows/Various Artists - Lion King [score]/The Lion King - Under The Stars.pdf",
    "ProcessedSongs/Bob Dylan/Anthology 2/Bob Dylan - It's Alright, Ma (i'm Only Bleeding).pdf",
]

print("Testing the 5 known error PDFs...")
print("=" * 80)

for i, pdf_rel_path in enumerate(known_errors, 1):
    pdf_path = Path("C:/Work/AWSMusic") / pdf_rel_path
    
    if not pdf_path.exists():
        print(f"\n{i}. NOT FOUND: {pdf_path.name}")
        continue
    
    print(f"\n{i}. Testing: {pdf_path.name}")
    print(f"   Path: {pdf_rel_path}")
    
    result = verifier.verify_pdf(pdf_path)
    
    if result.passed:
        print(f"   ❌ MISSED - Should have been flagged but PASSED")
    else:
        print(f"   ✅ CAUGHT - Correctly flagged")
        print(f"   Issues: {result.issues}")
    
    print(f"   Pages: {result.page_count}")

print("\n" + "=" * 80)
print("Testing complete!")
