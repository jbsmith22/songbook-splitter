"""
V3 Batch Pipeline Runner

Runs the V3 pipeline for multiple books, optionally in parallel.
Supports processing a single artist or all artists in SheetMusic_Input.

Parallelism strategy (based on load testing):
  - Bedrock throttle ceiling: ~50 concurrent vision calls (264 RPM burst)
  - Sustained load throttles at ~48 concurrent (8 books x 6 workers)
  - Default: 4 parallel books x 6 workers each = 24 concurrent calls
  - Vision workers retry with exponential backoff on throttling

Usage:
    # All books for one artist (parallel)
    python scripts/run_v3_batch.py --artist "Billy Joel"

    # All artists, all books
    python scripts/run_v3_batch.py --all

    # Subset
    python scripts/run_v3_batch.py --artist "Billy Joel" --only "52nd Street,Glass Houses"

    # Dry run to see what would process
    python scripts/run_v3_batch.py --all --dry-run

    # Tuning
    python scripts/run_v3_batch.py --all --parallel-books 4 --max-workers 12
"""

import argparse
import json
import os
import subprocess
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
PYTHON = sys.executable

# Lock for synchronized console output
print_lock = threading.Lock()


def sync_print(*args, **kwargs):
    """Thread-safe print."""
    with print_lock:
        print(*args, **kwargs, flush=True)


def get_books_for_artist(artist: str) -> list:
    """Find all book PDFs for an artist in SheetMusic_Input."""
    artist_dir = INPUT_DIR / artist
    if not artist_dir.exists():
        return []

    books = []
    prefix = f"{artist} - "
    for pdf in sorted(artist_dir.glob("*.pdf")):
        name = pdf.stem
        if name.startswith(prefix):
            book_name = name[len(prefix):]
            books.append({
                'artist': artist,
                'book_name': book_name,
                'file_name': pdf.name,
                'file_size_mb': pdf.stat().st_size / 1024 / 1024,
            })
    return books


def get_all_books() -> list:
    """Find all book PDFs across all artists."""
    all_books = []
    if not INPUT_DIR.exists():
        return all_books

    for artist_dir in sorted(INPUT_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        all_books.extend(get_books_for_artist(artist))

    return all_books


def is_already_processed(artist: str, book_name: str) -> bool:
    """Check if a book already has all 6 artifacts (skip if complete)."""
    book_dir = ARTIFACTS_DIR / artist / book_name
    if not book_dir.exists():
        return False

    expected = ['toc_discovery.json', 'toc_parse.json', 'page_analysis.json',
                'page_mapping.json', 'verified_songs.json', 'output_files.json']
    return all((book_dir / f).exists() for f in expected)


def run_single_book(artist: str, book_name: str, max_workers: int = 6,
                    book_num: int = 0, total_books: int = 0) -> dict:
    """Run the V3 pipeline for a single book. Returns result dict."""
    cmd = [
        PYTHON, '-u',
        str(PROJECT_ROOT / 'scripts' / 'run_v3_single_book.py'),
        '--artist', artist,
        '--book', book_name,
        '--max-workers', str(max_workers),
    ]

    label = f"[{book_num}/{total_books}]" if total_books > 0 else ""
    start_time = time.time()
    sync_print(f"\n{'='*70}")
    sync_print(f"  {label} STARTING: {artist} - {book_name}")
    sync_print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
    sync_print(f"{'='*70}\n")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        output_lines = []
        for line in proc.stdout:
            line = line.rstrip('\n')
            sync_print(f"  {label} {line}")
            output_lines.append(line)

        proc.wait(timeout=3600)
        duration = time.time() - start_time

        if proc.returncode == 0:
            sync_print(f"  {label} DONE: {artist} - {book_name} ({duration/60:.1f} min)")
            return {
                'artist': artist,
                'book_name': book_name,
                'status': 'success',
                'duration_sec': round(duration, 1),
                'duration_min': round(duration / 60, 1),
            }
        else:
            sync_print(f"  {label} FAILED: {artist} - {book_name}")
            return {
                'artist': artist,
                'book_name': book_name,
                'status': 'failed',
                'duration_sec': round(duration, 1),
                'error': '\n'.join(output_lines[-20:]),
            }
    except subprocess.TimeoutExpired:
        proc.kill()
        duration = time.time() - start_time
        return {
            'artist': artist,
            'book_name': book_name,
            'status': 'timeout',
            'duration_sec': round(duration, 1),
            'error': 'Exceeded 1 hour timeout',
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'artist': artist,
            'book_name': book_name,
            'status': 'error',
            'duration_sec': round(duration, 1),
            'error': str(e),
        }


def main():
    parser = argparse.ArgumentParser(description='V3 Batch Pipeline Runner')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--artist', help='Process all books for a single artist')
    group.add_argument('--all', action='store_true', help='Process all artists')

    parser.add_argument('--skip', help='Comma-separated book names to skip')
    parser.add_argument('--only', help='Comma-separated book names to process (only these)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would run')
    parser.add_argument('--force', action='store_true',
                        help='Re-process books even if all 6 artifacts exist')
    parser.add_argument('--parallel-books', type=int, default=4,
                        help='Number of books to process in parallel (default: 4)')
    parser.add_argument('--max-workers', type=int, default=6,
                        help='Parallel Bedrock vision calls per book (default: 6)')
    args = parser.parse_args()

    skip_books = set(b.strip() for b in args.skip.split(',')) if args.skip else set()
    only_books = set(b.strip() for b in args.only.split(',')) if args.only else None

    # Discover books
    if args.all:
        all_books = get_all_books()
        print(f"\nFound {len(all_books)} total books across all artists")
    else:
        all_books = get_books_for_artist(args.artist)
        print(f"\nFound {len(all_books)} books for {args.artist}")

    if not all_books:
        print("No books found!")
        sys.exit(1)

    # Filter
    books_to_run = []
    skipped_complete = 0
    for b in all_books:
        name = b['book_name']
        artist = b['artist']

        if name in skip_books:
            continue
        if only_books and name not in only_books:
            continue

        # Skip already-processed books unless --force
        if not args.force and is_already_processed(artist, name):
            skipped_complete += 1
            continue

        books_to_run.append(b)

    # Show plan
    total_conc = args.parallel_books * args.max_workers
    print(f"\nPlan:")
    print(f"  Books to process:    {len(books_to_run)}")
    print(f"  Already complete:    {skipped_complete} (skipped)")
    print(f"  Parallel books:      {args.parallel_books}")
    print(f"  Vision workers/book: {args.max_workers}")
    print(f"  Total concurrency:   {total_conc} Bedrock calls")

    if total_conc > 50:
        print(f"  WARNING: {total_conc} concurrent calls exceeds tested safe limit of 50")
        print(f"           Consider reducing --parallel-books or --max-workers")

    # Group by artist for display
    by_artist = {}
    for b in books_to_run:
        by_artist.setdefault(b['artist'], []).append(b)

    total_mb = sum(b['file_size_mb'] for b in books_to_run)
    print(f"\n  {len(by_artist)} artists, {len(books_to_run)} books, {total_mb:.0f} MB total")
    for artist, books in sorted(by_artist.items()):
        print(f"    {artist}: {len(books)} books")
        if len(books) <= 5:
            for b in books:
                print(f"      {b['file_size_mb']:6.1f} MB  {b['book_name']}")

    if args.dry_run:
        print("\n[DRY RUN] No processing performed.")
        return

    # Process books
    batch_start = time.time()
    results = []
    results_lock = threading.Lock()
    completed_count = [0]  # mutable counter

    def process_book(book, book_num):
        result = run_single_book(
            book['artist'], book['book_name'],
            max_workers=args.max_workers,
            book_num=book_num,
            total_books=len(books_to_run)
        )
        result['file_size_mb'] = book['file_size_mb']

        with results_lock:
            results.append(result)
            completed_count[0] += 1
            succeeded = sum(1 for r in results if r['status'] == 'success')
            failed = sum(1 for r in results if r['status'] != 'success')
            elapsed = time.time() - batch_start
            sync_print(f"\n  >>> Progress: {completed_count[0]}/{len(books_to_run)} | "
                       f"Success: {succeeded} | Failed: {failed} | "
                       f"Elapsed: {elapsed/60:.1f} min")
        return result

    if args.parallel_books <= 1:
        # Sequential mode
        for i, book in enumerate(books_to_run):
            process_book(book, i + 1)
    else:
        # Parallel mode
        with ThreadPoolExecutor(max_workers=args.parallel_books) as executor:
            futures = {}
            for i, book in enumerate(books_to_run):
                future = executor.submit(process_book, book, i + 1)
                futures[future] = book

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    book = futures[future]
                    sync_print(f"  EXCEPTION: {book['artist']} - {book['book_name']}: {e}")

    # Final summary
    batch_duration = time.time() - batch_start
    print(f"\n{'='*70}")
    print(f"  BATCH COMPLETE")
    print(f"{'='*70}")
    print(f"  Duration: {batch_duration/60:.1f} min ({batch_duration/3600:.1f} hr)")
    print(f"  Config:   {args.parallel_books} parallel books x {args.max_workers} workers")
    print()

    succeeded = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']

    print(f"  SUCCEEDED ({len(succeeded)}):")
    for r in sorted(succeeded, key=lambda x: x.get('duration_min', 0)):
        print(f"    {r.get('duration_min', 0):6.1f} min  {r['artist']} - {r['book_name']}")

    if failed:
        print(f"\n  FAILED ({len(failed)}):")
        for r in failed:
            err = r.get('error', 'Unknown')[:80]
            print(f"    [{r['status']}] {r['artist']} - {r['book_name']}: {err}")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    results_file = PROJECT_ROOT / 'SheetMusic_Artifacts' / f'batch_results_{timestamp}.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump({
            'batch_started': datetime.now().isoformat(),
            'config': {
                'parallel_books': args.parallel_books,
                'max_workers': args.max_workers,
                'total_concurrency': total_conc,
            },
            'total_duration_sec': round(batch_duration, 1),
            'books_processed': len(results),
            'books_succeeded': len(succeeded),
            'books_failed': len(failed),
            'results': results,
        }, f, indent=2)
    print(f"\n  Results saved to: {results_file}")


if __name__ == '__main__':
    main()
