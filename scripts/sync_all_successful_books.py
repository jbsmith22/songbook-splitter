#!/usr/bin/env python3
"""
Sync all successful books from S3 to local ProcessedSongs_Final folder.
Works directly with DynamoDB to find successful books.
"""
import json
import boto3
import argparse
from pathlib import Path
from urllib.parse import unquote

# Configuration
OUTPUT_BUCKET = 'jsmith-output'
LOCAL_OUTPUT_DIR = Path('ProcessedSongs_Final')

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

def get_successful_books():
    """Get all successful V2 books from DynamoDB."""
    print("Scanning DynamoDB for successful V2 books...")
    books = []

    response = table.scan(
        FilterExpression='begins_with(book_id, :v2) AND #status = :success',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':v2': 'v2-', ':success': 'success'}
    )

    books.extend(response['Items'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression='begins_with(book_id, :v2) AND #status = :success',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={':v2': 'v2-', ':success': 'success'},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        books.extend(response['Items'])

    # Deduplicate by source PDF (prefer latest successful version)
    books_by_source = {}
    for book in books:
        source_uri = book.get('source_pdf_uri', '')
        if not source_uri:
            continue
        source_key = source_uri.replace('s3://jsmith-input/', '')
        books_by_source[source_key] = book

    unique_books = list(books_by_source.values())
    print(f"  Found {len(books)} total successful books")
    print(f"  {len(unique_books)} unique successful books")

    return unique_books

def get_output_files(book_id: str) -> list:
    """Get the list of output files for a book from S3."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
        data = json.loads(obj['Body'].read())
        return data.get('output_files', [])
    except Exception as e:
        print(f"  ERROR: Could not read output_files.json for {book_id}: {e}")
        return []

def sync_book(book: dict, dry_run: bool = False) -> int:
    """Sync a single book's output files to local folder."""
    book_id = book['book_id']
    source_uri = book.get('source_pdf_uri', '')
    artist = book.get('artist', 'Unknown')
    book_name = book.get('book_name', 'Unknown')

    # Parse artist and book name from source path if not in metadata
    if source_uri:
        parts = Path(source_uri.replace('s3://jsmith-input/', '')).parts
        if len(parts) >= 2 and artist == 'Unknown':
            artist = parts[0]
        if book_name == 'Unknown':
            book_filename = Path(source_uri).stem
            if ' - ' in book_filename:
                book_name = book_filename.split(' - ', 1)[1]
            else:
                book_name = book_filename

    print(f"\n{artist} - {book_name}")
    print(f"  Book ID: {book_id}")

    # Get output files
    output_files = get_output_files(book_id)
    if not output_files:
        print("  No output files found")
        return 0

    print(f"  Found {len(output_files)} songs")

    # Create local folder structure: ProcessedSongs_Final/{Artist}/{Book}/
    local_book_dir = LOCAL_OUTPUT_DIR / artist / book_name

    if not dry_run:
        local_book_dir.mkdir(parents=True, exist_ok=True)

    synced = 0
    skipped = 0

    for of in output_files:
        s3_uri = of.get('output_uri', '')
        song_title = of.get('song_title', 'Unknown')

        if not s3_uri.startswith(f's3://{OUTPUT_BUCKET}/'):
            print(f"    SKIP: Invalid S3 URI: {s3_uri}")
            continue

        # Parse S3 key from URI
        s3_key = s3_uri.replace(f's3://{OUTPUT_BUCKET}/', '')

        # Local filename: sanitize song title
        safe_title = song_title.replace('/', '-').replace('\\', '-').replace(':', '-')
        safe_title = safe_title.replace('"', '').replace('?', '').replace('*', '')
        safe_title = safe_title.replace('<', '').replace('>', '').replace('|', '')
        local_filename = f"{artist} - {safe_title}.pdf"
        local_path = local_book_dir / local_filename

        if local_path.exists():
            # Skip if already exists
            skipped += 1
            continue

        if dry_run:
            print(f"    Would download: {local_filename}")
            synced += 1
        else:
            try:
                s3.download_file(OUTPUT_BUCKET, s3_key, str(local_path))
                synced += 1
            except Exception as e:
                print(f"    ERROR downloading {song_title}: {e}")

    if not dry_run and synced > 0:
        print(f"  Downloaded {synced} new files ({skipped} already existed)")
    elif not dry_run and skipped > 0:
        print(f"  All {skipped} files already synced")

    return synced

def main():
    parser = argparse.ArgumentParser(description='Sync all successful books from S3 to local')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced')
    parser.add_argument('--limit', type=int, help='Only sync first N books')

    args = parser.parse_args()

    print("="*80)
    print("SYNC SUCCESSFUL BOOKS TO LOCAL")
    print("="*80)

    books = get_successful_books()

    if args.limit:
        books = books[:args.limit]
        print(f"  Limited to {len(books)} books")

    if args.dry_run:
        print("\n*** DRY RUN - No files will be downloaded ***")

    # Create output directory
    if not args.dry_run:
        LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_synced = 0
    total_books = 0

    for book in books:
        synced = sync_book(book, dry_run=args.dry_run)
        total_synced += synced
        if synced > 0:
            total_books += 1

    print(f"\n{'='*80}")
    print(f"SYNC COMPLETE")
    print(f"{'='*80}")
    print(f"Books processed: {len(books)}")
    print(f"Books with new files: {total_books}")
    print(f"Total files synced: {total_synced}")
    print(f"Output folder: {LOCAL_OUTPUT_DIR.absolute()}")

if __name__ == '__main__':
    main()
