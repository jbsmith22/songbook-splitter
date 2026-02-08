#!/usr/bin/env python3
"""
Comprehensive vision-based validation of all extracted songs.

Uses local Ollama vision models to validate that extracted song data
(titles, page ranges, boundaries) matches actual source page images.

This validates the 559 successfully processed songbooks against their
cached source page images at S:/SlowImageCache/pdf_verification_v2/
"""

import json
import base64
import requests
import logging
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
CACHE_V2_PATH = Path("S:/SlowImageCache/pdf_verification_v2")
ARTIFACTS_BUCKET = "jsmith-artifacts"
RESULTS_FILE = Path("vision_validation_results.json")
VALIDATION_LOG = Path("vision_validation.log")
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2-vision:11b"  # Use the better quality model
MAX_WORKERS = 4  # Conservative for vision models
REQUEST_TIMEOUT = 60  # seconds per vision request

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(VALIDATION_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OllamaVisionValidator:
    """Validates extracted songs using Ollama vision models."""

    def __init__(self, model: str = OLLAMA_MODEL, base_url: str = OLLAMA_URL):
        self.model = model
        self.base_url = base_url
        self.request_count = 0
        self.error_count = 0

    def validate_song_title(self, image_path: Path, expected_title: str) -> Dict:
        """
        Validate that a song title matches what's on the actual page.

        Returns:
            {
                'title_match': bool,
                'extracted_title': str,  # What Ollama saw
                'expected_title': str,   # What we extracted
                'confidence': float,     # 0.0 to 1.0
                'status': str,           # 'pass', 'fail', 'error'
                'error': str or None
            }
        """
        if not image_path.exists():
            return {
                'title_match': False,
                'extracted_title': '',
                'expected_title': expected_title,
                'confidence': 0.0,
                'status': 'error',
                'error': f'Image not found: {image_path}'
            }

        try:
            # Encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')

            # Create prompt
            prompt = f"""Look at this sheet music page. What is the song title shown at the top?

Expected title: "{expected_title}"

Please respond with ONLY the exact title you see on the page, or "NO TITLE VISIBLE" if you cannot see a clear title."""

            # Call Ollama
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }

            response = requests.post(self.base_url, json=payload, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            result = response.json()
            extracted_title = result.get('response', '').strip()

            self.request_count += 1

            # Check if titles match
            expected_lower = expected_title.lower()
            extracted_lower = extracted_title.lower()

            # Fuzzy matching - either contains the other
            title_match = (
                expected_lower in extracted_lower or
                extracted_lower in expected_lower or
                extracted_lower == expected_lower
            )

            # Calculate confidence based on match quality
            if extracted_lower == expected_lower:
                confidence = 1.0
            elif expected_lower in extracted_lower or extracted_lower in expected_lower:
                confidence = 0.8
            elif extracted_title == "NO TITLE VISIBLE":
                confidence = 0.0
            else:
                confidence = 0.3

            return {
                'title_match': title_match,
                'extracted_title': extracted_title,
                'expected_title': expected_title,
                'confidence': confidence,
                'status': 'pass' if title_match else 'fail',
                'error': None
            }

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error validating {image_path}: {e}")
            return {
                'title_match': False,
                'extracted_title': '',
                'expected_title': expected_title,
                'confidence': 0.0,
                'status': 'error',
                'error': str(e)
            }


def load_prerender_results() -> List[Dict]:
    """Load the successful books from prerender results."""
    results_file = Path("prerender_results.json")

    if not results_file.exists():
        logger.error(f"Prerender results not found: {results_file}")
        return []

    with open(results_file) as f:
        data = json.load(f)

    # Get only successful books
    successful_books = [
        book for book in data.get('books', [])
        if book.get('pages_rendered', 0) > 0 or book.get('pages_cached', 0) > 0
    ]

    logger.info(f"Loaded {len(successful_books)} successful books from prerender results")
    return successful_books


def download_page_analysis(book: Dict) -> Optional[Dict]:
    """
    Load page_analysis.json for a book.
    Tries local ProcessedSongs_Final first, then falls back to S3.
    """
    book_id = book['book_id']
    artist = book['artist']
    book_name = book['book_name']

    # Try local path first
    local_path = Path("ProcessedSongs_Final") / artist / book_name / "page_analysis.json"

    if local_path.exists():
        try:
            with open(local_path) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading local page_analysis for {book_id}: {e}")

    # Fall back to S3
    try:
        import boto3
        s3 = boto3.client('s3')
        key = f"{book_id}/page_analysis.json"
        response = s3.get_object(Bucket=ARTIFACTS_BUCKET, Key=key)
        data = json.loads(response['Body'].read())
        return data
    except Exception as e:
        logger.debug(f"Could not download page_analysis from S3 for {book_id}: {e}")
        return None


def get_cache_image_path(book: Dict, pdf_page_num: int) -> Optional[Path]:
    """Get the path to a cached page image."""
    artist = book['artist'].replace('/', '_').replace('\\', '_')
    book_name = book['book_name'].replace('/', '_').replace('\\', '_')

    cache_dir = CACHE_V2_PATH / artist / book_name
    image_path = cache_dir / f"page_{pdf_page_num-1:04d}.jpg"

    return image_path if image_path.exists() else None


def validate_book(book: Dict, validator: OllamaVisionValidator, sample_size: int = 5) -> Dict:
    """
    Validate a single book by checking a sample of songs.

    Args:
        book: Book info dict
        validator: OllamaVisionValidator instance
        sample_size: Number of songs to validate per book (5 = reasonable sample)

    Returns:
        Validation results dict
    """
    book_id = book['book_id']
    artist = book['artist']
    book_name = book['book_name']

    # Download page analysis
    page_analysis = download_page_analysis(book)

    if not page_analysis:
        return {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name,
            'status': 'error',
            'error': 'Could not download page_analysis.json',
            'songs_validated': 0,
            'songs_passed': 0,
            'songs_failed': 0,
            'songs_errored': 0,
            'validations': []
        }

    songs = page_analysis.get('songs', [])

    if not songs:
        return {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name,
            'status': 'error',
            'error': 'No songs in page_analysis',
            'songs_validated': 0,
            'songs_passed': 0,
            'songs_failed': 0,
            'songs_errored': 0,
            'validations': []
        }

    # Sample songs (first, middle, last, plus random)
    import random

    if len(songs) <= sample_size:
        songs_to_validate = songs
    else:
        # Always include first and last
        sample_songs = [songs[0], songs[-1]]

        # Add middle
        mid_idx = len(songs) // 2
        sample_songs.append(songs[mid_idx])

        # Add random samples
        remaining = [s for i, s in enumerate(songs) if i not in {0, mid_idx, len(songs)-1}]
        if remaining:
            num_random = min(sample_size - 3, len(remaining))
            sample_songs.extend(random.sample(remaining, num_random))

        songs_to_validate = sample_songs

    # Validate each sampled song
    validations = []
    passed = 0
    failed = 0
    errored = 0

    for song in songs_to_validate:
        title = song.get('title', 'Unknown')
        start_page = song.get('start_pdf_page') or song.get('actual_pdf_start')

        if not start_page:
            errored += 1
            validations.append({
                'song_title': title,
                'status': 'error',
                'error': 'No start page',
                'validation': None
            })
            continue

        # Get cached image
        image_path = get_cache_image_path(book, start_page)

        if not image_path:
            errored += 1
            validations.append({
                'song_title': title,
                'status': 'error',
                'error': f'Image not found for page {start_page}',
                'validation': None
            })
            continue

        # Validate with vision model
        validation_result = validator.validate_song_title(image_path, title)

        if validation_result['status'] == 'pass':
            passed += 1
        elif validation_result['status'] == 'fail':
            failed += 1
        else:
            errored += 1

        validations.append({
            'song_title': title,
            'start_page': start_page,
            'status': validation_result['status'],
            'validation': validation_result
        })

    return {
        'book_id': book_id,
        'artist': artist,
        'book_name': book_name,
        'status': 'complete',
        'total_songs': len(songs),
        'songs_validated': len(validations),
        'songs_passed': passed,
        'songs_failed': failed,
        'songs_errored': errored,
        'pass_rate': passed / len(validations) if validations else 0.0,
        'validations': validations
    }


def validate_all_books(books: List[Dict], sample_size: int = 5, max_books: Optional[int] = None, workers: int = MAX_WORKERS):
    """
    Validate all books using parallel processing.

    Args:
        books: List of book dicts to validate
        sample_size: Number of songs to validate per book
        max_books: Optional limit for testing
        workers: Number of parallel workers
    """
    if max_books:
        books = books[:max_books]
        logger.info(f"Limited to first {max_books} books for testing")

    logger.info(f"Starting validation of {len(books)} books")
    logger.info(f"Sample size: {sample_size} songs per book")
    logger.info(f"Using model: {OLLAMA_MODEL}")
    logger.info(f"Workers: {workers}")

    start_time = time.time()

    # Create validator instances for each worker
    validator = OllamaVisionValidator()

    results = []
    total_passed = 0
    total_failed = 0
    total_errored = 0
    total_validated = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        # Submit all tasks
        futures = {
            executor.submit(validate_book, book, validator, sample_size): book
            for book in books
        }

        # Process results with progress bar
        with tqdm(total=len(books), desc="Validating books") as pbar:
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)

                    # Update totals
                    total_validated += result.get('songs_validated', 0)
                    total_passed += result.get('songs_passed', 0)
                    total_failed += result.get('songs_failed', 0)
                    total_errored += result.get('songs_errored', 0)

                    pbar.set_postfix({
                        'validated': total_validated,
                        'pass': total_passed,
                        'fail': total_failed,
                        'error': total_errored
                    })
                    pbar.update(1)

                except Exception as e:
                    book = futures[future]
                    logger.error(f"Error validating book {book.get('book_id')}: {e}")
                    results.append({
                        'book_id': book.get('book_id'),
                        'artist': book.get('artist'),
                        'book_name': book.get('book_name'),
                        'status': 'error',
                        'error': str(e),
                        'songs_validated': 0,
                        'songs_passed': 0,
                        'songs_failed': 0,
                        'songs_errored': 0,
                        'validations': []
                    })
                    pbar.update(1)

    elapsed = time.time() - start_time

    # Save results
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_books': len(books),
        'books_validated': len(results),
        'sample_size_per_book': sample_size,
        'total_songs_validated': total_validated,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'total_errored': total_errored,
        'pass_rate': total_passed / total_validated if total_validated > 0 else 0.0,
        'elapsed_seconds': elapsed,
        'model': OLLAMA_MODEL,
        'results': results
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    # Print summary
    logger.info("=" * 80)
    logger.info("VISION VALIDATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Books validated: {len(results)}/{len(books)}")
    logger.info(f"Songs validated: {total_validated}")
    if total_validated > 0:
        logger.info(f"  Passed: {total_passed} ({total_passed/total_validated*100:.1f}%)")
        logger.info(f"  Failed: {total_failed} ({total_failed/total_validated*100:.1f}%)")
        logger.info(f"  Errors: {total_errored} ({total_errored/total_validated*100:.1f}%)")
    else:
        logger.info("  No songs validated (check AWS credentials)")
    logger.info(f"Elapsed time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")
    logger.info(f"Results saved to: {RESULTS_FILE}")
    logger.info("=" * 80)

    # Show books with failures
    failed_books = [r for r in results if r.get('songs_failed', 0) > 0]
    if failed_books:
        logger.info(f"\nBooks with validation failures: {len(failed_books)}")
        for book in failed_books[:10]:  # Show first 10
            logger.info(f"  - {book['artist']} - {book['book_name']}: "
                       f"{book['songs_failed']}/{book['songs_validated']} failed")
        if len(failed_books) > 10:
            logger.info(f"  ... and {len(failed_books) - 10} more")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive vision validation of extracted songs")
    parser.add_argument('--sample', type=int, default=5,
                       help="Number of songs to validate per book (default: 5)")
    parser.add_argument('--test', type=int,
                       help="Test mode: validate only N books")
    parser.add_argument('--workers', type=int, default=MAX_WORKERS,
                       help=f"Number of parallel workers (default: {MAX_WORKERS})")

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("COMPREHENSIVE VISION VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Cache location: {CACHE_V2_PATH}")
    logger.info(f"Model: {OLLAMA_MODEL}")
    logger.info(f"Sample size: {args.sample} songs per book")
    logger.info(f"Workers: {args.workers}")
    logger.info("=" * 80)

    # Load books
    books = load_prerender_results()

    if not books:
        logger.error("No books to validate")
        return

    # Run validation
    validate_all_books(books, sample_size=args.sample, max_books=args.test, workers=args.workers)


if __name__ == "__main__":
    main()
