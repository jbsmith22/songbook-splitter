#!/usr/bin/env python3
"""
Analyze page gaps by comparing TOC data (expected pages) with actual extracted PDFs.
Downloads TOC and page mapping data from S3 to identify missing pages.
"""

import json
import boto3
from pathlib import Path
from collections import defaultdict
import PyPDF2

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
S3_BUCKET = "jsmith-output"

def get_s3_client():
    """Get boto3 S3 client."""
    return boto3.client('s3', region_name='us-east-1')

def list_book_artifacts():
    """List all book artifacts in S3."""
    s3 = get_s3_client()
    
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='artifacts/',
            Delimiter='/'
        )
        
        book_ids = []
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                book_id = prefix['Prefix'].split('/')[-2]
                book_ids.append(book_id)
        
        return book_ids
    except Exception as e:
        print(f"Error listing S3 artifacts: {e}")
        return []

def download_toc_data(book_id):
    """Download TOC data for a book from S3."""
    s3 = get_s3_client()
    
    toc_key = f"artifacts/{book_id}/toc_parse.json"
    
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=toc_key)
        toc_data = json.loads(response['Body'].read())
        return toc_data
    except:
        return None

def download_output_files(book_id):
    """Download output files data for a book from S3."""
    s3 = get_s3_client()
    
    output_key = f"artifacts/{book_id}/output_files.json"
    
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=output_key)
        output_data = json.loads(response['Body'].read())
        return output_data
    except:
        return None

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
    
    # Try fuzzy match
    for dir in artist_dir.iterdir():
        if dir.is_dir() and book_name.lower() in dir.name.lower():
            return dir
    
    return None

def analyze_book_coverage(book_id, toc_data, output_data):
    """Analyze page coverage for a book."""
    
    if not output_data or 'output_files' not in output_data:
        return {
            'book_id': book_id,
            'status': 'no_output',
            'message': 'No output files found'
        }
    
    # Get artist and book name from first output file
    first_file = output_data['output_files'][0] if output_data['output_files'] else {}
    artist = first_file.get('artist', 'Unknown')
    
    # Extract book name from S3 URI
    output_uri = first_file.get('output_uri', '')
    if output_uri:
        # s3://jsmith-output/Artist/Book Name/Songs/...
        parts = output_uri.replace('s3://jsmith-output/', '').split('/')
        if len(parts) >= 2:
            book_name = parts[1]
        else:
            book_name = 'Unknown'
    else:
        book_name = 'Unknown'
    
    # Find book directory
    book_dir = find_book_directory(artist, book_name)
    if not book_dir:
        return {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name,
            'status': 'not_found',
            'message': 'Book directory not found in ProcessedSongs'
        }
    
    # Get expected pages from TOC
    expected_songs = {}
    if toc_data and 'entries' in toc_data:
        for entry in toc_data['entries']:
            song_title = entry.get('song_title', 'Unknown')
            page_num = entry.get('page_number', 0)
            expected_songs[song_title] = page_num
    
    # Get actual PDFs
    actual_songs = []
    for pdf_file in book_dir.glob("*.pdf"):
        if pdf_file.suffix == '.original':
            continue
        
        has_backup = pdf_file.with_suffix('.pdf.original').exists()
        if has_backup:
            page_count = get_pdf_page_count(pdf_file.with_suffix('.pdf.original'))
        else:
            page_count = get_pdf_page_count(pdf_file)
        
        actual_songs.append({
            'filename': pdf_file.name,
            'page_count': page_count
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
            if expected_title.lower() in actual['filename'].lower():
                matched += 1
                found = True
                break
        if not found:
            unmatched_expected.append(expected_title)
    
    for actual in actual_songs:
        found = False
        for expected_title in expected_songs.keys():
            if expected_title.lower() in actual['filename'].lower():
                found = True
                break
        if not found:
            unmatched_actual.append(actual['filename'])
    
    return {
        'book_id': book_id,
        'artist': artist,
        'book_name': book_name,
        'status': 'analyzed',
        'expected_songs': total_expected,
        'actual_songs': total_actual,
        'matched_songs': matched,
        'missing_songs': unmatched_expected,
        'extra_songs': unmatched_actual,
        'coverage_percent': (matched / total_expected * 100) if total_expected > 0 else 0
    }

def generate_gap_report(analyses):
    """Generate a comprehensive gap report."""
    
    report = {
        'generated_at': json.dumps(None),  # Will be set below
        'summary': {
            'total_books': len(analyses),
            'books_analyzed': sum(1 for a in analyses if a and a.get('status') == 'analyzed'),
            'books_not_found': sum(1 for a in analyses if a and a.get('status') == 'not_found'),
            'books_with_gaps': 0,
            'total_missing_songs': 0,
            'total_extra_songs': 0
        },
        'books': []
    }
    
    for analysis in analyses:
        if not analysis or analysis.get('status') != 'analyzed':
            continue
        
        if analysis['missing_songs'] or analysis['extra_songs']:
            report['summary']['books_with_gaps'] += 1
        
        report['summary']['total_missing_songs'] += len(analysis['missing_songs'])
        report['summary']['total_extra_songs'] += len(analysis['extra_songs'])
        
        report['books'].append(analysis)
    
    # Sort by coverage percent (worst first)
    report['books'].sort(key=lambda x: x.get('coverage_percent', 100))
    
    return report

if __name__ == "__main__":
    import sys
    from datetime import datetime
    
    print("Analyzing page gaps...")
    print("=" * 80)
    
    # List all book artifacts
    print("\n1. Listing book artifacts from S3...")
    book_ids = list_book_artifacts()
    print(f"   Found {len(book_ids)} books in S3")
    
    if not book_ids:
        print("\n   No books found in S3. Make sure you're logged in:")
        print("   aws sso login --profile default")
        sys.exit(1)
    
    # Analyze each book
    print("\n2. Analyzing each book (first 5 for testing)...")
    analyses = []
    
    for i, book_id in enumerate(book_ids[:5], 1):  # Test with first 5
        print(f"   [{i}/5] Processing {book_id}...", end='')
        
        # Download data
        output_data = download_output_files(book_id)
        toc = download_toc_data(book_id)
        
        if not output_data:
            print(" (no output)")
            continue
        
        # Analyze
        analysis = analyze_book_coverage(book_id, toc, output_data)
        analyses.append(analysis)
        
        if analysis and analysis.get('status') == 'analyzed':
            coverage = analysis.get('coverage_percent', 0)
            missing = len(analysis.get('missing_songs', []))
            extra = len(analysis.get('extra_songs', []))
            print(f" {coverage:.1f}% coverage ({missing} missing, {extra} extra)")
        else:
            print(f" {analysis.get('status', 'unknown')}")
    
    # Generate report
    print("\n3. Generating gap report...")
    report = generate_gap_report(analyses)
    report['generated_at'] = datetime.now().isoformat()
    
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
    print(f"Books with gaps: {report['summary']['books_with_gaps']}")
    print(f"Total missing songs: {report['summary']['total_missing_songs']}")
    print(f"Total extra songs: {report['summary']['total_extra_songs']}")
    
    # Show worst offenders
    if report['books']:
        print("\nBooks with lowest coverage:")
        for book in report['books'][:10]:
            if book['coverage_percent'] < 100:
                print(f"  {book['coverage_percent']:.1f}% - {book['artist']} / {book['book_name']}")
                if book['missing_songs']:
                    print(f"         Missing: {', '.join(book['missing_songs'][:3])}")
                    if len(book['missing_songs']) > 3:
                        print(f"         ... and {len(book['missing_songs']) - 3} more")
