#!/usr/bin/env python3
"""
Debug why Every Breath You Take is not being flagged.
"""

from pathlib import Path
from verify_pdf_splits import PDFVerifier, OllamaVisionClient, PDFRenderer

# Initialize
ollama = OllamaVisionClient()
renderer = PDFRenderer()
verifier = PDFVerifier(ollama, renderer)

pdf_path = Path("C:/Work/AWSMusic/ProcessedSongs/Various Artists/Best Of 80s Rock [pvg]/The Police - Every Breath You Take.pdf")

print(f"Testing: {pdf_path.name}")
print("=" * 80)

result = verifier.verify_pdf(pdf_path)

print(f"\nResult: {'PASSED' if result.passed else 'FLAGGED'}")
print(f"Page count: {result.page_count}")
print(f"Issues: {result.issues}")

# Check page 6 specifically (where Forever Young should start)
print(f"\n{'='*80}")
print("Checking page 6 (where Forever Young should start):")
print(f"{'='*80}")

if len(result.middle_pages_analysis) >= 5:  # Page 6 is index 4 in middle_pages
    page_6_analysis = result.middle_pages_analysis[4]
    print(f"Has title: {page_6_analysis.has_title}")
    print(f"Has new song: {page_6_analysis.has_new_song}")
    print(f"Raw response: {page_6_analysis.raw_response}")
    
    # Show the image path
    rendered_pages = renderer.render_all_pages(pdf_path)
    if len(rendered_pages) > 5:
        print(f"\nImage: file:///{rendered_pages[5].as_posix()}")
