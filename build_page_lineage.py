#!/usr/bin/env python3
"""
Build complete page lineage showing TOC vs actual page ranges.
Identifies gaps and mismatches in page sequences.
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
    
    book_dir = artist_dir / book_name
    if book_dir.exists():
        return book_dir
    
    if book_name.startswith("Various Artists - "):
        book_name_short = book_name.replace("Various Artists - ", "")
        book_dir = artist_dir / book_name_short
        if book_dir.exists():
            return book_dir
    
    book_name_lower = book_name.lower()
    for dir in artist_dir.iterdir():
        if dir.is_dir():
            dir_name_lower = dir.name.lower()
            if book_name_lower in dir_name_lower or dir_name_lower in book_name_lower:
                return dir
    
    return None

def analyze_book_pages(toc_cache_file):
    """Analyze page sequence for a book."""
    with open(toc_cache_file, 'r') as f:
        data = json.load(f)
    
    toc = data.get('toc', {})
    output = data.get('output', {})
    
    if not output or 'output_files' not in output or not output['output_files']:
        return None
    
    # Get book info
    first_file = output['output_files'][0]
    artist = first_file.get('artist', 'Unknown')
    output_uri = first_file.get('output_uri', '')
    
    if output_uri:
        parts = output_uri.replace('s3://jsmith-output/', '').split('/')
        if len(parts) >= 2:
            book_name = parts[1]
        else:
            return None
    else:
        return None
    
    book_dir = find_book_directory(artist, book_name)
    if not book_dir:
        return None
    
    # Build TOC page map
    toc_entries = []
    if toc and 'entries' in toc:
        for entry in toc['entries']:
            toc_entries.append({
                'title': entry.get('song_title', 'Unknown'),
                'toc_page': entry.get('page_number', 0)
            })
    
    # Build output page map (from AWS extraction)
    output_songs = []
    for out_file in output['output_files']:
        page_range = out_file.get('page_range', [0, 0])
        output_songs.append({
            'title': out_file.get('song_title', 'Unknown'),
            'extracted_pages': f"{page_range[0]}-{page_range[1]-1}" if page_range[1] > page_range[0] else str(page_range[0]),
            'page_start': page_range[0],
            'page_end': page_range[1] - 1,
            'page_count': page_range[1] - page_range[0]
        })
    
    # Get actual local PDFs
    local_songs = []
    for pdf_file in sorted(book_dir.glob("*.pdf")):
        if pdf_file.suffix == '.original':
            continue
        
        has_backup = pdf_file.with_suffix('.pdf.original').exists()
        if has_backup:
            page_count = get_pdf_page_count(pdf_file.with_suffix('.pdf.original'))
        else:
            page_count = get_pdf_page_count(pdf_file)
        
        local_songs.append({
            'filename': pdf_file.name,
            'page_count': page_count
        })
    
    # Calculate total pages and identify gaps
    total_pages = 0
    if output_songs:
        total_pages = max(s['page_end'] for s in output_songs) + 1
    
    # Identify gaps in page sequence (excluding gaps at the beginning)
    covered_pages = set()
    for song in output_songs:
        for p in range(song['page_start'], song['page_end'] + 1):
            covered_pages.add(p)
    
    gaps = []
    if total_pages > 0:
        all_pages = set(range(total_pages))
        gap_pages = sorted(all_pages - covered_pages)
        
        if gap_pages:
            # Find where actual content starts (first covered page)
            first_content_page = min(covered_pages) if covered_pages else 0
            
            # Filter out gaps at the beginning (TOC/title pages)
            gap_pages = [p for p in gap_pages if p >= first_content_page]
            
            if gap_pages:
                # Group consecutive gaps
                start = gap_pages[0]
                end = gap_pages[0]
                
                for page in gap_pages[1:]:
                    if page == end + 1:
                        end = page
                    else:
                        gaps.append(f"{start}-{end}" if start != end else str(start))
                        start = page
                        end = page
                
                gaps.append(f"{start}-{end}" if start != end else str(start))
    
    # Check for page count mismatches
    mismatches = []
    for i, out_song in enumerate(output_songs):
        # Try to find matching local PDF
        for local in local_songs:
            if out_song['title'].lower() in local['filename'].lower():
                if out_song['page_count'] != local['page_count']:
                    mismatches.append({
                        'song': out_song['title'],
                        'expected_pages': out_song['page_count'],
                        'actual_pages': local['page_count']
                    })
                break
    
    return {
        'artist': artist,
        'book_name': book_name,
        'book_dir': str(book_dir),
        'has_toc': len(toc_entries) > 0,
        'toc_entries': toc_entries,
        'extracted_songs': output_songs,
        'local_songs': local_songs,
        'total_pages': total_pages,
        'gaps': gaps,
        'mismatches': mismatches,
        'status': 'has_gaps' if gaps else 'complete'
    }

if __name__ == "__main__":
    from datetime import datetime
    
    print("Building complete page lineage...")
    print("=" * 80)
    
    # Scan ProcessedSongs as source of truth
    print("Scanning ProcessedSongs directory...")
    actual_books = set()
    for artist_dir in PROCESSED_SONGS_PATH.iterdir():
        if not artist_dir.is_dir():
            continue
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            # Check if it has PDF files
            pdf_files = list(book_dir.glob("*.pdf"))
            if pdf_files:
                actual_books.add((artist_dir.name, book_dir.name))
    
    print(f"✓ Found {len(actual_books)} books in ProcessedSongs")
    print()
    
    if not TOC_CACHE_DIR.exists():
        print("\nError: TOC cache directory not found.")
        print("Run 'py download_all_tocs.py' first.")
        exit(1)
    
    toc_files = list(TOC_CACHE_DIR.glob("*.json"))
    print(f"Processing {len(toc_files)} TOC cache files...")
    
    lineages = []
    processed = 0
    skipped_not_in_processed = 0
    
    for i, toc_file in enumerate(toc_files, 1):
        if i % 100 == 0:
            print(f"  Progress: {i}/{len(toc_files)}")
        
        lineage = analyze_book_pages(toc_file)
        if lineage:
            # Only include if in ProcessedSongs
            key = (lineage['artist'], lineage['book_name'])
            if key in actual_books:
                lineages.append(lineage)
                processed += 1
            else:
                skipped_not_in_processed += 1
    
    print(f"\n✓ Processed {processed} books from ProcessedSongs")
    print(f"✗ Skipped {skipped_not_in_processed} books not in ProcessedSongs")
    
    # Deduplicate books - keep the one with most songs
    print("Deduplicating books...")
    from collections import defaultdict
    book_map = defaultdict(list)
    for lineage in lineages:
        key = (lineage['artist'], lineage['book_name'])
        book_map[key].append(lineage)
    
    deduplicated = []
    for key, entries in book_map.items():
        # Keep the entry with the most songs
        best = max(entries, key=lambda x: len(x['extracted_songs']))
        deduplicated.append(best)
    
    if len(lineages) != len(deduplicated):
        print(f"✓ Deduplicated from {len(lineages)} to {len(deduplicated)} unique books")
    lineages = deduplicated
    
    # Generate report
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_books': len(lineages),
            'books_with_toc': sum(1 for l in lineages if l['has_toc']),
            'books_without_toc': sum(1 for l in lineages if not l['has_toc']),
            'books_with_gaps': sum(1 for l in lineages if l['gaps']),
            'books_with_mismatches': sum(1 for l in lineages if l['mismatches']),
            'total_pages': sum(l['total_pages'] for l in lineages),
            'total_songs': sum(len(l['extracted_songs']) for l in lineages)
        },
        'books': sorted(lineages, key=lambda x: (len(x['gaps']) > 0, x['artist'], x['book_name']))
    }
    
    output_file = Path("complete_page_lineage.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total books: {report['summary']['total_books']}")
    print(f"Books with TOC: {report['summary']['books_with_toc']}")
    print(f"Books without TOC: {report['summary']['books_without_toc']}")
    print(f"Books with page gaps: {report['summary']['books_with_gaps']}")
    print(f"Books with page count mismatches: {report['summary']['books_with_mismatches']}")
    print(f"Total pages: {report['summary']['total_pages']:,}")
    print(f"Total songs: {report['summary']['total_songs']:,}")
    
    # Show books with gaps
    if report['summary']['books_with_gaps'] > 0:
        print(f"\nBooks with page gaps (first 10):")
        count = 0
        for book in report['books']:
            if book['gaps']:
                count += 1
                if count > 10:
                    break
                print(f"  {book['artist']} / {book['book_name']}")
                print(f"    Gap pages: {', '.join(book['gaps'])}")
