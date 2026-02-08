"""
Batch reprocess all songbooks through the improved pipeline.

Usage:
    py scripts/reprocessing/batch_reprocess_all.py --dry-run           # See what would be processed
    py scripts/reprocessing/batch_reprocess_all.py --limit 10          # Process first 10 books
    py scripts/reprocessing/batch_reprocess_all.py --artist "Beatles"  # Process specific artist
    py scripts/reprocessing/batch_reprocess_all.py --all               # Process ALL books
    py scripts/reprocessing/batch_reprocess_all.py --status            # Check running executions

Options:
    --dry-run       Show what would be processed without starting executions
    --limit N       Only process first N books
    --artist NAME   Only process books by this artist (case-insensitive partial match)
    --all           Process all books (required to process everything)
    --force         Force reprocess even if book has existing artifacts
    --delay N       Delay between executions in seconds (default: 0.5)
    --status        Show status of recent executions
    --concurrency N Max concurrent executions (default: 50)
"""
import sys
import json
import boto3
import time
import argparse
from datetime import datetime, timedelta
from collections import defaultdict

# AWS clients
stepfunctions = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

# Configuration
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'


def get_all_books():
    """Get all books from DynamoDB ledger."""
    print("Scanning DynamoDB ledger...")
    books = []
    response = TABLE.scan()
    books.extend(response.get('Items', []))

    while 'LastEvaluatedKey' in response:
        response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        books.extend(response.get('Items', []))

    print(f"  Found {len(books)} books")
    return books


def clear_old_artifacts(book_id: str) -> int:
    """Clear old artifacts before reprocessing."""
    artifacts_prefix = f"artifacts/{book_id}/"
    deleted_count = 0
    paginator = s3.get_paginator('list_objects_v2')

    try:
        for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=artifacts_prefix):
            if 'Contents' not in page:
                continue

            objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]

            if objects_to_delete:
                s3.delete_objects(
                    Bucket=OUTPUT_BUCKET,
                    Delete={'Objects': objects_to_delete}
                )
                deleted_count += len(objects_to_delete)
    except Exception as e:
        print(f"  Warning: Error clearing artifacts: {e}")

    return deleted_count


def get_local_source_pdf_path(book: dict) -> str:
    """Get local source PDF path from book info."""
    artist = book.get('artist', '')
    book_name = book.get('book_name', '')

    if not artist or not book_name:
        return None

    # Build expected path: SheetMusic/<Artist>/<Artist> - <Book Name>.pdf
    from pathlib import Path
    local_path = Path('SheetMusic') / artist / f"{artist} - {book_name}.pdf"

    if local_path.exists():
        return str(local_path)

    # Try without .pdf (some might have different extension)
    for ext in ['.pdf', '.PDF']:
        path = Path('SheetMusic') / artist / f"{artist} - {book_name}{ext}"
        if path.exists():
            return str(path)

    # Try to find any PDF with book_name in the artist folder
    artist_folder = Path('SheetMusic') / artist
    if artist_folder.exists():
        for pdf in artist_folder.glob('*.pdf'):
            if book_name.lower() in pdf.stem.lower():
                return str(pdf)

    return None


def upload_source_pdf_if_needed(local_path: str) -> str:
    """Upload source PDF to S3 if not already there. Returns S3 key."""
    from pathlib import Path
    local_path = Path(local_path)

    # Build S3 key from local path
    # SheetMusic/Artist/Artist - Book.pdf -> Artist/Artist - Book.pdf
    parts = local_path.parts
    try:
        sheetmusic_idx = parts.index('SheetMusic')
        s3_key = '/'.join(parts[sheetmusic_idx + 1:])
    except ValueError:
        s3_key = local_path.name

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


def check_source_pdf_exists(book: dict) -> tuple:
    """Check if source PDF exists locally or in S3. Returns (exists, local_path)."""
    # First check local
    local_path = get_local_source_pdf_path(book)
    if local_path:
        return True, local_path

    # Fallback: check S3 directly
    source_pdf_uri = book.get('source_pdf_uri', '')
    if not source_pdf_uri:
        return False, None

    # Parse S3 URI
    if source_pdf_uri.startswith('s3://'):
        parts = source_pdf_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ''
    else:
        bucket = INPUT_BUCKET
        key = source_pdf_uri

    try:
        s3.head_object(Bucket=bucket, Key=key)
        return True, None  # In S3 but not local
    except:
        return False, None


def start_execution(book: dict, local_path: str = None, force: bool = True) -> dict:
    """Start a Step Functions execution for a book."""
    book_id = book.get('book_id')
    artist = book.get('artist', 'Unknown')
    book_name = book.get('book_name', 'Unknown')

    # Upload source PDF if we have a local path
    if local_path:
        s3_key = upload_source_pdf_if_needed(local_path)
        source_pdf_uri = f's3://{INPUT_BUCKET}/{s3_key}'
    else:
        source_pdf_uri = book.get('source_pdf_uri', '')

    # Clear old artifacts if force is True
    if force:
        clear_old_artifacts(book_id)

    # Prepare execution input
    execution_input = {
        'book_id': book_id,
        'source_pdf_uri': source_pdf_uri,
        'artist': artist,
        'book_name': book_name,
        'force_reprocess': force,
        'use_manual_splits': False,
        'manual_splits_path': None
    }

    # Start execution
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f'batch-{book_id}-{int(time.time())}',
        input=json.dumps(execution_input)
    )

    return {
        'book_id': book_id,
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
            PaginationConfig={'MaxItems': 100}
        ):
            for ex in page.get('executions', []):
                # Filter by time
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
            # Extract book_id from name like "batch-abc123-1234567890"
            parts = name.split('-')
            book_id = parts[1] if len(parts) >= 2 else name
            duration = datetime.now(ex['startDate'].tzinfo) - ex['startDate']
            print(f"  {book_id}: running for {duration.seconds // 60}m {duration.seconds % 60}s")
        if len(executions['RUNNING']) > 10:
            print(f"  ... and {len(executions['RUNNING']) - 10} more")

    if executions['FAILED']:
        print(f"\nRecent failures ({len(executions['FAILED'])}):")
        for ex in executions['FAILED'][:5]:
            name = ex['name']
            parts = name.split('-')
            book_id = parts[1] if len(parts) >= 2 else name
            print(f"  {book_id}")
        if len(executions['FAILED']) > 5:
            print(f"  ... and {len(executions['FAILED']) - 5} more")


def main():
    parser = argparse.ArgumentParser(description='Batch reprocess songbooks through the pipeline')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed')
    parser.add_argument('--limit', type=int, help='Only process first N books')
    parser.add_argument('--artist', type=str, help='Only process books by this artist')
    parser.add_argument('--all', action='store_true', help='Process all books')
    parser.add_argument('--force', action='store_true', default=True, help='Force reprocess (default: True)')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between executions in seconds')
    parser.add_argument('--status', action='store_true', help='Show status of recent executions')
    parser.add_argument('--concurrency', type=int, default=50, help='Max concurrent executions')

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    # Get all books
    books = get_all_books()

    # Filter books
    if args.artist:
        artist_filter = args.artist.lower()
        books = [b for b in books if artist_filter in b.get('artist', '').lower()]
        print(f"  Filtered to {len(books)} books for artist matching '{args.artist}'")

    # Check source PDFs exist (locally or in S3)
    valid_books = []
    missing_source = []
    for book in books:
        exists, local_path = check_source_pdf_exists(book)
        if exists:
            book['_local_path'] = local_path  # Store for later use
            valid_books.append(book)
        else:
            missing_source.append(book)

    local_count = sum(1 for b in valid_books if b.get('_local_path'))
    s3_count = len(valid_books) - local_count
    print(f"  {len(valid_books)} books have source PDFs ({local_count} local, {s3_count} in S3)")
    if missing_source:
        print(f"  {len(missing_source)} books missing source PDFs (will be skipped)")
        if args.dry_run:
            print("  Missing books:")
            for b in missing_source[:10]:
                print(f"    - {b.get('artist')} - {b.get('book_name')}")
            if len(missing_source) > 10:
                print(f"    ... and {len(missing_source) - 10} more")

    books = valid_books

    # Apply limit
    if args.limit:
        books = books[:args.limit]
        print(f"  Limited to {len(books)} books")

    # Safety check
    if not args.all and not args.limit and not args.artist and not args.dry_run:
        print("\n*** SAFETY: Must specify --all, --limit, --artist, or --dry-run ***")
        print("Use --dry-run to see what would be processed")
        sys.exit(1)

    # Group by artist for display
    by_artist = defaultdict(list)
    for book in books:
        by_artist[book.get('artist', 'Unknown')].append(book)

    print(f"\n" + "="*80)
    print(f"BOOKS TO PROCESS: {len(books)}")
    print("="*80)

    for artist in sorted(by_artist.keys()):
        artist_books = by_artist[artist]
        print(f"\n{artist} ({len(artist_books)} books):")
        for book in artist_books[:5]:
            print(f"  - {book.get('book_name', 'Unknown')}")
        if len(artist_books) > 5:
            print(f"  ... and {len(artist_books) - 5} more")

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
            local_path = book.get('_local_path')
            result = start_execution(book, local_path=local_path, force=args.force)
            started.append(result)
            print(f"  [{i+1}/{len(books)}] Started: {book.get('artist')} - {book.get('book_name')}")

            # Rate limiting
            if args.delay > 0 and i < len(books) - 1:
                time.sleep(args.delay)

        except Exception as e:
            failed.append({'book': book, 'error': str(e)})
            print(f"  [{i+1}/{len(books)}] FAILED: {book.get('artist')} - {book.get('book_name')}: {e}")

    # Summary
    print(f"\n" + "="*80)
    print("BATCH COMPLETE")
    print("="*80)
    print(f"  Started: {len(started)}")
    print(f"  Failed:  {len(failed)}")

    # Save execution ARNs for tracking
    if started:
        log_file = f'batch_executions_{int(time.time())}.json'
        with open(log_file, 'w') as f:
            json.dump({
                'started_at': datetime.now().isoformat(),
                'total': len(started),
                'executions': started
            }, f, indent=2)
        print(f"\nExecution log saved to: {log_file}")

    print(f"\nUse --status to monitor progress")


if __name__ == '__main__':
    main()
