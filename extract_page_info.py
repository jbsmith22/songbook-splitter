#!/usr/bin/env python3
"""
Extract page information from PDFs to build complete page mapping.
Shows which pages belong to which songs and identifies gaps.
"""

import PyPDF2
from pathlib import Path
import json
from collections import defaultdict

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def get_pdf_page_count(pdf_path):
    """Get the number of pages in a PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except:
        return 0

def extract_page_ranges_from_splits(feedback_file):
    """Extract page ranges from split instructions."""
    if not Path(feedback_file).exists():
        return {}
    
    with open(feedback_file, 'r') as f:
        feedback = json.load(f)
    
    return feedback.get('splitInstructions', {})

def parse_page_range(page_str):
    """Parse page range string like '1-3' or '4' into (start, end)."""
    if '-' in page_str:
        start, end = page_str.split('-')
        return (int(start), int(end))
    else:
        page = int(page_str)
        return (page, page)

def build_page_mapping_for_book(book_path, split_instructions=None):
    """Build complete page mapping for a book showing all songs and gaps."""
    
    mapping = {
        'book_path': str(book_path),
        'total_pages': 0,
        'songs': [],
        'gaps': [],
        'coverage': 0.0
    }
    
    # Get all PDFs in the book
    pdfs = []
    for pdf_file in book_path.glob("*.pdf"):
        if pdf_file.suffix == '.original':
            continue
        
        # Check if this was split (has .original backup)
        was_split = pdf_file.with_suffix('.pdf.original').exists()
        
        if was_split:
            # Use the original for page counting
            original_path = pdf_file.with_suffix('.pdf.original')
            page_count = get_pdf_page_count(original_path)
        else:
            page_count = get_pdf_page_count(pdf_file)
        
        pdfs.append({
            'filename': pdf_file.name,
            'path': str(pdf_file),
            'page_count': page_count,
            'was_split': was_split,
            'page_range': None  # Will be filled if we have split info
        })
    
    # If we have split instructions, add page ranges
    if split_instructions:
        for pdf in pdfs:
            if pdf['was_split']:
                # Find split info for this PDF
                # This is approximate - we'd need to match back to the original
                pass
    
    # Sort by filename to get sequential order
    pdfs.sort(key=lambda x: x['filename'])
    
    # Calculate total pages and identify gaps
    current_page = 1
    covered_pages = set()
    
    for pdf in pdfs:
        if pdf['page_count'] > 0:
            song_entry = {
                'filename': pdf['filename'],
                'page_count': pdf['page_count'],
                'estimated_range': f"{current_page}-{current_page + pdf['page_count'] - 1}",
                'was_split': pdf['was_split']
            }
            mapping['songs'].append(song_entry)
            
            for p in range(current_page, current_page + pdf['page_count']):
                covered_pages.add(p)
            
            current_page += pdf['page_count']
    
    mapping['total_pages'] = current_page - 1 if pdfs else 0
    
    # Identify gaps (this is simplified - real gaps would need TOC data)
    if mapping['total_pages'] > 0:
        all_pages = set(range(1, mapping['total_pages'] + 1))
        gap_pages = all_pages - covered_pages
        
        if gap_pages:
            # Group consecutive gaps
            sorted_gaps = sorted(gap_pages)
            gap_ranges = []
            start = sorted_gaps[0]
            end = sorted_gaps[0]
            
            for page in sorted_gaps[1:]:
                if page == end + 1:
                    end = page
                else:
                    gap_ranges.append(f"{start}-{end}" if start != end else str(start))
                    start = page
                    end = page
            
            gap_ranges.append(f"{start}-{end}" if start != end else str(start))
            mapping['gaps'] = gap_ranges
        
        mapping['coverage'] = len(covered_pages) / mapping['total_pages'] * 100
    
    return mapping

def scan_all_books_with_pages():
    """Scan all books and extract page information."""
    
    books_with_pages = {}
    
    if not PROCESSED_SONGS_PATH.exists():
        return books_with_pages
    
    for artist_dir in PROCESSED_SONGS_PATH.iterdir():
        if not artist_dir.is_dir():
            continue
        
        artist = artist_dir.name
        
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            book = book_dir.name
            book_key = f"{artist}/{book}"
            
            print(f"Processing: {book_key}")
            
            page_mapping = build_page_mapping_for_book(book_dir)
            books_with_pages[book_key] = page_mapping
    
    return books_with_pages

if __name__ == "__main__":
    print("Scanning books and extracting page information...")
    print("This may take a while as we need to open each PDF...\n")
    
    books = scan_all_books_with_pages()
    
    output_file = Path("books_page_mapping.json")
    with open(output_file, 'w') as f:
        json.dump(books, f, indent=2)
    
    print(f"\n✓ Page mapping saved to: {output_file}")
    
    # Print summary
    total_books = len(books)
    books_with_gaps = sum(1 for b in books.values() if b['gaps'])
    total_pages = sum(b['total_pages'] for b in books.values())
    
    print(f"\nSummary:")
    print(f"  Total books: {total_books}")
    print(f"  Total pages: {total_pages}")
    print(f"  Books with gaps: {books_with_gaps}")
    
    if books_with_gaps > 0:
        print(f"\nBooks with gaps:")
        for book_key, data in books.items():
            if data['gaps']:
                print(f"  {book_key}: {len(data['gaps'])} gap(s) - {', '.join(data['gaps'])}")
