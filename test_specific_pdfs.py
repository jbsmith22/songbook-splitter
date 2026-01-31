#!/usr/bin/env python3
"""
Test specific PDFs to understand what the vision model is detecting.
"""

from pathlib import Path
from verify_pdf_splits import PDFVerifier, OllamaVisionClient, PDFRenderer

# Initialize
ollama = OllamaVisionClient()
renderer = PDFRenderer()
verifier = PDFVerifier(ollama, renderer)

# Test cases from user feedback
test_cases = [
    # Should PASS - these are correct
    "ProcessedSongs/_movie And Tv/Various Artists - Tv Fakebook 2nd Ed/Tim Truman - Melrose Place Theme.pdf",
    "ProcessedSongs/Various Artists/557 Standards (sheet Music - Piano)(2)/(s.rollins) - Allegin.pdf",
    "ProcessedSongs/Beatles/Fake Songbook (guitar)/Beatles - Help!.pdf",
    
    # Should FLAG - these have errors
    "ProcessedSongs/Various Artists/Best Of 80s Rock [pvg]/The Police - Every Breath You Take.pdf",
    "ProcessedSongs/_broadway Shows/Various Artists - The Ultimate Broadway Fakebook/Oscar Hammerstein - Climb Ev'ry Mountain.pdf",
]

for pdf_rel_path in test_cases:
    pdf_path = Path("C:/Work/AWSMusic") / pdf_rel_path
    
    if not pdf_path.exists():
        print(f"\n{'='*80}")
        print(f"SKIPPING (not found): {pdf_path.name}")
        continue
    
    print(f"\n{'='*80}")
    print(f"Testing: {pdf_path.name}")
    print(f"Path: {pdf_rel_path}")
    print(f"{'='*80}")
    
    result = verifier.verify_pdf(pdf_path)
    
    print(f"\nResult: {'PASSED' if result.passed else 'FLAGGED'}")
    print(f"Page count: {result.page_count}")
    
    if result.issues:
        print(f"\nIssues:")
        for issue in result.issues:
            print(f"  - {issue}")
    
    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    # Show first page analysis
    if result.first_page_analysis:
        print(f"\nFirst page analysis:")
        print(f"  Has title: {result.first_page_analysis.has_title}")
        print(f"  Title text: {result.first_page_analysis.title_text}")
        print(f"  Is first page: {result.first_page_analysis.is_first_page}")
        print(f"  Is continuation: {result.first_page_analysis.is_continuation}")
        print(f"  Raw response: {result.first_page_analysis.raw_response[:200]}...")
    
    # Show middle page issues
    if result.middle_pages_analysis:
        for i, analysis in enumerate(result.middle_pages_analysis):
            if analysis.has_title or analysis.has_new_song:
                print(f"\nPage {i+2} analysis:")
                print(f"  Has title: {analysis.has_title}")
                print(f"  Has new song: {analysis.has_new_song}")
                print(f"  Raw response: {analysis.raw_response[:200]}...")
    
    # Show last page analysis
    if result.last_page_analysis:
        if result.last_page_analysis.has_title or result.last_page_analysis.has_new_song:
            print(f"\nLast page analysis:")
            print(f"  Has title: {result.last_page_analysis.has_title}")
            print(f"  Has new song: {result.last_page_analysis.has_new_song}")
            print(f"  Raw response: {result.last_page_analysis.raw_response[:200]}...")

print(f"\n{'='*80}")
print("Testing complete!")
