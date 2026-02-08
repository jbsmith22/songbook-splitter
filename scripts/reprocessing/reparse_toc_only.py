"""
Re-parse TOC for books that have 0 TOC entries but good extracted OCR text.

This script:
1. Finds COMPLETE books with 0 toc_song_count
2. Loads their toc_discovery.json (which has extracted OCR text)
3. Re-parses using the text-based parser (with the new fallback logic)
4. Updates toc_parse.json in S3
5. Reports on TOC vs extracted song count discrepancies

Usage:
    py scripts/reprocessing/reparse_toc_only.py --dry-run    # See what would be reparsed
    py scripts/reprocessing/reparse_toc_only.py              # Actually reparse
    py scripts/reprocessing/reparse_toc_only.py --limit 10   # Reparse first 10
"""
import sys
import json
import boto3
import argparse
from pathlib import Path
from collections import defaultdict

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.toc_parser import TOCParser
from app.services.bedrock_parser import BedrockParserService

# Configuration
OUTPUT_BUCKET = 'jsmith-output'
PROVENANCE_FILE = Path('data/analysis/v2_provenance_database.json')

s3 = boto3.client('s3')


def get_books_needing_toc_reparse():
    """Find COMPLETE books with 0 TOC entries."""
    if not PROVENANCE_FILE.exists():
        print(f"ERROR: {PROVENANCE_FILE} not found. Run generate_v2_provenance.py first.")
        return []

    with open(PROVENANCE_FILE) as f:
        data = json.load(f)

    # Find COMPLETE books with 0 toc_songs but >0 actual_songs
    books_to_reparse = []
    for book in data['songbooks']:
        if book['verification']['status'] != 'COMPLETE':
            continue

        toc_songs = book['verification'].get('toc_songs', 0)
        actual_songs = book['verification'].get('actual_songs', 0)
        book_id = book['mapping'].get('book_id')

        if toc_songs == 0 and actual_songs > 0 and book_id and book_id != 'NOT_PROCESSED':
            books_to_reparse.append({
                'book_id': book_id,
                'source_pdf': book['source_pdf']['path'],
                'actual_songs': actual_songs,
                'toc_songs': toc_songs
            })

    return books_to_reparse


def load_toc_discovery(book_id: str) -> dict:
    """Load toc_discovery.json from S3."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/toc_discovery.json')
        return json.loads(obj['Body'].read())
    except Exception as e:
        print(f"  ERROR loading toc_discovery.json: {e}")
        return None


def reparse_toc(book_id: str, toc_discovery: dict, dry_run: bool = False) -> dict:
    """Re-parse TOC using extracted text from discovery."""
    toc_pages = toc_discovery.get('toc_pages', [])
    extracted_text = toc_discovery.get('extracted_text', {})

    if not extracted_text:
        print(f"  No extracted text available")
        return None

    # Combine text from all TOC pages
    combined_text = '\n'.join(
        extracted_text.get(str(page_num), '')
        for page_num in toc_pages
    )

    if not combined_text.strip():
        print(f"  Combined TOC text is empty")
        return None

    print(f"  Parsing {len(combined_text)} chars of OCR text from {len(toc_pages)} pages...")

    if dry_run:
        # Just count lines that look like TOC entries
        potential_entries = sum(1 for line in combined_text.split('\n')
                               if line.strip() and any(c.isdigit() for c in line))
        print(f"  [DRY RUN] ~{potential_entries} potential TOC entries")
        return {'entries': [], 'dry_run': True, 'potential': potential_entries}

    # Parse using text-based parser (which uses Bedrock)
    parser = TOCParser(use_bedrock_fallback=True)

    # Extract artist/book info from path
    book_metadata = {}

    result = parser.parse_toc(combined_text, book_metadata)

    return {
        'entries': [
            {
                'song_title': e.song_title,
                'page_number': e.page_number,
                'artist': e.artist,
                'confidence': e.confidence
            }
            for e in result.entries
        ],
        'extraction_method': result.extraction_method,
        'confidence': result.confidence,
        'artist_overrides': result.artist_overrides
    }


def save_toc_parse(book_id: str, toc_parse: dict):
    """Save updated toc_parse.json to S3."""
    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=f'artifacts/{book_id}/toc_parse.json',
        Body=json.dumps(toc_parse, indent=2),
        ContentType='application/json'
    )


def update_page_analysis_toc_count(book_id: str, toc_count: int):
    """Update toc_song_count in page_analysis.json."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
        page_analysis = json.loads(obj['Body'].read())

        page_analysis['toc_song_count'] = toc_count

        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=f'artifacts/{book_id}/page_analysis.json',
            Body=json.dumps(page_analysis, indent=2),
            ContentType='application/json'
        )
        return True
    except Exception as e:
        print(f"  Warning: Could not update page_analysis.json: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Re-parse TOC for books with 0 entries')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--limit', type=int, help='Only process first N books')
    parser.add_argument('--book-id', type=str, help='Process specific book ID')

    args = parser.parse_args()

    print("=" * 70)
    print("TOC RE-PARSER")
    print("=" * 70)

    if args.book_id:
        # Process single book
        books = [{'book_id': args.book_id, 'source_pdf': 'manual', 'actual_songs': 0, 'toc_songs': 0}]
    else:
        # Find books needing reparse
        print("\nFinding books with 0 TOC entries...")
        books = get_books_needing_toc_reparse()
        print(f"Found {len(books)} books needing TOC reparse")

    if args.limit:
        books = books[:args.limit]
        print(f"Limited to {len(books)} books")

    if args.dry_run:
        print("\n*** DRY RUN - No changes will be made ***\n")

    # Statistics
    stats = {
        'processed': 0,
        'success': 0,
        'failed': 0,
        'no_discovery': 0,
        'matches': 0,
        'mismatches': 0
    }
    mismatches = []

    for i, book in enumerate(books):
        book_id = book['book_id']
        source_pdf = book['source_pdf']
        actual_songs = book['actual_songs']

        print(f"\n[{i+1}/{len(books)}] {source_pdf}")
        print(f"  Book ID: {book_id}")
        print(f"  Extracted songs: {actual_songs}")

        # Load toc_discovery.json
        toc_discovery = load_toc_discovery(book_id)
        if not toc_discovery:
            stats['no_discovery'] += 1
            continue

        # Re-parse TOC
        toc_parse = reparse_toc(book_id, toc_discovery, dry_run=args.dry_run)
        if not toc_parse:
            stats['failed'] += 1
            continue

        toc_count = len(toc_parse.get('entries', []))
        print(f"  TOC entries found: {toc_count}")

        if not args.dry_run and toc_count > 0:
            # Save results
            save_toc_parse(book_id, toc_parse)
            update_page_analysis_toc_count(book_id, toc_count)
            print(f"  Saved {toc_count} TOC entries")

        stats['processed'] += 1
        if toc_count > 0:
            stats['success'] += 1

        # Compare TOC vs extracted
        if toc_count > 0:
            diff = abs(toc_count - actual_songs)
            diff_pct = (diff / max(toc_count, actual_songs)) * 100 if max(toc_count, actual_songs) > 0 else 0

            if diff_pct <= 10:
                stats['matches'] += 1
                print(f"  [OK] Match: TOC={toc_count}, Extracted={actual_songs}")
            else:
                stats['mismatches'] += 1
                mismatches.append({
                    'book_id': book_id,
                    'source_pdf': source_pdf,
                    'toc_count': toc_count,
                    'actual_count': actual_songs,
                    'diff_pct': diff_pct
                })
                print(f"  [!!] MISMATCH: TOC={toc_count}, Extracted={actual_songs} ({diff_pct:.1f}% diff)")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Books processed:    {stats['processed']}")
    print(f"Successful parses:  {stats['success']}")
    print(f"Failed parses:      {stats['failed']}")
    print(f"No discovery data:  {stats['no_discovery']}")
    print(f"TOC/Extract match:  {stats['matches']}")
    print(f"TOC/Extract differ: {stats['mismatches']}")

    if mismatches:
        print(f"\n{'='*70}")
        print("MISMATCHES (may need full reprocessing)")
        print("=" * 70)
        for m in sorted(mismatches, key=lambda x: -x['diff_pct']):
            print(f"  {m['source_pdf']}")
            print(f"    TOC: {m['toc_count']}, Extracted: {m['actual_count']} ({m['diff_pct']:.1f}% diff)")

        # Save mismatches to file
        if not args.dry_run:
            mismatch_file = Path('data/analysis/toc_extraction_mismatches.json')
            mismatch_file.parent.mkdir(parents=True, exist_ok=True)
            with open(mismatch_file, 'w') as f:
                json.dump(mismatches, f, indent=2)
            print(f"\nMismatches saved to: {mismatch_file}")


if __name__ == '__main__':
    main()
