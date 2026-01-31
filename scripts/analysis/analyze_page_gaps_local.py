#!/usr/bin/env python3
"""
Analyze page gaps using locally available data (output folder manifests and TOCs).
"""

import json
from pathlib import Path
from collections import defaultdict
import PyPDF2

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
OUTPUT_PATH = Path("c:/Work/AWSMusic/output")

def get_pdf_page_count(pdf_path):
    """Get the number of pages in a PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except:
        return 0

def load_local_manifests():
    """Load all manifest files from output directory."""
    manifests = {}
    
    if not OUTPUT_PATH.exists():
        return manifests
    
    for manifest_file in OUTPUT_PATH.glob("*_manifest.json"):
        try:
            with open(manifest_file, 'r') as f:
                data = json.load(f)
                book_name = data.get('book_name', manifest_file.stem.replace('_manifest', ''))
                manifests[book_name] = data
        except:
            pass
    
    return manifests

def load_local_tocs():
    """Load all TOC files from output directory."""
    tocs = {}
    
    if not OUTPUT_PATH.exists():
        return tocs
    
    for toc_file in OUTPUT_PATH.glob("*_toc.json"):
        try:
            with open(toc_file, 'r') as f:
                data = json.load(f)
                book_name = toc_file.stem.replace('_toc', '')
                tocs[book_name] = data
        except:
            pass
    
    return tocs

def find_book_directory(artist, book_name):
    """Find the directory for a book."""
    artist_dir = PROCESSED_SONGS_PATH / artist
    if not artist_dir.exists():
        return None
    
    # Try exact match first
    book_dir = artist_dir / book_name
    if book_dir.exists():
        return book_dir
    
    # Try without artist prefix
    if ' - ' in book_name:
        book_name_without_artist = book_name.split(' - ', 1)[1]
        book_dir = artist_dir / book_name_without_artist
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

def analyze_book_coverage(book_name, manifest_data, toc_data):
    """Analyze page coverage for a book."""
    
    artist = manifest_data.get('artist', 'Unknown')
    
    # Find book directory
    book_dir = find_book_directory(artist, book_name)
    if not book_dir:
        return {
            'artist': artist,
            'book_name': book_name,
            'status': 'not_found',
            'message': 'Book directory not found in ProcessedSongs'
        }
    
    # Get expected pages from TOC
    expected_songs = {}
    if toc_data and 'entries' in toc_data:
        for entry in toc_data['entries']:
            song_title = entry.get('title', 'Unknown')
            page_num = entry.get('page', 0)
            expected_songs[song_title] = {
                'page': page_num,
                'title': song_title
            }
    
    # Get actual PDFs and their page counts
    actual_songs = []
    total_actual_pages = 0
    
    for pdf_file in sorted(book_dir.glob("*.pdf")):
        if pdf_file.suffix == '.original':
            continue
        
        has_backup = pdf_file.with_suffix('.pdf.original').exists()
        if has_backup:
            page_count = get_pdf_page_count(pdf_file.with_suffix('.pdf.original'))
        else:
            page_count = get_pdf_page_count(pdf_file)
        
        total_actual_pages += page_count
        
        actual_songs.append({
            'filename': pdf_file.name,
            'page_count': page_count,
            'was_split': has_backup
        })
    
    # Calculate coverage
    total_expected = len(expected_songs)
    total_actual = len(actual_songs)
    
    # Try to match songs
    matched = 0
    unmatched_expected = []
    unmatched_actual = []
    
    for expected_title in expected_songs.keys():
        found = False
        for actual in actual_songs:
            # Fuzzy match
            if expected_title.lower() in actual['filename'].lower() or \
               actual['filename'].lower().replace('.pdf', '').split(' - ')[-1] in expected_title.lower():
                matched += 1
                found = True
                break
        if not found:
            unmatched_expected.append({
                'title': expected_title,
                'expected_page': expected_songs[expected_title]['page']
            })
    
    for actual in actual_songs:
        found = False
        for expected_title in expected_songs.keys():
            if expected_title.lower() in actual['filename'].lower() or \
               actual['filename'].lower().replace('.pdf', '').split(' - ')[-1] in expected_title.lower():
                found = True
                break
        if not found:
            unmatched_actual.append(actual['filename'])
    
    # Estimate expected total pages (rough estimate based on TOC)
    if expected_songs:
        max_page = max(s['page'] for s in expected_songs.values())
        estimated_total_pages = max_page + 50  # Rough estimate
    else:
        estimated_total_pages = total_actual_pages
    
    return {
        'artist': artist,
        'book_name': book_name,
        'status': 'analyzed',
        'expected_songs': total_expected,
        'actual_songs': total_actual,
        'matched_songs': matched,
        'missing_songs': unmatched_expected,
        'extra_songs': unmatched_actual,
        'total_actual_pages': total_actual_pages,
        'estimated_total_pages': estimated_total_pages,
        'page_coverage_percent': (total_actual_pages / estimated_total_pages * 100) if estimated_total_pages > 0 else 0,
        'song_coverage_percent': (matched / total_expected * 100) if total_expected > 0 else 0
    }

def generate_gap_report(analyses):
    """Generate a comprehensive gap report."""
    from datetime import datetime
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_books': len(analyses),
            'books_analyzed': sum(1 for a in analyses if a and a.get('status') == 'analyzed'),
            'books_not_found': sum(1 for a in analyses if a and a.get('status') == 'not_found'),
            'books_with_missing_songs': 0,
            'books_with_extra_songs': 0,
            'total_missing_songs': 0,
            'total_extra_songs': 0
        },
        'books': []
    }
    
    for analysis in analyses:
        if not analysis or analysis.get('status') != 'analyzed':
            if analysis:
                report['books'].append(analysis)
            continue
        
        if analysis['missing_songs']:
            report['summary']['books_with_missing_songs'] += 1
            report['summary']['total_missing_songs'] += len(analysis['missing_songs'])
        
        if analysis['extra_songs']:
            report['summary']['books_with_extra_songs'] += 1
            report['summary']['total_extra_songs'] += len(analysis['extra_songs'])
        
        report['books'].append(analysis)
    
    # Sort by song coverage percent (worst first)
    report['books'].sort(key=lambda x: x.get('song_coverage_percent', 100))
    
    return report

if __name__ == "__main__":
    print("Analyzing page gaps using local data...")
    print("=" * 80)
    
    # Load local manifests and TOCs
    print("\n1. Loading local manifests and TOCs...")
    manifests = load_local_manifests()
    tocs = load_local_tocs()
    print(f"   Found {len(manifests)} manifests and {len(tocs)} TOCs")
    
    if not manifests:
        print("\n   No manifests found in output directory.")
        print("   Run the AWS pipeline first or download artifacts from S3.")
        exit(1)
    
    # Analyze each book
    print("\n2. Analyzing each book...")
    analyses = []
    
    for i, (book_name, manifest) in enumerate(manifests.items(), 1):
        print(f"   [{i}/{len(manifests)}] {book_name}...", end='')
        
        # Find matching TOC
        toc = tocs.get(book_name)
        
        # Analyze
        analysis = analyze_book_coverage(book_name, manifest, toc)
        analyses.append(analysis)
        
        if analysis and analysis.get('status') == 'analyzed':
            song_coverage = analysis.get('song_coverage_percent', 0)
            page_coverage = analysis.get('page_coverage_percent', 0)
            missing = len(analysis.get('missing_songs', []))
            extra = len(analysis.get('extra_songs', []))
            print(f" {song_coverage:.0f}% songs, {page_coverage:.0f}% pages ({missing} missing, {extra} extra)")
        else:
            print(f" {analysis.get('status', 'unknown')}")
    
    # Generate report
    print("\n3. Generating gap report...")
    report = generate_gap_report(analyses)
    
    output_file = Path("page_gap_analysis.json")
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"   ✓ Report saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total books: {report['summary']['total_books']}")
    print(f"Books analyzed: {report['summary']['books_analyzed']}")
    print(f"Books with missing songs: {report['summary']['books_with_missing_songs']}")
    print(f"Books with extra songs: {report['summary']['books_with_extra_songs']}")
    print(f"Total missing songs: {report['summary']['total_missing_songs']}")
    print(f"Total extra songs: {report['summary']['total_extra_songs']}")
    
    # Show books with gaps
    if report['books']:
        print("\nBooks with lowest song coverage:")
        count = 0
        for book in report['books']:
            if book.get('status') != 'analyzed':
                continue
            if book['song_coverage_percent'] < 100:
                count += 1
                if count > 10:
                    break
                print(f"  {book['song_coverage_percent']:.0f}% - {book['artist']} / {book['book_name']}")
                if book['missing_songs']:
                    missing_titles = [m['title'] for m in book['missing_songs'][:3]]
                    print(f"         Missing: {', '.join(missing_titles)}")
                    if len(book['missing_songs']) > 3:
                        print(f"         ... and {len(book['missing_songs']) - 3} more")
