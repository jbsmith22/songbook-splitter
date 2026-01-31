#!/usr/bin/env python3
"""
Analyze page gaps using cached TOC files.
Shows which songs from TOC are missing in ProcessedSongs folders.
"""

import json
from pathlib import Path
from collections import defaultdict
import PyPDF2

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
TOC_CACHE_DIR = Path("toc_cache")

def get_pdf_page_count(pdf_path):
    """Get the number of pages in a PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except:
        return 0

def find_book_directory(artist, book_name):
    """Find the directory for a book."""
    artist_dir = PROCESSED_SONGS_PATH / artist
    if not artist_dir.exists():
        return None
    
    # Try exact match first
    book_dir = artist_dir / book_name
    if book_dir.exists():
        return book_dir
    
    # Try without "Various Artists - " prefix
    if book_name.startswith("Various Artists - "):
        book_name_short = book_name.replace("Various Artists - ", "")
        book_dir = artist_dir / book_name_short
        if book_dir.exists():
            return book_dir
    
    # Try fuzzy match
    book_name_lower = book_name.lower()
    for dir in artist_dir.iterdir():
        if dir.is_dir():
            dir_name_lower = dir.name.lower()
            if book_name_lower in dir_name_lower or dir_name_lower in book_name_lower:
                return dir
    
    return None

def analyze_book(toc_cache_file):
    """Analyze a single book from cached TOC."""
    with open(toc_cache_file, 'r') as f:
        data = json.load(f)
    
    toc = data.get('toc')
    output = data.get('output')
    
    if not output or 'output_files' not in output or not output['output_files']:
        return None
    
    # Get book info from output
    first_file = output['output_files'][0]
    artist = first_file.get('artist', 'Unknown')
    output_uri = first_file.get('output_uri', '')
    
    # Extract book name from S3 URI
    if output_uri:
        parts = output_uri.replace('s3://jsmith-output/', '').split('/')
        if len(parts) >= 2:
            book_name = parts[1]
        else:
            return None
    else:
        return None
    
    # Find local directory
    book_dir = find_book_directory(artist, book_name)
    if not book_dir:
        return None
    
    # Get expected songs from TOC
    expected_songs = []
    if toc and 'entries' in toc:
        for entry in toc['entries']:
            expected_songs.append({
                'title': entry.get('song_title', 'Unknown'),
                'page': entry.get('page_number', 0)
            })
    
    # Get actual PDFs
    actual_songs = []
    total_pages = 0
    for pdf_file in sorted(book_dir.glob("*.pdf")):
        if pdf_file.suffix == '.original':
            continue
        
        has_backup = pdf_file.with_suffix('.pdf.original').exists()
        if has_backup:
            page_count = get_pdf_page_count(pdf_file.with_suffix('.pdf.original'))
        else:
            page_count = get_pdf_page_count(pdf_file)
        
        total_pages += page_count
        actual_songs.append({
            'filename': pdf_file.name,
            'page_count': page_count
        })
    
    # Match songs
    matched = 0
    missing = []
    extra = []
    
    for expected in expected_songs:
        found = False
        for actual in actual_songs:
            if expected['title'].lower() in actual['filename'].lower():
                matched += 1
                found = True
                break
        if not found:
            missing.append(expected)
    
    for actual in actual_songs:
        found = False
        for expected in expected_songs:
            if expected['title'].lower() in actual['filename'].lower():
                found = True
                break
        if not found:
            extra.append(actual['filename'])
    
    coverage = (matched / len(expected_songs) * 100) if expected_songs else 0
    
    return {
        'artist': artist,
        'book_name': book_name,
        'book_dir': str(book_dir),
        'expected_songs': len(expected_songs),
        'actual_songs': len(actual_songs),
        'matched': matched,
        'missing': missing,
        'extra': extra,
        'total_pages': total_pages,
        'coverage_percent': coverage
    }

if __name__ == "__main__":
    from datetime import datetime
    
    print("Analyzing page gaps from cached TOC files...")
    print("=" * 80)
    
    if not TOC_CACHE_DIR.exists():
        print("\nError: TOC cache directory not found.")
        print("Run 'py download_all_tocs.py' first to download TOC files from S3.")
        exit(1)
    
    toc_files = list(TOC_CACHE_DIR.glob("*.json"))
    print(f"\nFound {len(toc_files)} cached TOC files")
    
    print("\nAnalyzing books...")
    analyses = []
    found_locally = 0
    not_found = 0
    
    for i, toc_file in enumerate(toc_files, 1):
        if i % 50 == 0:
            print(f"  Progress: {i}/{len(toc_files)} ({found_locally} found, {not_found} not found)")
        
        analysis = analyze_book(toc_file)
        if analysis:
            analyses.append(analysis)
            found_locally += 1
        else:
            not_found += 1
    
    print(f"\n✓ Analyzed {found_locally} books")
    print(f"✗ {not_found} books not found locally")
    
    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_toc_files': len(toc_files),
            'books_found_locally': found_locally,
            'books_not_found': not_found,
            'books_with_missing_songs': sum(1 for a in analyses if a['missing']),
            'books_with_extra_songs': sum(1 for a in analyses if a['extra']),
            'total_missing_songs': sum(len(a['missing']) for a in analyses),
            'total_extra_songs': sum(len(a['extra']) for a in analyses)
        },
        'books': sorted(analyses, key=lambda x: x['coverage_percent'])
    }
    
    output_file = Path("page_gap_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Books analyzed: {found_locally}")
    print(f"Books with missing songs: {report['summary']['books_with_missing_songs']}")
    print(f"Books with extra songs: {report['summary']['books_with_extra_songs']}")
    print(f"Total missing songs: {report['summary']['total_missing_songs']}")
    print(f"Total extra songs: {report['summary']['total_extra_songs']}")
    
    # Show worst coverage
    print("\nBooks with lowest coverage (top 10):")
    for book in report['books'][:10]:
        if book['coverage_percent'] < 100:
            print(f"  {book['coverage_percent']:.0f}% - {book['artist']} / {book['book_name']}")
            if book['missing']:
                missing_titles = [m['title'] for m in book['missing'][:3]]
                print(f"         Missing: {', '.join(missing_titles)}")
                if len(book['missing']) > 3:
                    print(f"         ... and {len(book['missing']) - 3} more")
