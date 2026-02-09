"""
V3 Batch Pipeline Runner

Runs the V3 pipeline for multiple books under a single artist.
Processes books sequentially, logging results and continuing on failure.

Usage:
    python scripts/run_v3_batch.py --artist "Billy Joel"
    python scripts/run_v3_batch.py --artist "Billy Joel" --skip "My Lives"
    python scripts/run_v3_batch.py --artist "Billy Joel" --only "52nd Street,Glass Houses"
    python scripts/run_v3_batch.py --artist "Billy Joel" --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
PYTHON = sys.executable


def get_books_for_artist(artist: str) -> list:
    """Find all book PDFs for an artist in SheetMusic_Input."""
    artist_dir = INPUT_DIR / artist
    if not artist_dir.exists():
        print(f"ERROR: Artist directory not found: {artist_dir}")
        sys.exit(1)

    books = []
    prefix = f"{artist} - "
    for pdf in sorted(artist_dir.glob("*.pdf")):
        name = pdf.stem
        if name.startswith(prefix):
            book_name = name[len(prefix):]
            books.append({
                'book_name': book_name,
                'file_name': pdf.name,
                'file_size_mb': pdf.stat().st_size / 1024 / 1024,
            })
    return books


def run_single_book(artist: str, book_name: str, max_workers: int = 1) -> dict:
    """Run the V3 pipeline for a single book. Returns result dict."""
    cmd = [
        PYTHON, '-u',
        str(PROJECT_ROOT / 'scripts' / 'run_v3_single_book.py'),
        '--artist', artist,
        '--book', book_name,
        '--max-workers', str(max_workers),
    ]

    start_time = time.time()
    print(f"\n{'='*70}")
    print(f"  STARTING: {artist} - {book_name}")
    print(f"  Time: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*70}\n")

    try:
        # Stream output in real-time (no capture_output)
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # line-buffered
        )
        stderr_lines = []
        for line in proc.stdout:
            line = line.rstrip('\n')
            print(f"  {line}", flush=True)
            stderr_lines.append(line)

        proc.wait(timeout=3600)
        duration = time.time() - start_time

        if proc.returncode == 0:
            return {
                'book_name': book_name,
                'status': 'success',
                'duration_sec': round(duration, 1),
                'duration_min': round(duration / 60, 1),
            }
        else:
            return {
                'book_name': book_name,
                'status': 'failed',
                'duration_sec': round(duration, 1),
                'error': '\n'.join(stderr_lines[-20:]),
            }
    except subprocess.TimeoutExpired:
        proc.kill()
        duration = time.time() - start_time
        return {
            'book_name': book_name,
            'status': 'timeout',
            'duration_sec': round(duration, 1),
            'error': 'Exceeded 1 hour timeout',
        }
    except Exception as e:
        duration = time.time() - start_time
        return {
            'book_name': book_name,
            'status': 'error',
            'duration_sec': round(duration, 1),
            'error': str(e),
        }


def main():
    parser = argparse.ArgumentParser(description='V3 Batch Pipeline Runner')
    parser.add_argument('--artist', required=True, help='Artist name')
    parser.add_argument('--skip', help='Comma-separated book names to skip')
    parser.add_argument('--only', help='Comma-separated book names to process (only these)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would run')
    parser.add_argument('--max-workers', type=int, default=1,
                        help='Parallel Bedrock vision calls for page analysis (default: 1)')
    args = parser.parse_args()

    artist = args.artist
    skip_books = set(b.strip() for b in args.skip.split(',')) if args.skip else set()
    only_books = set(b.strip() for b in args.only.split(',')) if args.only else None

    # Discover books
    all_books = get_books_for_artist(artist)
    print(f"\nFound {len(all_books)} books for {artist}:")
    for b in all_books:
        print(f"  {b['file_size_mb']:7.1f} MB  {b['book_name']}")

    # Filter
    books_to_run = []
    for b in all_books:
        name = b['book_name']
        if name in skip_books:
            print(f"  SKIP (--skip): {name}")
            continue
        if only_books and name not in only_books:
            print(f"  SKIP (--only): {name}")
            continue
        books_to_run.append(b)

    print(f"\nWill process {len(books_to_run)} books:")
    total_mb = 0
    for b in books_to_run:
        print(f"  {b['file_size_mb']:7.1f} MB  {b['book_name']}")
        total_mb += b['file_size_mb']
    print(f"  {'':>7}     Total: {total_mb:.0f} MB")

    if args.dry_run:
        print("\n[DRY RUN] No processing performed.")
        return

    # Process each book
    batch_start = time.time()
    results = []

    for i, book in enumerate(books_to_run):
        print(f"\n{'#'*70}")
        print(f"  BOOK {i+1} of {len(books_to_run)}: {book['book_name']} ({book['file_size_mb']:.1f} MB)")
        print(f"{'#'*70}")

        result = run_single_book(artist, book['book_name'], max_workers=args.max_workers)
        result['file_size_mb'] = book['file_size_mb']
        results.append(result)

        # Print running summary
        succeeded = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] != 'success')
        print(f"\n  Progress: {i+1}/{len(books_to_run)} | Success: {succeeded} | Failed: {failed}")

    # Final summary
    batch_duration = time.time() - batch_start
    print(f"\n{'='*70}")
    print(f"  BATCH COMPLETE")
    print(f"{'='*70}")
    print(f"  Artist:   {artist}")
    print(f"  Books:    {len(results)}")
    print(f"  Duration: {batch_duration/60:.1f} min ({batch_duration/3600:.1f} hr)")
    print(f"")

    succeeded = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']

    if succeeded:
        print(f"  SUCCEEDED ({len(succeeded)}):")
        for r in succeeded:
            print(f"    {r['duration_min']:6.1f} min  {r['book_name']}")

    if failed:
        print(f"\n  FAILED ({len(failed)}):")
        for r in failed:
            err = r.get('error', 'Unknown')[:80]
            print(f"    [{r['status']}] {r['book_name']}: {err}")

    # Save results to file
    results_file = PROJECT_ROOT / 'SheetMusic_Artifacts' / artist / 'batch_results.json'
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump({
            'artist': artist,
            'batch_started': datetime.now().isoformat(),
            'total_duration_sec': round(batch_duration, 1),
            'books_processed': len(results),
            'books_succeeded': len(succeeded),
            'books_failed': len(failed),
            'results': results,
        }, f, indent=2)
    print(f"\n  Results saved to: {results_file}")


if __name__ == '__main__':
    main()
