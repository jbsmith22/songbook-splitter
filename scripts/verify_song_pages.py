"""
Comprehensive song PDF page verification.

For every extracted song PDF, renders each page and compares it against the
corresponding source page image from the v3 image cache. Uses imagehash
perceptual hashing for robust comparison that handles JPEG compression differences.

Checks:
  1. Structural: page counts match metadata, no gaps/overlaps in coverage
  2. Visual: every page in every song PDF matches the expected source page
  3. Boundary: first/last pages of each song are at expected positions

Usage:
    python scripts/verify_song_pages.py                    # Verify all 342 books
    python scripts/verify_song_pages.py --artist "Pink Floyd"  # One artist
    python scripts/verify_song_pages.py --book-limit 10    # First N books only
    python scripts/verify_song_pages.py --workers 2        # Limit parallelism
"""

import argparse
import json
import sys
import time
import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import imagehash
from PIL import Image
import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
CACHE_DIR = Path('S:/SlowImageCache/pdf_verification_v3')
RENDER_DPI = 72  # Lower DPI for comparison (faster rendering)
HASH_SIZE = 16   # Hash resolution (produces HASH_SIZE^2 bits)
MISMATCH_THRESHOLD = 15  # Max hamming distance for pHash "match" (out of 256 bits)


def render_pdf_page(doc, page_num, dpi=72):
    """Render a PDF page to a PIL Image at given DPI."""
    zoom = dpi / 72
    mat = fitz.Matrix(zoom, zoom)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def load_cache_image(cache_path):
    """Load a cached source page image."""
    return Image.open(cache_path).convert('RGB')


def verify_book(book_info):
    """Verify all song PDFs for a single book.

    Returns a dict with:
      - artist, book: identifiers
      - structural_issues: list of structural problems
      - page_results: list of per-page comparison results
      - summary: counts of matches/mismatches/errors
    """
    artist = book_info['artist']
    book = book_info['book']
    threshold = book_info.get('threshold', MISMATCH_THRESHOLD)
    result = {
        'artist': artist,
        'book': book,
        'structural_issues': [],
        'page_mismatches': [],
        'song_issues': [],
        'songs_checked': 0,
        'pages_compared': 0,
        'pages_matched': 0,
        'pages_mismatched': 0,
        'pages_error': 0,
        'songs_missing_pdf': 0,
        'songs_missing_cache': 0,
        'status': 'OK',
    }

    # Load artifacts
    artifacts_path = ARTIFACTS_DIR / artist / book
    verified_path = artifacts_path / 'verified_songs.json'
    output_files_path = artifacts_path / 'output_files.json'

    if not verified_path.exists():
        result['status'] = 'MISSING_ARTIFACTS'
        result['structural_issues'].append('verified_songs.json not found')
        return result

    if not output_files_path.exists():
        result['status'] = 'MISSING_ARTIFACTS'
        result['structural_issues'].append('output_files.json not found')
        return result

    try:
        with open(verified_path, 'r', encoding='utf-8') as f:
            verified_data = json.load(f)
        with open(output_files_path, 'r', encoding='utf-8') as f:
            output_data = json.load(f)
    except Exception as e:
        result['status'] = 'JSON_ERROR'
        result['structural_issues'].append(f'JSON parse error: {e}')
        return result

    songs = verified_data.get('verified_songs', [])
    output_files = output_data.get('output_files', [])

    if not songs:
        result['structural_issues'].append('No songs in verified_songs.json')
        result['status'] = 'NO_SONGS'
        return result

    # Build output filename lookup from output_files.json
    # Extract filename from S3 URI
    output_lookup = {}
    for of in output_files:
        uri = of.get('output_uri', '')
        filename = uri.split('/')[-1] if '/' in uri else ''
        output_lookup[of['song_title']] = {
            'filename': filename,
            'page_range': of.get('page_range', []),
            'file_size': of.get('file_size_bytes', 0),
        }

    # Structural check: verify page coverage (no gaps, no overlaps)
    songs_sorted = sorted(songs, key=lambda s: s['start_page'])
    for i in range(len(songs_sorted) - 1):
        curr = songs_sorted[i]
        nxt = songs_sorted[i + 1]
        if curr['end_page'] < nxt['start_page']:
            result['structural_issues'].append(
                f"GAP: pages {curr['end_page']}-{nxt['start_page']-1} between "
                f"'{curr['song_title']}' and '{nxt['song_title']}'"
            )
        elif curr['end_page'] > nxt['start_page']:
            result['structural_issues'].append(
                f"OVERLAP: '{curr['song_title']}' ends at {curr['end_page']} but "
                f"'{nxt['song_title']}' starts at {nxt['start_page']}"
            )

    # Check cache directory exists
    cache_book_dir = CACHE_DIR / artist / book
    if not cache_book_dir.exists():
        result['status'] = 'MISSING_CACHE'
        result['structural_issues'].append(f'Cache dir not found: {cache_book_dir}')
        return result

    # Process each song
    output_book_dir = OUTPUT_DIR / artist / book

    for song in songs:
        title = song['song_title']
        start_page = song['start_page']
        end_page = song['end_page']
        expected_pages = end_page - start_page

        result['songs_checked'] += 1

        # Find the song PDF
        out_info = output_lookup.get(title, {})
        filename = out_info.get('filename', '')

        if not filename:
            # Try to construct filename
            filename = f"{artist} - {title}.pdf"

        song_pdf_path = output_book_dir / filename

        # If exact path doesn't exist, try case-insensitive search
        if not song_pdf_path.exists():
            # Search for matching file
            found = False
            if output_book_dir.exists():
                for f in output_book_dir.iterdir():
                    if f.name.lower() == filename.lower():
                        song_pdf_path = f
                        found = True
                        break
                    # Also try matching just the song title portion
                    if f.suffix.lower() == '.pdf' and title.lower() in f.stem.lower():
                        song_pdf_path = f
                        found = True
                        break

            if not found:
                result['songs_missing_pdf'] += 1
                result['song_issues'].append(
                    f"MISSING PDF: '{title}' (expected: {filename})"
                )
                continue

        # Open song PDF and verify
        try:
            song_doc = fitz.open(song_pdf_path)
        except Exception as e:
            result['pages_error'] += expected_pages
            result['song_issues'].append(f"PDF OPEN ERROR: '{title}': {e}")
            continue

        actual_pages = len(song_doc)

        # Page count check
        if actual_pages != expected_pages:
            result['structural_issues'].append(
                f"PAGE COUNT: '{title}' has {actual_pages} pages, "
                f"expected {expected_pages} (range {start_page}-{end_page})"
            )

        # Compare each page
        pages_to_check = min(actual_pages, expected_pages)
        song_ok = True

        for page_idx in range(pages_to_check):
            source_page_num = start_page + page_idx
            cache_img_path = cache_book_dir / f"page_{source_page_num:04d}.jpg"

            if not cache_img_path.exists():
                result['pages_error'] += 1
                if page_idx == 0:
                    result['songs_missing_cache'] += 1
                continue

            try:
                # Render song page
                song_img = render_pdf_page(song_doc, page_idx, dpi=RENDER_DPI)

                # Load cached source image
                source_img = load_cache_image(cache_img_path)

                # Compute perceptual hashes and compare (pHash is more robust
                # than dHash for sheet music with JPEG compression differences)
                song_hash = imagehash.phash(song_img, hash_size=HASH_SIZE)
                source_hash = imagehash.phash(source_img, hash_size=HASH_SIZE)
                distance = song_hash - source_hash

                result['pages_compared'] += 1

                if distance <= threshold:
                    result['pages_matched'] += 1
                else:
                    result['pages_mismatched'] += 1
                    song_ok = False
                    position = 'FIRST' if page_idx == 0 else (
                        'LAST' if page_idx == pages_to_check - 1 else 'MID'
                    )
                    result['page_mismatches'].append({
                        'song': title,
                        'song_page': page_idx,
                        'expected_source_page': source_page_num,
                        'distance': int(distance),
                        'position': position,
                        'song_pdf': str(song_pdf_path.name),
                    })

            except Exception as e:
                result['pages_error'] += 1

        song_doc.close()

        if not song_ok:
            result['song_issues'].append(f"VISUAL MISMATCH: '{title}' has page mismatches")

    # Set overall status
    if result['pages_mismatched'] > 0:
        result['status'] = 'MISMATCHES'
    elif result['songs_missing_pdf'] > 0:
        result['status'] = 'MISSING_PDFS'
    elif result['structural_issues']:
        result['status'] = 'STRUCTURAL'
    elif result['pages_error'] > 0:
        result['status'] = 'ERRORS'
    else:
        result['status'] = 'OK'

    return result


def discover_books():
    """Find all v3 books from artifacts directory."""
    books = []
    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name
            books.append({'artist': artist, 'book': book})
    return books


def main():
    parser = argparse.ArgumentParser(description="Verify song PDF pages against source images")
    parser.add_argument('--artist', type=str, help="Verify only one artist")
    parser.add_argument('--book', type=str, help="Verify only one book (requires --artist)")
    parser.add_argument('--book-limit', type=int, help="Limit to first N books")
    parser.add_argument('--workers', type=int, default=4, help="Parallel workers (default: 4)")
    parser.add_argument('--threshold', type=int, default=MISMATCH_THRESHOLD,
                        help=f"Hash distance threshold (default: {MISMATCH_THRESHOLD})")
    args = parser.parse_args()

    books = discover_books()

    if args.artist:
        books = [b for b in books if b['artist'].lower() == args.artist.lower()]
        if args.book:
            books = [b for b in books if b['book'].lower() == args.book.lower()]

    if args.book_limit:
        books = books[:args.book_limit]

    # Inject threshold into book_info dicts for workers
    for b in books:
        b['threshold'] = args.threshold

    print(f"Song PDF Page Verification")
    print(f"  Books to verify: {len(books)}")
    print(f"  Source cache: {CACHE_DIR}")
    print(f"  Comparison DPI: {RENDER_DPI}")
    print(f"  Hash size: {HASH_SIZE}x{HASH_SIZE} ({HASH_SIZE**2} bits)")
    print(f"  Mismatch threshold: {args.threshold}")
    print(f"  Workers: {args.workers}")
    print()

    start = time.time()
    all_results = []
    total_ok = 0
    total_issues = 0
    total_pages_compared = 0
    total_pages_matched = 0
    total_pages_mismatched = 0
    total_songs = 0
    total_missing_pdfs = 0

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(verify_book, b): b for b in books}
        done_count = 0

        for future in as_completed(futures):
            done_count += 1
            result = future.result()
            all_results.append(result)

            total_songs += result['songs_checked']
            total_pages_compared += result['pages_compared']
            total_pages_matched += result['pages_matched']
            total_pages_mismatched += result['pages_mismatched']
            total_missing_pdfs += result['songs_missing_pdf']

            if result['status'] == 'OK':
                total_ok += 1
                tag = 'OK'
            else:
                total_issues += 1
                tag = result['status']

            elapsed = time.time() - start
            rate = done_count / elapsed if elapsed > 0 else 0
            eta = (len(books) - done_count) / rate if rate > 0 else 0

            # Show summary per book
            mismatch_str = ''
            if result['pages_mismatched'] > 0:
                mismatch_str = f" ** {result['pages_mismatched']} MISMATCHES **"
            if result['songs_missing_pdf'] > 0:
                mismatch_str += f" ({result['songs_missing_pdf']} missing PDFs)"

            print(
                f"  [{done_count}/{len(books)}] {tag:16s} "
                f"{result['artist']} / {result['book']} "
                f"({result['songs_checked']} songs, "
                f"{result['pages_compared']} pages){mismatch_str} "
                f"[{elapsed:.0f}s, ETA {eta:.0f}s]"
            )

    elapsed = time.time() - start

    # Sort results by artist/book for report
    all_results.sort(key=lambda r: (r['artist'], r['book']))

    # Print summary
    print()
    print("=" * 80)
    print(f"VERIFICATION COMPLETE in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print("=" * 80)
    print()
    print(f"  Books verified:    {len(books)}")
    print(f"  Books OK:          {total_ok}")
    print(f"  Books with issues: {total_issues}")
    print(f"  Songs checked:     {total_songs}")
    print(f"  Songs missing PDF: {total_missing_pdfs}")
    print(f"  Pages compared:    {total_pages_compared}")
    print(f"  Pages matched:     {total_pages_matched}")
    print(f"  Pages mismatched:  {total_pages_mismatched}")
    print()

    # Detail any issues
    structural_issues = [r for r in all_results if r['structural_issues']]
    mismatch_books = [r for r in all_results if r['pages_mismatched'] > 0]
    missing_pdf_books = [r for r in all_results if r['songs_missing_pdf'] > 0]
    error_books = [r for r in all_results if r['pages_error'] > 0]

    if structural_issues:
        print(f"\nSTRUCTURAL ISSUES ({len(structural_issues)} books):")
        print("-" * 60)
        for r in structural_issues:
            print(f"\n  {r['artist']} / {r['book']}:")
            for issue in r['structural_issues']:
                print(f"    - {issue}")

    if mismatch_books:
        print(f"\nVISUAL MISMATCHES ({len(mismatch_books)} books):")
        print("-" * 60)
        for r in mismatch_books:
            print(f"\n  {r['artist']} / {r['book']} ({r['pages_mismatched']} mismatched pages):")
            for m in r['page_mismatches']:
                print(
                    f"    [{m['position']}] '{m['song']}' page {m['song_page']} "
                    f"vs source page {m['expected_source_page']} "
                    f"(distance={m['distance']})"
                )

    if missing_pdf_books:
        print(f"\nMISSING SONG PDFs ({len(missing_pdf_books)} books):")
        print("-" * 60)
        for r in missing_pdf_books:
            print(f"\n  {r['artist']} / {r['book']} ({r['songs_missing_pdf']} missing):")
            for issue in r['song_issues']:
                if 'MISSING PDF' in issue:
                    print(f"    - {issue}")

    if error_books:
        print(f"\nERRORS ({len(error_books)} books):")
        print("-" * 60)
        for r in error_books:
            print(f"\n  {r['artist']} / {r['book']} ({r['pages_error']} errors):")
            for issue in r['song_issues']:
                if 'ERROR' in issue:
                    print(f"    - {issue}")

    if not structural_issues and not mismatch_books and not missing_pdf_books and not error_books:
        print("\n  ALL CLEAR - Every page of every song matches its source!")

    # Save detailed results to JSON
    report_path = PROJECT_ROOT / 'data' / 'v3_verification' / 'page_verification_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': {
                'render_dpi': RENDER_DPI,
                'hash_size': HASH_SIZE,
                'mismatch_threshold': MISMATCH_THRESHOLD,
            },
            'summary': {
                'books_verified': len(books),
                'books_ok': total_ok,
                'books_with_issues': total_issues,
                'songs_checked': total_songs,
                'songs_missing_pdf': total_missing_pdfs,
                'pages_compared': total_pages_compared,
                'pages_matched': total_pages_matched,
                'pages_mismatched': total_pages_mismatched,
                'elapsed_seconds': elapsed,
            },
            'books': all_results,
        }, f, indent=2)
    print(f"\nDetailed report saved to: {report_path}")


if __name__ == '__main__':
    main()
