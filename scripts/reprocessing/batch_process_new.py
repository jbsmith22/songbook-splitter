"""
Batch process NEW songbooks that haven't been run through the V2 pipeline yet.

Uses the v2 provenance database to find MISSING books and submits them.

Usage:
    py scripts/reprocessing/batch_process_new.py --dry-run           # See what would be processed
    py scripts/reprocessing/batch_process_new.py --limit 100         # Process first 100 books
    py scripts/reprocessing/batch_process_new.py --artist "Beatles"  # Process specific artist
    py scripts/reprocessing/batch_process_new.py --status            # Check running executions
"""
import sys
import json
import boto3
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# AWS clients
stepfunctions = boto3.client('stepfunctions')
s3 = boto3.client('s3')

# Configuration
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
SHEETMUSIC_DIR = Path('SheetMusic')
PROVENANCE_FILE = Path('data/analysis/v2_provenance_database.json')


def generate_book_id(source_path: str) -> str:
    """Generate a v2 book_id from the source path."""
    # Hash the path to create a unique ID
    path_hash = hashlib.md5(source_path.encode()).hexdigest()[:16]
    return f"v2-{path_hash}-2"


def get_missing_books():
    """Get all MISSING books from the v2 provenance database."""
    if not PROVENANCE_FILE.exists():
        print(f"ERROR: {PROVENANCE_FILE} not found. Run generate_v2_provenance.py first.")
        sys.exit(1)

    with open(PROVENANCE_FILE) as f:
        data = json.load(f)

    missing = [b for b in data['songbooks'] if b['verification']['status'] == 'MISSING']
    return missing


def upload_source_pdf(local_path: Path) -> str:
    """Upload source PDF to S3. Returns S3 key."""
    # Build S3 key from local path
    # SheetMusic/Artist/Artist - Book.pdf -> Artist/Artist - Book.pdf
    rel_path = local_path.relative_to(SHEETMUSIC_DIR)
    s3_key = str(rel_path).replace('\\', '/')

    # Check if already in S3
    try:
        s3.head_object(Bucket=INPUT_BUCKET, Key=s3_key)
        return s3_key  # Already exists
    except:
        pass

    # Upload
    print(f"    Uploading: {s3_key}")
    with open(local_path, 'rb') as f:
        s3.put_object(
            Bucket=INPUT_BUCKET,
            Key=s3_key,
            Body=f,
            ContentType='application/pdf'
        )

    return s3_key


def start_execution(book: dict) -> dict:
    """Start a Step Functions execution for a book."""
    source_pdf_path = book['source_pdf']['path']
    local_path = SHEETMUSIC_DIR / source_pdf_path

    # Parse artist and book name from path
    parts = Path(source_pdf_path).parts
    if len(parts) >= 2:
        artist = parts[0]
        filename = Path(source_pdf_path).stem
        if ' - ' in filename:
            book_name = filename.split(' - ', 1)[1]
        else:
            book_name = filename
    else:
        artist = 'Unknown'
        book_name = Path(source_pdf_path).stem

    # Generate book_id
    book_id = generate_book_id(source_pdf_path)

    # Upload source PDF
    s3_key = upload_source_pdf(local_path)
    source_pdf_uri = f's3://{INPUT_BUCKET}/{s3_key}'

    # Prepare execution input
    execution_input = {
        'book_id': book_id,
        'source_pdf_uri': source_pdf_uri,
        'artist': artist,
        'book_name': book_name,
        'force_reprocess': False,
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
        'source_pdf': source_pdf_path,
        'artist': artist,
        'book_name': book_name,
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

    return executions


def show_status():
    """Show status of recent executions."""
    print("\n" + "="*80)
    print("STEP FUNCTIONS EXECUTION STATUS")
    print("="*80)

    executions = get_recent_executions(hours=24)

    print(f"\nLast 24 hours:")
    print(f"  RUNNING:   {len(executions['RUNNING'])}")
    print(f"  SUCCEEDED: {len(executions['SUCCEEDED'])}")
    print(f"  FAILED:    {len(executions['FAILED'])}")
    print(f"  TIMED_OUT: {len(executions['TIMED_OUT'])}")
    print(f"  ABORTED:   {len(executions['ABORTED'])}")

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
    parser = argparse.ArgumentParser(description='Batch process NEW songbooks')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--limit', type=int, help='Only process first N books')
    parser.add_argument('--artist', type=str, help='Only process books by this artist')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between executions in seconds')
    parser.add_argument('--status', action='store_true', help='Show status of recent executions')
    parser.add_argument('--concurrency', type=int, default=50, help='Max concurrent executions')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Get MISSING books from provenance database
    print("Loading v2 provenance database...")
    books = get_missing_books()
    print(f"  Found {len(books)} MISSING books")

    # Filter by artist if specified
    if args.artist:
        artist_filter = args.artist.lower()
        books = [b for b in books if artist_filter in b['source_pdf']['path'].lower()]
        print(f"  Filtered to {len(books)} books for artist matching '{args.artist}'")

    # Check that source PDFs exist locally
    valid_books = []
    missing_local = []
    for book in books:
        local_path = SHEETMUSIC_DIR / book['source_pdf']['path']
        if local_path.exists():
            valid_books.append(book)
        else:
            missing_local.append(book)

    print(f"  {len(valid_books)} books have local source PDFs")
    if missing_local:
        print(f"  {len(missing_local)} books missing local PDFs (will be skipped)")

    books = valid_books

    # Apply limit
    if args.limit:
        books = books[:args.limit]
        print(f"  Limited to {len(books)} books")

    # Safety check
    if not args.limit and not args.artist and not args.dry_run:
        print("\n*** SAFETY: Must specify --limit, --artist, or --dry-run ***")
        print("Use --dry-run to see what would be processed")
        sys.exit(1)

    # Group by artist for display
    by_artist = defaultdict(list)
    for book in books:
        path = book['source_pdf']['path']
        artist = path.split('/')[0] if '/' in path else 'Unknown'
        by_artist[artist].append(book)

    print(f"\n" + "="*80)
    print(f"BOOKS TO PROCESS: {len(books)}")
    print("="*80)

    for artist in sorted(by_artist.keys()):
        artist_books = by_artist[artist]
        print(f"\n{artist} ({len(artist_books)} books):")
        for book in artist_books[:3]:
            print(f"  - {book['source_pdf']['path']}")
        if len(artist_books) > 3:
            print(f"  ... and {len(artist_books) - 3} more")

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
            result = start_execution(book)
            started.append(result)
            print(f"  [{i+1}/{len(books)}] Started: {result['artist']} - {result['book_name']}")

            # Rate limiting
            if args.delay > 0 and i < len(books) - 1:
                time.sleep(args.delay)

        except Exception as e:
            failed.append({'book': book, 'error': str(e)})
            print(f"  [{i+1}/{len(books)}] FAILED: {book['source_pdf']['path']}: {e}")

    # Summary
    print(f"\n" + "="*80)
    print("BATCH COMPLETE")
    print("="*80)
    print(f"  Started: {len(started)}")
    print(f"  Failed:  {len(failed)}")

    # Save execution log
    if started:
        log_file = f'batch_new_{int(time.time())}.json'
        with open(log_file, 'w') as f:
            json.dump({
                'started_at': datetime.now().isoformat(),
                'total': len(started),
                'executions': started
            }, f, indent=2)
        print(f"\nExecution log saved to: {log_file}")

    print(f"\nUse --status to monitor progress")
    print(f"After completion, run:")
    print(f"  py scripts/analysis/generate_v2_provenance.py")


if __name__ == '__main__':
    main()
