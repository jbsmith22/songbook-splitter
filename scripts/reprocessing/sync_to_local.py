"""
Sync processed songs from S3 to local ProcessedSongs_Final folder.

Reads the v2 provenance database to find COMPLETE books and downloads
their split PDFs from S3 to the local folder structure.

Usage:
    py scripts/reprocessing/sync_to_local.py --dry-run    # See what would be synced
    py scripts/reprocessing/sync_to_local.py              # Actually sync
    py scripts/reprocessing/sync_to_local.py --limit 10   # Sync first 10 complete books
"""
import json
import boto3
import argparse
from pathlib import Path
from urllib.parse import unquote

# Configuration
OUTPUT_BUCKET = 'jsmith-output'
LOCAL_OUTPUT_DIR = Path('ProcessedSongs_Final')
PROVENANCE_FILE = Path('data/analysis/v2_provenance_database.json')

s3 = boto3.client('s3')


def get_complete_books():
    """Get all COMPLETE books from the v2 provenance database."""
    if not PROVENANCE_FILE.exists():
        print(f"ERROR: {PROVENANCE_FILE} not found. Run generate_v2_provenance.py first.")
        return []

    with open(PROVENANCE_FILE) as f:
        data = json.load(f)

    complete = [b for b in data['songbooks'] if b['verification']['status'] == 'COMPLETE']
    return complete


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
    book_id = book['mapping']['book_id']
    source_path = book['source_pdf']['path']

    # Parse artist and book name from source path
    parts = Path(source_path).parts
    if len(parts) >= 2:
        artist = parts[0]
        book_name = Path(source_path).stem
        if ' - ' in book_name:
            book_name = book_name.split(' - ', 1)[1]
    else:
        artist = 'Unknown'
        book_name = Path(source_path).stem

    print(f"\n{artist} - {book_name} ({book_id}):")

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
        local_filename = f"{artist} - {safe_title}.pdf"
        local_path = local_book_dir / local_filename

        if local_path.exists():
            # Skip if already exists
            continue

        if dry_run:
            print(f"    Would download: {local_filename}")
        else:
            try:
                s3.download_file(OUTPUT_BUCKET, s3_key, str(local_path))
                synced += 1
            except Exception as e:
                print(f"    ERROR downloading {song_title}: {e}")

    if not dry_run and synced > 0:
        print(f"  Downloaded {synced} new files")
    elif not dry_run:
        print(f"  All files already synced")

    return synced


def main():
    parser = argparse.ArgumentParser(description='Sync processed songs from S3 to local')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be synced')
    parser.add_argument('--limit', type=int, help='Only sync first N complete books')

    args = parser.parse_args()

    print("Loading v2 provenance database...")
    books = get_complete_books()
    print(f"  Found {len(books)} COMPLETE books")

    if args.limit:
        books = books[:args.limit]
        print(f"  Limited to {len(books)} books")

    if args.dry_run:
        print("\n*** DRY RUN - No files will be downloaded ***")

    # Create output directory
    if not args.dry_run:
        LOCAL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_synced = 0
    for book in books:
        synced = sync_book(book, dry_run=args.dry_run)
        total_synced += synced

    print(f"\n{'='*60}")
    print(f"SYNC COMPLETE")
    print(f"{'='*60}")
    print(f"Books processed: {len(books)}")
    print(f"Total songs synced: {total_synced}")
    print(f"Output folder: {LOCAL_OUTPUT_DIR}")


if __name__ == '__main__':
    main()
