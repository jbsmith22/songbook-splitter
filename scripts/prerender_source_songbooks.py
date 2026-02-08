#!/usr/bin/env python3
"""
Pre-render all SOURCE songbook PDF pages to JPG for validation.

This script extracts every page from the 559 source songbooks as images,
allowing us to validate extracted song data against actual source pages.

Unlike prerender_all_pages.py which renders extracted songs, this renders
the ORIGINAL source PDFs to enable comprehensive validation.

Usage:
    python prerender_source_songbooks.py --test 5         # Test with 5 books
    python prerender_source_songbooks.py --batch 50       # Render 50 books
    python prerender_source_songbooks.py --all            # Render all 559 books
    python prerender_source_songbooks.py --artist "Beatles"  # Render one artist
"""

import argparse
import logging
import json
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import fitz
import boto3

# Configuration
SOURCE_BUCKET = 'jsmith-input'
LOCAL_SHEETMUSIC = Path("d:/SheetMusic")  # Adjust if needed
CACHE_V2_PATH = Path("S:/SlowImageCache/pdf_verification_v2")
LINEAGE_DATA = Path("data/analysis/complete_lineage_data.json")
RENDER_DPI = 200  # Lower than 300 for source books (they're larger)
JPG_QUALITY = 85
MAX_WORKERS = 8

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prerender_source_songbooks.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

s3 = boto3.client('s3')


def load_book_list():
    """Load list of 559 unique books from lineage data."""
    if not LINEAGE_DATA.exists():
        logger.error(f"Lineage data not found at {LINEAGE_DATA}")
        return []

    with open(LINEAGE_DATA) as f:
        data = json.load(f)

    books = []
    for book in data.get('books', []):
        dynamodb = book.get('dynamodb', {})
        if dynamodb.get('exists'):
            books.append({
                'book_id': book['book_id'],
                'artist': dynamodb.get('artist', 'Unknown'),
                'book_name': dynamodb.get('book_name', 'Unknown'),
                'source_pdf_uri': dynamodb.get('source_pdf_uri', ''),
                'status': dynamodb.get('status', 'unknown')
            })

    logger.info(f"Loaded {len(books)} books from lineage data")
    return books


def get_local_pdf_path(source_pdf_uri: str) -> Path:
    """Convert S3 URI to local SheetMusic path."""
    # s3://jsmith-input/Artist/Book.pdf -> d:/SheetMusic/Artist/Book.pdf
    if source_pdf_uri.startswith('s3://'):
        s3_path = source_pdf_uri.replace('s3://jsmith-input/', '')
        local_path = LOCAL_SHEETMUSIC / s3_path
        return local_path
    return Path(source_pdf_uri)


def download_from_s3(source_pdf_uri: str, temp_path: Path) -> bool:
    """Download PDF from S3 if not available locally."""
    try:
        s3_path = source_pdf_uri.replace('s3://jsmith-input/', '')
        s3.download_file(SOURCE_BUCKET, s3_path, str(temp_path))
        return True
    except Exception as e:
        logger.error(f"Error downloading from S3: {e}")
        return False


def get_cache_dir(book_id: str, artist: str, book_name: str) -> Path:
    """Get cache directory for a book."""
    # Organize by artist/book like the original cache
    safe_artist = artist.replace('/', '_').replace('\\', '_')
    safe_book = book_name.replace('/', '_').replace('\\', '_')

    cache_dir = CACHE_V2_PATH / safe_artist / safe_book
    cache_dir.mkdir(parents=True, exist_ok=True)

    return cache_dir


def render_source_pdf(book_info: dict, use_s3: bool = False) -> tuple[int, int, float, str]:
    """
    Render all pages of a source songbook PDF to JPG.
    Returns (pages_rendered, pages_cached, time_seconds, status_message).
    """
    book_id = book_info['book_id']
    artist = book_info['artist']
    book_name = book_info['book_name']
    source_pdf_uri = book_info['source_pdf_uri']

    start_time = time.time()
    pages_rendered = 0
    pages_cached = 0

    # Get cache directory
    cache_dir = get_cache_dir(book_id, artist, book_name)

    # Try local path first
    local_pdf = get_local_pdf_path(source_pdf_uri)

    pdf_path = None
    temp_download = None

    if local_pdf.exists():
        pdf_path = local_pdf
        logger.debug(f"Using local PDF: {pdf_path}")
    elif use_s3:
        # Download from S3 to temp location
        import tempfile
        temp_download = Path(tempfile.gettempdir()) / f"{book_id}.pdf"
        if download_from_s3(source_pdf_uri, temp_download):
            pdf_path = temp_download
            logger.debug(f"Downloaded from S3 to: {temp_download}")
        else:
            return 0, 0, time.time() - start_time, "S3 download failed"
    else:
        return 0, 0, time.time() - start_time, "PDF not found locally"

    if not pdf_path:
        return 0, 0, time.time() - start_time, "No PDF available"

    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)

        zoom = RENDER_DPI / 72
        mat = fitz.Matrix(zoom, zoom)

        for page_num in range(page_count):
            cache_path = cache_dir / f"page_{page_num:04d}.jpg"

            # Skip if already cached
            if cache_path.exists():
                pages_cached += 1
                continue

            # Render page
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            pix.save(str(cache_path), "jpeg", jpg_quality=JPG_QUALITY)
            pages_rendered += 1

        doc.close()

        # Clean up temp download
        if temp_download and temp_download.exists():
            temp_download.unlink()

        status = f"OK: {pages_rendered} rendered, {pages_cached} cached"

    except Exception as e:
        logger.error(f"Error rendering {pdf_path}: {e}")
        status = f"ERROR: {str(e)}"
        return 0, 0, time.time() - start_time, status

    return pages_rendered, pages_cached, time.time() - start_time, status


def main():
    parser = argparse.ArgumentParser(description="Pre-render source songbook PDFs to JPG")
    parser.add_argument('--test', type=int, help="Test with N books")
    parser.add_argument('--batch', type=int, help="Render N books")
    parser.add_argument('--all', action='store_true', help="Render all 559 books")
    parser.add_argument('--artist', type=str, help="Render all books by specific artist")
    parser.add_argument('--s3', action='store_true', help="Download from S3 if not local")
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f"Number of workers (default: {MAX_WORKERS})")

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("SOURCE SONGBOOK PRE-RENDERER")
    logger.info("=" * 80)
    logger.info(f"Cache location: {CACHE_V2_PATH}")
    logger.info(f"Local SheetMusic: {LOCAL_SHEETMUSIC}")
    logger.info(f"Use S3 fallback: {args.s3}")
    logger.info(f"Workers: {args.workers}")
    logger.info("=" * 80)

    # Load book list
    all_books = load_book_list()

    if not all_books:
        logger.error("No books found in lineage data")
        return

    # Filter by artist if specified
    if args.artist:
        all_books = [b for b in all_books if b['artist'].lower() == args.artist.lower()]
        logger.info(f"Filtered to {len(all_books)} books by artist: {args.artist}")

    # Determine which books to process
    if args.test:
        import random
        books_to_process = random.sample(all_books, min(args.test, len(all_books)))
        logger.info(f"Test mode: Rendering {len(books_to_process)} random books")
    elif args.batch:
        import random
        books_to_process = random.sample(all_books, min(args.batch, len(all_books)))
        logger.info(f"Batch mode: Rendering {len(books_to_process)} books")
    elif args.all:
        books_to_process = all_books
        logger.info(f"Full mode: Rendering all {len(books_to_process)} books")
    elif args.artist:
        # If --artist is specified alone, process all books by that artist
        books_to_process = all_books
        logger.info(f"Artist mode: Rendering all {len(books_to_process)} books by {args.artist}")
    else:
        logger.error("Please specify --test N, --batch N, --all, or --artist NAME")
        return

    # Render books with progress bar
    total_rendered = 0
    total_cached = 0
    total_time = 0
    successes = 0
    failures = 0

    results = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(render_source_pdf, book, args.s3): book for book in books_to_process}

        with tqdm(total=len(books_to_process), desc="Rendering source PDFs") as pbar:
            for future in as_completed(futures):
                try:
                    rendered, cached, elapsed, status = future.result()
                    total_rendered += rendered
                    total_cached += cached
                    total_time += elapsed

                    book = futures[future]

                    if rendered > 0 or cached > 0:
                        successes += 1
                    else:
                        failures += 1

                    results.append({
                        'book_id': book['book_id'],
                        'artist': book['artist'],
                        'book_name': book['book_name'],
                        'pages_rendered': rendered,
                        'pages_cached': cached,
                        'time_seconds': elapsed,
                        'status': status
                    })

                    pbar.set_postfix({
                        'success': successes,
                        'fail': failures,
                        'pages': total_rendered + total_cached
                    })
                    pbar.update(1)

                except Exception as e:
                    book = futures[future]
                    logger.error(f"Error processing {book['book_id']}: {e}")
                    failures += 1
                    pbar.update(1)

    # Save results
    results_file = Path("prerender_results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_books': len(books_to_process),
            'successes': successes,
            'failures': failures,
            'total_pages_rendered': total_rendered,
            'total_pages_cached': total_cached,
            'total_time_seconds': total_time,
            'books': results
        }, f, indent=2)

    # Summary
    logger.info("=" * 80)
    logger.info("PRE-RENDERING COMPLETE!")
    logger.info("=" * 80)
    logger.info(f"Books processed: {len(books_to_process)}")
    logger.info(f"Successes: {successes}")
    logger.info(f"Failures: {failures}")
    logger.info(f"Pages rendered: {total_rendered}")
    logger.info(f"Pages cached (skipped): {total_cached}")
    logger.info(f"Total pages: {total_rendered + total_cached}")
    logger.info(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if total_rendered > 0:
        logger.info(f"Average per page: {total_time/total_rendered:.3f}s")
    logger.info(f"Results saved to: {results_file}")
    logger.info("=" * 80)
    logger.info(f"Next step: Use local LLM to analyze images in {CACHE_V2_PATH}")


if __name__ == "__main__":
    main()
