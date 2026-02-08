"""
Reprocess specific books through the full pipeline.

Usage:
    py scripts/reprocessing/reprocess_specific_books.py --dry-run
    py scripts/reprocessing/reprocess_specific_books.py
"""
import sys
import json
import boto3
import time
import argparse
from pathlib import Path

# Configuration
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
SHEETMUSIC_DIR = Path('SheetMusic')

stepfunctions = boto3.client('stepfunctions')
s3 = boto3.client('s3')

# Books to reprocess - these have TOC/extraction mismatches
BOOKS_TO_REPROCESS = [
    # Books where extraction missed songs (need full reprocess)
    {
        'source_pdf': 'Beatles/Beatles - Essential Songs.pdf',
        'book_id': 'v2-504918da8c736ac3-2',
        'reason': 'TOC=94, Extracted=51 - extraction missed songs'
    },
    {
        'source_pdf': 'Beatles/Beatles - All Songs 1962-1974.pdf',
        'book_id': 'v2-1e46e821cacf170d-2',
        'reason': 'TOC=201, Extracted=157 - extraction missed songs'
    },
    # Books with contaminated TOC discovery data (need full reprocess to fix)
    {
        'source_pdf': 'Beatles/Beatles - Songbook.pdf',
        'book_id': 'v2-572ab40c580d53b6-2',
        'reason': 'Contaminated TOC data from All Songs'
    },
    {
        'source_pdf': 'Beatles/Beatles - Anthology.pdf',
        'book_id': 'v2-f9b37d9aca156dd9-2',
        'reason': 'Contaminated TOC data from All Songs'
    },
]


def clear_artifacts(book_id: str):
    """Clear existing artifacts before reprocessing."""
    prefix = f'artifacts/{book_id}/'
    paginator = s3.get_paginator('list_objects_v2')

    deleted = 0
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=prefix):
        if 'Contents' not in page:
            continue
        objects = [{'Key': obj['Key']} for obj in page['Contents']]
        if objects:
            s3.delete_objects(Bucket=OUTPUT_BUCKET, Delete={'Objects': objects})
            deleted += len(objects)

    return deleted


def upload_source_pdf(local_path: Path) -> str:
    """Upload source PDF to S3 if not already there."""
    rel_path = local_path.relative_to(SHEETMUSIC_DIR)
    s3_key = str(rel_path).replace('\\', '/')

    try:
        s3.head_object(Bucket=INPUT_BUCKET, Key=s3_key)
        return s3_key  # Already exists
    except:
        pass

    print(f"    Uploading {s3_key}...")
    with open(local_path, 'rb') as f:
        s3.put_object(Bucket=INPUT_BUCKET, Key=s3_key, Body=f, ContentType='application/pdf')

    return s3_key


def start_execution(book: dict) -> dict:
    """Start Step Functions execution for a book."""
    source_pdf = book['source_pdf']
    book_id = book['book_id']

    local_path = SHEETMUSIC_DIR / source_pdf
    if not local_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {local_path}")

    # Parse artist and book name
    parts = Path(source_pdf).parts
    artist = parts[0] if len(parts) >= 1 else 'Unknown'
    filename = Path(source_pdf).stem
    book_name = filename.split(' - ', 1)[1] if ' - ' in filename else filename

    # Upload source PDF
    s3_key = upload_source_pdf(local_path)
    source_pdf_uri = f's3://{INPUT_BUCKET}/{s3_key}'

    # Prepare execution input
    execution_input = {
        'book_id': book_id,
        'source_pdf_uri': source_pdf_uri,
        'artist': artist,
        'book_name': book_name,
        'force_reprocess': True,
        'use_manual_splits': False,
        'manual_splits_path': None
    }

    # Start execution
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=f'reprocess-{book_id}-{int(time.time())}',
        input=json.dumps(execution_input)
    )

    return {
        'book_id': book_id,
        'execution_arn': response['executionArn'],
        'start_date': response['startDate'].isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description='Reprocess specific books')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--clear-artifacts', action='store_true', default=True,
                       help='Clear existing artifacts before reprocessing')
    args = parser.parse_args()

    print("=" * 70)
    print("REPROCESS SPECIFIC BOOKS")
    print("=" * 70)

    print(f"\nBooks to reprocess: {len(BOOKS_TO_REPROCESS)}")
    for book in BOOKS_TO_REPROCESS:
        print(f"  - {book['source_pdf']}")
        print(f"    Reason: {book['reason']}")

    if args.dry_run:
        print("\n*** DRY RUN - No changes will be made ***")
        return

    # Confirm
    print(f"\n*** Ready to reprocess {len(BOOKS_TO_REPROCESS)} books ***")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    started = []
    failed = []

    for i, book in enumerate(BOOKS_TO_REPROCESS):
        print(f"\n[{i+1}/{len(BOOKS_TO_REPROCESS)}] {book['source_pdf']}")

        try:
            # Clear existing artifacts
            if args.clear_artifacts:
                deleted = clear_artifacts(book['book_id'])
                print(f"    Cleared {deleted} existing artifacts")

            # Start execution
            result = start_execution(book)
            started.append(result)
            print(f"    Started execution: {result['execution_arn'].split(':')[-1]}")

            # Rate limiting
            if i < len(BOOKS_TO_REPROCESS) - 1:
                time.sleep(0.5)

        except Exception as e:
            failed.append({'book': book, 'error': str(e)})
            print(f"    FAILED: {e}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Started: {len(started)}")
    print(f"Failed:  {len(failed)}")

    if started:
        print("\nUse this to check status:")
        print("  py scripts/reprocessing/batch_reprocess_all.py --status")


if __name__ == '__main__':
    main()
