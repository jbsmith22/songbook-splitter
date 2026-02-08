"""
Process a single book through the improved pipeline and output to ProcessedSongs_Final.

Usage:
    python scripts/process_book_to_final.py <book_id>
    python scripts/process_book_to_final.py 2dbdadbcc4ac8c07

This script:
1. Checks if the book has correct artifacts (page_mapping.json with high confidence)
2. Downloads split files from S3
3. Creates manifest.json
4. Places everything in ProcessedSongs_Final/<Artist>/<Book>/
"""

import sys
import json
import boto3
from pathlib import Path
from datetime import datetime

# Configuration
S3_BUCKET = 'jsmith-output'
LOCAL_OUTPUT_BASE = Path('ProcessedSongs_Final')
DYNAMODB_TABLE = 'jsmith-processing-ledger'

# AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(DYNAMODB_TABLE)


def get_book_info(book_id: str) -> dict:
    """Get book info from DynamoDB."""
    response = table.get_item(Key={'book_id': book_id})
    if 'Item' not in response:
        raise ValueError(f"Book {book_id} not found in DynamoDB")
    return response['Item']


def get_page_mapping(book_id: str) -> dict:
    """Get page_mapping.json from S3."""
    key = f'artifacts/{book_id}/page_mapping.json'
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except s3.exceptions.NoSuchKey:
        raise ValueError(f"page_mapping.json not found for {book_id}")


def get_output_files(book_id: str) -> dict:
    """Get output_files.json from S3."""
    key = f'artifacts/{book_id}/output_files.json'
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except s3.exceptions.NoSuchKey:
        raise ValueError(f"output_files.json not found for {book_id}")


def download_split_files(output_files: dict, local_folder: Path) -> list:
    """Download all split PDFs from S3 to local folder."""
    local_folder.mkdir(parents=True, exist_ok=True)
    downloaded = []

    for file_info in output_files.get('output_files', []):
        s3_uri = file_info['output_uri']
        # Parse S3 URI: s3://bucket/key
        parts = s3_uri.replace('s3://', '').split('/', 1)
        bucket = parts[0]
        key = parts[1]

        # Get filename from URI
        filename = key.split('/')[-1]
        local_path = local_folder / filename

        print(f"  Downloading: {filename}")
        s3.download_file(bucket, key, str(local_path))

        downloaded.append({
            'filename': filename,
            'song_title': file_info['song_title'],
            'artist': file_info['artist'],
            'file_size_bytes': local_path.stat().st_size,
            'page_range': file_info.get('page_range', [])
        })

    return downloaded


def create_manifest(book_id: str, book_info: dict, page_mapping: dict,
                   downloaded_files: list, local_folder: Path) -> dict:
    """Create manifest.json for the book."""
    manifest = {
        'book_id': book_id,
        'source_pdf': book_info.get('source_pdf_uri', '').replace('s3://jsmith-input/', ''),
        'artist': book_info.get('artist', 'Unknown'),
        'book_name': book_info.get('book_name', 'Unknown'),
        'song_count': len(downloaded_files),
        'songs': [
            {
                'filename': f['filename'],
                'song_title': f['song_title'],
                'artist': f['artist'],
                'file_size_bytes': f['file_size_bytes'],
                'page_range': f['page_range']
            }
            for f in downloaded_files
        ],
        'page_mapping_confidence': page_mapping.get('confidence', 0),
        'mapping_method': page_mapping.get('mapping_method', 'unknown'),
        'generated_at': datetime.now().isoformat(),
        'status': 'COMPLETE'
    }

    manifest_path = local_folder / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

    return manifest


def process_book(book_id: str, min_confidence: float = 0.8):
    """Process a single book to ProcessedSongs_Final."""
    print(f"\n{'='*60}")
    print(f"Processing book: {book_id}")
    print('='*60)

    # Step 1: Get book info
    print("\n1. Getting book info from DynamoDB...")
    book_info = get_book_info(book_id)
    artist = book_info.get('artist', 'Unknown')
    book_name = book_info.get('book_name', 'Unknown')
    print(f"   Artist: {artist}")
    print(f"   Book: {book_name}")

    # Step 2: Check page_mapping
    print("\n2. Checking page_mapping.json...")
    page_mapping = get_page_mapping(book_id)
    confidence = page_mapping.get('confidence', 0)
    song_count = len(page_mapping.get('song_locations', []))
    print(f"   Songs mapped: {song_count}")
    print(f"   Confidence: {confidence*100:.0f}%")

    if confidence < min_confidence:
        print(f"\n   WARNING: Confidence ({confidence*100:.0f}%) is below threshold ({min_confidence*100:.0f}%)")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted.")
            return None

    # Step 3: Get output files
    print("\n3. Getting output_files.json...")
    output_files = get_output_files(book_id)
    file_count = len(output_files.get('output_files', []))
    print(f"   Split files: {file_count}")

    if file_count != song_count:
        print(f"   WARNING: Song count mismatch! page_mapping={song_count}, output_files={file_count}")

    # Step 4: Create local folder
    # Normalize artist name for folder (capitalize, remove special chars)
    artist_folder = artist.title().replace('/', '-')
    book_folder = f"{artist} - {book_name}"
    local_folder = LOCAL_OUTPUT_BASE / artist_folder / book_folder

    print(f"\n4. Creating local folder...")
    print(f"   {local_folder}")

    if local_folder.exists():
        print("   WARNING: Folder already exists!")
        response = input("   Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("   Aborted.")
            return None
        import shutil
        shutil.rmtree(local_folder)

    # Step 5: Download files
    print("\n5. Downloading split files from S3...")
    downloaded = download_split_files(output_files, local_folder)
    print(f"   Downloaded: {len(downloaded)} files")

    # Step 6: Create manifest
    print("\n6. Creating manifest.json...")
    manifest = create_manifest(book_id, book_info, page_mapping, downloaded, local_folder)
    print(f"   Created manifest with {manifest['song_count']} songs")

    # Summary
    total_size = sum(f['file_size_bytes'] for f in downloaded)
    print(f"\n{'='*60}")
    print("COMPLETE!")
    print(f"{'='*60}")
    print(f"   Location: {local_folder}")
    print(f"   Songs: {len(downloaded)}")
    print(f"   Total size: {total_size/1024/1024:.2f} MB")
    print(f"   Confidence: {confidence*100:.0f}%")

    return manifest


def list_ready_books(min_confidence: float = 0.9):
    """List books that have high-confidence page_mapping and are ready to process."""
    print("\nScanning for ready books...")

    # Get all books from DynamoDB
    response = table.scan()
    all_books = response.get('Items', [])
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        all_books.extend(response.get('Items', []))

    ready_books = []

    for book in all_books:
        book_id = book.get('book_id')
        try:
            # Check for page_mapping
            key = f'artifacts/{book_id}/page_mapping.json'
            response = s3.get_object(Bucket=S3_BUCKET, Key=key)
            mapping = json.loads(response['Body'].read())

            confidence = mapping.get('confidence', 0)
            method = mapping.get('mapping_method', '')

            if confidence >= min_confidence and method == 'page_analysis':
                ready_books.append({
                    'book_id': book_id,
                    'artist': book.get('artist', 'Unknown'),
                    'book_name': book.get('book_name', 'Unknown'),
                    'confidence': confidence,
                    'song_count': len(mapping.get('song_locations', []))
                })
        except:
            pass

    print(f"\nFound {len(ready_books)} books with >= {min_confidence*100:.0f}% confidence:\n")
    for b in sorted(ready_books, key=lambda x: x['artist']):
        print(f"  {b['book_id']}  {b['artist']} - {b['book_name']} ({b['song_count']} songs, {b['confidence']*100:.0f}%)")

    return ready_books


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/process_book_to_final.py <book_id>")
        print("  python scripts/process_book_to_final.py --list")
        print("\nExamples:")
        print("  python scripts/process_book_to_final.py 2dbdadbcc4ac8c07")
        print("  python scripts/process_book_to_final.py --list")
        sys.exit(1)

    if sys.argv[1] == '--list':
        list_ready_books()
    else:
        book_id = sys.argv[1]
        process_book(book_id)
