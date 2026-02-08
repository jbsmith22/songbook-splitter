#!/usr/bin/env python3
"""
Batch process unprocessed books through V2 pipeline.
Finds books that haven't been processed and submits them to Step Functions.
"""
import json
import boto3
import time
from pathlib import Path
from datetime import datetime
import hashlib

# AWS clients
stepfunctions = boto3.client('stepfunctions')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

# Configuration
INPUT_BUCKET = 'jsmith-input'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'

def generate_book_id(source_pdf_path: str, version: int = 2) -> str:
    """Generate deterministic book ID from source PDF path."""
    content = f"{source_pdf_path}-v{version}"
    hash_obj = hashlib.md5(content.encode())
    return f"v{version}-{hash_obj.hexdigest()}"

def get_processed_books():
    """Get set of source PDFs that have already been processed successfully."""
    processed_sources = set()

    try:
        # Scan DynamoDB for successful V2 books
        response = table.scan(
            FilterExpression='begins_with(book_id, :v2)',
            ExpressionAttributeValues={':v2': 'v2-'}
        )

        for item in response['Items']:
            if item.get('status') == 'success' and 'source_pdf_uri' in item:
                # Extract relative path from S3 URI
                uri = item['source_pdf_uri']
                if uri.startswith('s3://jsmith-input/'):
                    rel_path = uri.replace('s3://jsmith-input/', '')
                    processed_sources.add(rel_path)

        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                FilterExpression='begins_with(book_id, :v2)',
                ExpressionAttributeValues={':v2': 'v2-'},
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response['Items']:
                if item.get('status') == 'success' and 'source_pdf_uri' in item:
                    uri = item['source_pdf_uri']
                    if uri.startswith('s3://jsmith-input/'):
                        rel_path = uri.replace('s3://jsmith-input/', '')
                        processed_sources.add(rel_path)

        print(f"Found {len(processed_sources)} already processed V2 books")
        return processed_sources

    except Exception as e:
        print(f"Error getting processed books: {e}")
        return set()

def find_unprocessed_books(limit=None):
    """Find books that haven't been processed yet."""
    sheetmusic_dir = Path('SheetMusic')

    if not sheetmusic_dir.exists():
        print(f"ERROR: SheetMusic directory not found at {sheetmusic_dir}")
        return []

    # Get all PDFs
    all_pdfs = list(sheetmusic_dir.rglob('*.pdf'))
    print(f"Found {len(all_pdfs)} total PDFs in SheetMusic folder")

    # Get already processed source PDFs
    processed_sources = get_processed_books()

    # Find unprocessed
    unprocessed = []
    for pdf_path in all_pdfs:
        # Get relative path from SheetMusic folder
        rel_path = pdf_path.relative_to(sheetmusic_dir)
        source_pdf = str(rel_path).replace('\\', '/')

        # Check if already processed (compare source PDF paths, not book IDs)
        if source_pdf not in processed_sources:
            # Generate book ID for this processing run
            book_id = generate_book_id(source_pdf, version=2)
            # Extract artist and book name
            parts = source_pdf.split('/')
            if len(parts) >= 2:
                artist = parts[0]
                book_filename = parts[-1].replace('.pdf', '')
                if ' - ' in book_filename:
                    book_name = book_filename.split(' - ', 1)[1]
                else:
                    book_name = book_filename
            else:
                artist = 'Unknown'
                book_name = source_pdf.replace('.pdf', '')

            unprocessed.append({
                'book_id': book_id,
                'source_pdf': source_pdf,
                'artist': artist,
                'book_name': book_name,
                'local_path': str(pdf_path)
            })

    print(f"Found {len(unprocessed)} unprocessed books")

    if limit:
        unprocessed = unprocessed[:limit]
        print(f"Limited to {limit} books")

    return unprocessed

def upload_source_pdf_if_needed(source_pdf_path: str, local_path: str) -> bool:
    """Upload source PDF to S3 if it doesn't exist."""
    try:
        # Check if already exists
        s3.head_object(Bucket=INPUT_BUCKET, Key=source_pdf_path)
        return True
    except:
        # Need to upload
        try:
            print(f"  Uploading {source_pdf_path}...")
            with open(local_path, 'rb') as f:
                s3.put_object(
                    Bucket=INPUT_BUCKET,
                    Key=source_pdf_path,
                    Body=f,
                    ContentType='application/pdf'
                )
            print(f"  OK Uploaded")
            return True
        except Exception as e:
            print(f"  ERROR uploading: {e}")
            return False

def submit_book_for_processing(book):
    """Submit a book to Step Functions for processing."""
    book_id = book['book_id']
    source_pdf = book['source_pdf']
    artist = book['artist']
    book_name = book['book_name']
    local_path = book['local_path']

    print(f"\nProcessing: {artist} - {book_name}")
    print(f"  Book ID: {book_id}")

    # Upload source PDF if needed
    if not upload_source_pdf_if_needed(source_pdf, local_path):
        print(f"  SKIPPED: Failed to upload source PDF")
        return None

    # Prepare execution input
    execution_input = {
        'book_id': book_id,
        'source_pdf_uri': f's3://{INPUT_BUCKET}/{source_pdf}',
        'artist': artist,
        'book_name': book_name,
        'force_reprocess': False,
        'use_manual_splits': False
    }

    try:
        # Start execution
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f'batch-{book_id}-{int(time.time())}',
            input=json.dumps(execution_input)
        )

        execution_arn = response['executionArn']
        print(f"  OK Submitted: {execution_arn}")

        return {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name,
            'execution_arn': execution_arn,
            'start_time': datetime.now().isoformat()
        }

    except Exception as e:
        print(f"  ERROR submitting: {e}")
        return None

def batch_process(count=100, delay_between_submissions=2):
    """Process a batch of books."""
    print("=" * 80)
    print(f"BATCH PROCESSING: {count} books")
    print("=" * 80)

    # Find unprocessed books
    unprocessed = find_unprocessed_books(limit=count)

    if not unprocessed:
        print("\nNo unprocessed books found!")
        return

    print(f"\nSubmitting {len(unprocessed)} books for processing...")
    print(f"Delay between submissions: {delay_between_submissions}s")

    # Submit each book
    results = []
    for i, book in enumerate(unprocessed, 1):
        print(f"\n[{i}/{len(unprocessed)}]")
        result = submit_book_for_processing(book)
        if result:
            results.append(result)

        # Delay between submissions to avoid throttling
        if i < len(unprocessed):
            time.sleep(delay_between_submissions)

    # Save batch results
    batch_file = Path(f'data/batch_executions_{int(time.time())}.json')
    batch_file.parent.mkdir(exist_ok=True)

    with open(batch_file, 'w') as f:
        json.dump({
            'submitted_at': datetime.now().isoformat(),
            'total_submitted': len(results),
            'executions': results
        }, f, indent=2)

    print("\n" + "=" * 80)
    print(f"BATCH COMPLETE")
    print("=" * 80)
    print(f"Successfully submitted: {len(results)}/{len(unprocessed)} books")
    print(f"Batch details saved to: {batch_file}")
    print("\nYou can monitor progress with:")
    print("  python scripts/monitor_batch.py")

if __name__ == '__main__':
    import sys

    # Get count from command line or default to 100
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100

    batch_process(count=count, delay_between_submissions=2)
