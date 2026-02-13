"""
Pre-render all v3 songbook input PDFs to JPG page images.

Reads from SheetMusic_Input/{Artist}/{Artist} - {Book}.pdf
Writes to S:/SlowImageCache/pdf_verification_v3/{Artist}/{Book}/page_NNNN.jpg

Usage:
    python scripts/prerender_v3_images.py              # Render all 342 books
    python scripts/prerender_v3_images.py --artist "Pink Floyd"  # One artist
    python scripts/prerender_v3_images.py --workers 4  # Limit parallelism
"""

import argparse
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import fitz  # PyMuPDF

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
CACHE_DIR = Path('S:/SlowImageCache/pdf_verification_v3')
RENDER_DPI = 200
JPG_QUALITY = 85


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
            pdf_path = INPUT_DIR / artist / f"{artist} - {book}.pdf"
            books.append({
                'artist': artist,
                'book': book,
                'pdf_path': pdf_path,
            })
    return books


def render_book(book_info):
    """Render all pages of a single book PDF to JPG images."""
    artist = book_info['artist']
    book = book_info['book']
    pdf_path = book_info['pdf_path']

    if not pdf_path.exists():
        return artist, book, 0, 0, 0, f"PDF not found: {pdf_path}"

    cache_dir = CACHE_DIR / artist / book
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        zoom = RENDER_DPI / 72
        mat = fitz.Matrix(zoom, zoom)

        rendered = 0
        skipped = 0

        for page_num in range(page_count):
            out_path = cache_dir / f"page_{page_num:04d}.jpg"
            if out_path.exists():
                skipped += 1
                continue
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            pix.save(str(out_path), "jpeg", jpg_quality=JPG_QUALITY)
            rendered += 1

        doc.close()
        return artist, book, rendered, skipped, page_count, "OK"

    except Exception as e:
        return artist, book, 0, 0, 0, f"ERROR: {e}"


def main():
    parser = argparse.ArgumentParser(description="Pre-render v3 songbook PDFs to JPG")
    parser.add_argument('--artist', type=str, help="Render only one artist")
    parser.add_argument('--workers', type=int, default=4, help="Parallel workers (default: 4)")
    args = parser.parse_args()

    books = discover_books()
    if args.artist:
        books = [b for b in books if b['artist'].lower() == args.artist.lower()]

    print(f"V3 Image Cache Pre-renderer")
    print(f"  Books to process: {len(books)}")
    print(f"  Output: {CACHE_DIR}")
    print(f"  DPI: {RENDER_DPI}, JPG quality: {JPG_QUALITY}")
    print(f"  Workers: {args.workers}")
    print()

    total_rendered = 0
    total_skipped = 0
    total_pages = 0
    successes = 0
    failures = 0
    failed_books = []
    start = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(render_book, b): b for b in books}
        done_count = 0

        for future in as_completed(futures):
            done_count += 1
            artist, book, rendered, skipped, pages, status = future.result()
            total_rendered += rendered
            total_skipped += skipped
            total_pages += pages

            if status == "OK":
                successes += 1
                tag = "OK"
                if rendered == 0 and skipped > 0:
                    tag = "CACHED"
            else:
                failures += 1
                tag = "FAIL"
                failed_books.append(f"{artist} / {book}: {status}")

            elapsed = time.time() - start
            rate = done_count / elapsed if elapsed > 0 else 0
            eta = (len(books) - done_count) / rate if rate > 0 else 0

            print(f"  [{done_count}/{len(books)}] {tag:6s} {artist} / {book} "
                  f"({rendered} new, {skipped} cached, {pages} total) "
                  f"[{elapsed:.0f}s elapsed, ETA {eta:.0f}s]")

    elapsed = time.time() - start
    print()
    print(f"COMPLETE in {elapsed:.0f}s ({elapsed/60:.1f} min)")
    print(f"  Books: {successes} OK, {failures} failed")
    print(f"  Pages: {total_rendered} rendered, {total_skipped} cached, {total_pages} total")

    if failed_books:
        print(f"\nFailed books:")
        for fb in failed_books:
            print(f"  {fb}")


if __name__ == '__main__':
    main()
