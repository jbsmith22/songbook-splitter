"""
Download v2 processed books from S3 to ProcessedSongs_Final.

Usage:
    py scripts/reprocessing/download_v2_to_final.py --dry-run    # See what would be downloaded
    py scripts/reprocessing/download_v2_to_final.py --all        # Download all complete v2 books
    py scripts/reprocessing/download_v2_to_final.py --limit 5    # Download first 5
"""
import json
import boto3
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# Configuration
OUTPUT_BUCKET = 'jsmith-output'
INPUT_BUCKET = 'jsmith-input'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
FINAL_DIR = Path('ProcessedSongs_Final')
SHEETMUSIC_DIR = Path('SheetMusic')

s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')


def get_v2_complete_books():
    """Get list of v2 books with complete artifacts."""
    print("Fetching v2 executions...")

    complete_books = []

    paginator = sfn.get_paginator('list_executions')
    for page in paginator.paginate(
        stateMachineArn=STATE_MACHINE_ARN,
        statusFilter='SUCCEEDED',
        PaginationConfig={'MaxItems': 500}
    ):
        for ex in page.get('executions', []):
            if not ex['name'].startswith('v2-'):
                continue

            try:
                desc = sfn.describe_execution(executionArn=ex['executionArn'])
                input_data = json.loads(desc.get('input', '{}'))
                output = json.loads(desc.get('output', '{}'))

                # Check internal status
                payload = output.get('Payload', {})
                if payload.get('status') != 'success':
                    continue

                book_id = input_data.get('book_id')
                source_uri = input_data.get('source_pdf_uri', '')

                # Extract relative path from S3 URI
                if source_uri.startswith(f's3://{INPUT_BUCKET}/'):
                    rel_path = source_uri.replace(f's3://{INPUT_BUCKET}/', '')
                else:
                    rel_path = source_uri

                # Check if output_files.json exists
                try:
                    s3.head_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
                    has_output = True
                except:
                    has_output = False

                if has_output:
                    complete_books.append({
                        'book_id': book_id,
                        'source_path': rel_path,
                        'artist': input_data.get('artist', ''),
                        'book_name': input_data.get('book_name', '')
                    })
            except Exception as e:
                pass

    print(f"  Found {len(complete_books)} complete v2 books")
    return complete_books


def get_output_files(book_id: str) -> list:
    """Get list of output files from artifacts."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
        data = json.loads(obj['Body'].read())
        return data.get('output_files', [])
    except:
        return []


def download_book(book: dict, dry_run: bool = False) -> dict:
    """Download a v2 book to ProcessedSongs_Final."""
    book_id = book['book_id']
    artist = book['artist']
    book_name = book['book_name']

    # Get output files
    output_files = get_output_files(book_id)
    if not output_files:
        return {'status': 'error', 'message': 'No output files found'}

    # Determine local folder structure - NO Songs subfolder
    local_artist_dir = FINAL_DIR / artist
    local_book_dir = local_artist_dir / f"{artist} - {book_name}"

    # Deduplicate by S3 key (some books have duplicate entries)
    seen_keys = set()
    unique_files = []
    for f in output_files:
        uri = f.get('output_uri', '')
        if uri not in seen_keys:
            seen_keys.add(uri)
            unique_files.append(f)

    if dry_run:
        print(f"  Would create: {local_book_dir}")
        print(f"  Would download {len(unique_files)} songs (from {len(output_files)} entries)")
        return {'status': 'dry_run', 'songs': len(unique_files)}

    # Create directory
    local_book_dir.mkdir(parents=True, exist_ok=True)

    # Download each song
    downloaded = 0
    skipped = 0
    errors = []

    for file_info in unique_files:
        output_uri = file_info.get('output_uri', '')
        song_title = file_info.get('song_title', 'Unknown')

        if not output_uri.startswith(f's3://{OUTPUT_BUCKET}/'):
            errors.append(f"Invalid URI: {output_uri}")
            continue

        s3_key = output_uri.replace(f's3://{OUTPUT_BUCKET}/', '')

        # Create local filename: Artist - Song Title.pdf
        # Remove/replace Windows-invalid characters: \ / : * ? " < > |
        safe_title = song_title
        for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', "'", '"', '"']:
            safe_title = safe_title.replace(char, '')
        local_filename = f"{artist} - {safe_title}.pdf"
        local_path = local_book_dir / local_filename

        # Skip if already exists
        if local_path.exists():
            skipped += 1
            continue

        try:
            s3.download_file(OUTPUT_BUCKET, s3_key, str(local_path))
            downloaded += 1
        except Exception as e:
            errors.append(f"Failed to download {song_title}: {e}")

    # Copy original PDF from SheetMusic to artist folder (not book folder)
    source_rel_path = book['source_path']
    source_pdf = SHEETMUSIC_DIR / source_rel_path
    original_copied = False
    if source_pdf.exists():
        dest_pdf = local_artist_dir / source_pdf.name
        if not dest_pdf.exists():
            shutil.copy2(source_pdf, dest_pdf)
            original_copied = True

    # Create manifest
    manifest = {
        'book_id': book_id,
        'artist': artist,
        'book_name': book_name,
        'source_path': book['source_path'],
        'pipeline_version': 'v2',
        'downloaded_at': datetime.now().isoformat(),
        'songs': [
            {
                'title': f.get('song_title'),
                'pages': f.get('page_range'),
                'file_size': f.get('file_size_bytes')
            }
            for f in unique_files
        ],
        'total_entries': len(output_files),
        'unique_songs': len(unique_files),
        'downloaded_songs': downloaded,
        'skipped_existing': skipped,
        'original_pdf_copied': original_copied
    }

    manifest_path = local_book_dir / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    actual_downloaded = downloaded + skipped  # skipped means already exists
    return {
        'status': 'success' if actual_downloaded == len(unique_files) else 'partial',
        'downloaded': downloaded,
        'skipped': skipped,
        'unique': len(unique_files),
        'total_entries': len(output_files),
        'errors': errors,
        'local_path': str(local_book_dir)
    }


def main():
    parser = argparse.ArgumentParser(description='Download v2 processed books to ProcessedSongs_Final')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be downloaded')
    parser.add_argument('--all', action='store_true', help='Download all complete v2 books')
    parser.add_argument('--limit', type=int, help='Only download first N books')
    parser.add_argument('--book-id', type=str, help='Download specific book by ID')

    args = parser.parse_args()

    # Safety check
    if not args.all and not args.limit and not args.book_id and not args.dry_run:
        print("*** SAFETY: Must specify --all, --limit, --book-id, or --dry-run ***")
        return

    # Get complete books
    books = get_v2_complete_books()

    # Filter by book_id if specified
    if args.book_id:
        books = [b for b in books if b['book_id'] == args.book_id]
        if not books:
            print(f"Book ID {args.book_id} not found")
            return

    # Apply limit
    if args.limit:
        books = books[:args.limit]

    print(f"\n{'=' * 60}")
    print(f"BOOKS TO DOWNLOAD: {len(books)}")
    print(f"{'=' * 60}")

    for book in books[:10]:
        print(f"  {book['artist']} - {book['book_name']}")
    if len(books) > 10:
        print(f"  ... and {len(books) - 10} more")

    if args.dry_run:
        print("\n*** DRY RUN - No files downloaded ***")
        return

    # Download books
    print(f"\nDownloading to {FINAL_DIR}...")

    results = {'success': 0, 'partial': 0, 'error': 0}

    for i, book in enumerate(books):
        print(f"\n[{i+1}/{len(books)}] {book['artist']} - {book['book_name']}")

        result = download_book(book, dry_run=args.dry_run)

        if result['status'] == 'success':
            results['success'] += 1
            msg = f"  {result['unique']} songs"
            if result['skipped'] > 0:
                msg += f" ({result['downloaded']} new, {result['skipped']} existing)"
            print(msg)
        elif result['status'] == 'partial':
            results['partial'] += 1
            print(f"  Partial: {result['downloaded']}/{result['unique']} unique songs")
            if result['total_entries'] != result['unique']:
                print(f"  (Note: {result['total_entries']} entries, {result['unique']} unique)")
            for err in result['errors'][:3]:
                print(f"    Error: {err}")
        else:
            results['error'] += 1
            print(f"  Error: {result.get('message', 'Unknown error')}")

    # Summary
    print(f"\n{'=' * 60}")
    print("DOWNLOAD COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Success: {results['success']}")
    print(f"  Partial: {results['partial']}")
    print(f"  Error:   {results['error']}")
    print(f"\nFiles saved to: {FINAL_DIR}")


if __name__ == '__main__':
    main()
