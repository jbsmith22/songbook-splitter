#!/usr/bin/env python3
"""
Retry a single book through the V2 pipeline.
"""
import boto3
import hashlib
import time
from pathlib import Path

# Configuration
INPUT_BUCKET = 'jsmith-input'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'

s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

def submit_book(local_path: str, artist: str, book_name: str):
    """Submit a single book for processing."""

    local_file = Path(local_path)
    if not local_file.exists():
        print(f"ERROR: File not found: {local_path}")
        return False

    # Generate book ID from local path
    path_for_hash = str(local_file).replace('\\', '/')
    book_id = f"v2-{hashlib.md5(path_for_hash.encode()).hexdigest()}"

    # Check if file exists in S3
    s3_key = f"{artist}/{local_file.name}"
    s3_uri = f"s3://{INPUT_BUCKET}/{s3_key}"

    try:
        s3.head_object(Bucket=INPUT_BUCKET, Key=s3_key)
        print(f"OK File exists in S3: {s3_uri}")
    except:
        print(f"Uploading to S3: {s3_uri}")
        s3.upload_file(str(local_file), INPUT_BUCKET, s3_key)
        print(f"OK Uploaded successfully")

    # Submit to Step Functions
    timestamp = int(time.time())
    execution_name = f"retry-{book_id}-{timestamp}"

    input_data = {
        "book_id": book_id,
        "source_pdf_uri": s3_uri,
        "artist": artist,
        "book_name": book_name
    }

    print(f"\nSubmitting to Step Functions:")
    print(f"  Book ID: {book_id}")
    print(f"  Artist: {artist}")
    print(f"  Book: {book_name}")
    print(f"  Source: {s3_uri}")

    import json
    response = stepfunctions.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=execution_name,
        input=json.dumps(input_data)
    )

    print(f"\nOK Execution started: {execution_name}")
    print(f"  ARN: {response['executionArn']}")

    return True

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python retry_single_book.py <local_path> <artist> <book_name>")
        print("Example: python retry_single_book.py 'SheetMusic/Artist/Book.pdf' 'Artist Name' 'Book Name'")
        sys.exit(1)

    local_path = sys.argv[1]
    artist = sys.argv[2]
    book_name = sys.argv[3]

    submit_book(local_path, artist, book_name)
