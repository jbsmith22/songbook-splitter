"""
Process ALL local PDFs through the new pipeline from scratch.

Ignores existing DynamoDB entries - creates new book_ids with a 'v2-' prefix
to distinguish from old pipeline runs.

Usage:
    py scripts/reprocessing/process_all_fresh.py --dry-run    # See what would be processed
    py scripts/reprocessing/process_all_fresh.py --limit 10   # Process first 10
    py scripts/reprocessing/process_all_fresh.py --all        # Process everything
    py scripts/reprocessing/process_all_fresh.py --status     # Check running executions
"""
import sys
import json
import boto3
import time
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

# AWS clients
stepfunctions = boto3.client('stepfunctions')
s3 = boto3.client('s3')

# Configuration
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
SHEETMUSIC_DIR = Path('SheetMusic')
BOOK_ID_PREFIX = 'v2-'  # Prefix to distinguish from old pipeline


def generate_book_id(pdf_path: Path) -> str:
    """Generate a unique book_id from the PDF path."""
    # Use hash of the relative path (normalized to forward slashes) for consistency
    rel_path = str(pdf_path.relative_to(SHEETMUSIC_DIR)).replace('\\', '/')
    hash_val = hashlib.md5(rel_path.encode()).hexdigest()[:16]
    return f"{BOOK_ID_PREFIX}{hash_val}"


def parse_pdf_path(pdf_path: Path) -> dict:
    """Extract artist and book_name from PDF path."""
    # Path format: SheetMusic/Artist/Artist - Book Name.pdf
    rel_path = pdf_path.relative_to(SHEETMUSIC_DIR)
    parts = rel_path.parts

    if len(parts) >= 2:
        artist = parts[0]
        filename = pdf_path.stem  # Without .pdf

        # Try to extract book name from "Artist - Book Name" format
        if ' - ' in filename:
            book_name = filename.split(' - ', 1)[1]
        else:
            book_name = filename
    else:
        artist = 'Unknown'
        book_name = pdf_path.stem

    return {
        'artist': artist,
        'book_name': book_name,
        'filename': pdf_path.name,
        'rel_path': str(rel_path).replace('\\', '/')  # S3 needs forward slashes
    }


def scan_local_pdfs() -> list:
    """Scan SheetMusic folder for all PDFs."""
    print(f"Scanning {SHEETMUSIC_DIR} for PDFs...")
    pdfs = list(SHEETMUSIC_DIR.glob('**/*.pdf'))
    pdfs.extend(SHEETMUSIC_DIR.glob('**/*.PDF'))

    # Remove duplicates (case-insensitive on Windows)
    seen = set()
    unique_pdfs = []
    for pdf in pdfs:
        key = str(pdf).lower()
        if key not in seen:
            seen.add(key)
            unique_pdfs.append(pdf)

    print(f"  Found {len(unique_pdfs)} PDFs")
    return sorted(unique_pdfs)


def clear_old_artifacts(book_id: str) -> int:
    """Clear old artifacts for a book."""
    artifacts_prefix = f"artifacts/{book_id}/"
    deleted_count = 0

    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=artifacts_prefix):
            if 'Contents' not in page:
                continue
            objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
            if objects_to_delete:
                s3.delete_objects(Bucket=OUTPUT_BUCKET, Delete={'Objects': objects_to_delete})
                deleted_count += len(objects_to_delete)
    except Exception as e:
        print(f"  Warning: Error clearing artifacts: {e}")

    return deleted_count


def start_execution(pdf_path: Path, book_id: str, info: dict) -> dict:
    """Start a Step Functions execution for a PDF."""
    # Build S3 key (already uploaded)
    s3_key = info['rel_path']
    source_pdf_uri = f's3://{INPUT_BUCKET}/{s3_key}'

    # Clear any old artifacts
    clear_old_artifacts(book_id)

    # Prepare execution input
    execution_input = {
        'book_id': book_id,
        'source_pdf_uri': source_pdf_uri,
        'artist': info['artist'],
        'book_name': info['book_name'],
        'force_reprocess': True,
        'use_manual_splits': False,
        'manual_splits_path': None
    }

    # Start execution
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f'{book_id}-{int(time.time())}',
        input=json.dumps(execution_input)
    )

    return {
        'book_id': book_id,
        'artist': info['artist'],
        'book_name': info['book_name'],
        'execution_arn': response['executionArn'],
        'start_date': response['startDate'].isoformat()
    }


def get_running_executions():
    """Get list of running Step Functions executions."""
    running = []
    paginator = stepfunctions.get_paginator('list_executions')

    for page in paginator.paginate(
        stateMachineArn=STATE_MACHINE_ARN,
        statusFilter='RUNNING'
    ):
        running.extend(page.get('executions', []))

    return running


def get_recent_executions(hours: int = 24):
    """Get executions from the last N hours."""
    executions = {'RUNNING': [], 'SUCCEEDED': [], 'FAILED': [], 'TIMED_OUT': [], 'ABORTED': []}

    for status in executions.keys():
        try:
            paginator = stepfunctions.get_paginator('list_executions')
            for page in paginator.paginate(
                stateMachineArn=STATE_MACHINE_ARN,
                statusFilter=status,
                PaginationConfig={'MaxItems': 200}
            ):
                for ex in page.get('executions', []):
                    start_time = ex['startDate']
                    if start_time > datetime.now(start_time.tzinfo) - timedelta(hours=hours):
                        executions[status].append(ex)
        except:
            pass

    return executions


def show_status():
    """Show status of recent executions."""
    print("\n" + "="*80)
    print("STEP FUNCTIONS EXECUTION STATUS")
    print("="*80)

    executions = get_recent_executions(hours=24)

    total = sum(len(v) for v in executions.values())
    print(f"\nLast 24 hours ({total} total):")
    print(f"  RUNNING:   {len(executions['RUNNING'])}")
    print(f"  SUCCEEDED: {len(executions['SUCCEEDED'])}")
    print(f"  FAILED:    {len(executions['FAILED'])}")
    print(f"  TIMED_OUT: {len(executions['TIMED_OUT'])}")
    print(f"  ABORTED:   {len(executions['ABORTED'])}")

    # Count v2 executions
    v2_count = sum(1 for ex in executions['SUCCEEDED'] if ex['name'].startswith('v2-'))
    print(f"\n  New pipeline (v2-*): {v2_count} succeeded")

    if executions['RUNNING']:
        print(f"\nCurrently running ({len(executions['RUNNING'])}):")
        for ex in executions['RUNNING'][:10]:
            name = ex['name']
            duration = datetime.now(ex['startDate'].tzinfo) - ex['startDate']
            print(f"  {name}: {duration.seconds // 60}m {duration.seconds % 60}s")
        if len(executions['RUNNING']) > 10:
            print(f"  ... and {len(executions['RUNNING']) - 10} more")

    if executions['FAILED']:
        print(f"\nRecent failures ({len(executions['FAILED'])}):")
        for ex in executions['FAILED'][:5]:
            print(f"  {ex['name']}")
        if len(executions['FAILED']) > 5:
            print(f"  ... and {len(executions['FAILED']) - 5} more")


def main():
    parser = argparse.ArgumentParser(description='Process all local PDFs through new pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--limit', type=int, help='Only process first N books')
    parser.add_argument('--artist', type=str, help='Only process books by this artist')
    parser.add_argument('--exclude-prefix', type=str, help='Exclude folders starting with this prefix (e.g., "_")')
    parser.add_argument('--all', action='store_true', help='Process all books')
    parser.add_argument('--delay', type=float, default=0.3, help='Delay between executions (default: 0.3s)')
    parser.add_argument('--status', action='store_true', help='Show status of recent executions')
    parser.add_argument('--concurrency', type=int, default=100, help='Max concurrent executions (default: 100)')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Scan for PDFs
    pdfs = scan_local_pdfs()

    # Parse each PDF
    books = []
    for pdf in pdfs:
        info = parse_pdf_path(pdf)
        info['path'] = pdf
        info['book_id'] = generate_book_id(pdf)
        books.append(info)

    # Filter by exclude-prefix if specified
    if args.exclude_prefix:
        before = len(books)
        books = [b for b in books if not b['artist'].startswith(args.exclude_prefix)]
        print(f"  Excluded {before - len(books)} books with prefix '{args.exclude_prefix}' -> {len(books)} remaining")

    # Filter by artist if specified
    if args.artist:
        artist_filter = args.artist.lower()
        books = [b for b in books if artist_filter in b['artist'].lower()]
        print(f"  Filtered to {len(books)} books for artist matching '{args.artist}'")

    # Apply limit
    if args.limit:
        books = books[:args.limit]
        print(f"  Limited to {len(books)} books")

    # Safety check
    if not args.all and not args.limit and not args.artist and not args.dry_run:
        print("\n*** SAFETY: Must specify --all, --limit, --artist, or --dry-run ***")
        sys.exit(1)

    # Group by artist for display
    by_artist = defaultdict(list)
    for book in books:
        by_artist[book['artist']].append(book)

    print(f"\n" + "="*80)
    print(f"BOOKS TO PROCESS: {len(books)}")
    print(f"Book ID prefix: {BOOK_ID_PREFIX}")
    print("="*80)

    for artist in sorted(by_artist.keys())[:20]:
        artist_books = by_artist[artist]
        print(f"\n{artist} ({len(artist_books)} books):")
        for book in artist_books[:3]:
            print(f"  - {book['book_name']} [{book['book_id']}]")
        if len(artist_books) > 3:
            print(f"  ... and {len(artist_books) - 3} more")

    if len(by_artist) > 20:
        print(f"\n... and {len(by_artist) - 20} more artists")

    if args.dry_run:
        print("\n*** DRY RUN - No executions started ***")
        return

    # Check current running executions
    running = get_running_executions()
    print(f"\nCurrently running executions: {len(running)}")

    available_slots = args.concurrency - len(running)
    if available_slots <= 0:
        print(f"*** Max concurrency ({args.concurrency}) reached. Wait for executions to complete. ***")
        print("Use --status to check progress")
        sys.exit(1)

    if len(books) > available_slots:
        print(f"*** Will start {available_slots} of {len(books)} books (concurrency limit) ***")
        books = books[:available_slots]

    # Confirm
    print(f"\n*** Ready to start {len(books)} Step Functions executions ***")
    print(f"*** All books will get new '{BOOK_ID_PREFIX}' prefixed IDs ***")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Start executions
    print(f"\nStarting executions...")
    started = []
    failed = []

    for i, book in enumerate(books):
        try:
            result = start_execution(book['path'], book['book_id'], book)
            started.append(result)
            print(f"  [{i+1}/{len(books)}] Started: {book['artist']} - {book['book_name']}")

            # Rate limiting
            if args.delay > 0 and i < len(books) - 1:
                time.sleep(args.delay)

        except Exception as e:
            failed.append({'book': book, 'error': str(e)})
            print(f"  [{i+1}/{len(books)}] FAILED: {book['artist']} - {book['book_name']}: {e}")

    # Summary
    print(f"\n" + "="*80)
    print("BATCH COMPLETE")
    print("="*80)
    print(f"  Started: {len(started)}")
    print(f"  Failed:  {len(failed)}")

    # Save execution log
    if started:
        log_file = f'batch_v2_executions_{int(time.time())}.json'
        with open(log_file, 'w') as f:
            json.dump({
                'started_at': datetime.now().isoformat(),
                'book_id_prefix': BOOK_ID_PREFIX,
                'total': len(started),
                'executions': started
            }, f, indent=2)
        print(f"\nExecution log saved to: {log_file}")

    print(f"\nUse --status to monitor progress")


if __name__ == '__main__':
    main()
