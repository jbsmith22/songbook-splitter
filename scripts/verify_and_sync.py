"""
Verify S3 artifacts consistency and sync local files.
"""
import json
import boto3
from pathlib import Path

s3 = boto3.client('s3')
OUTPUT_BUCKET = 'jsmith-output'
FINAL_DIR = Path('ProcessedSongs_Final')

# All 16 books (excluding Beatles Fake Songbook Guitar)
books = [
    {'book_id': 'v2-e32e7feb95c5dd5b-2', 'name': 'Aerosmith - Greatest Hits _Songbook_'},
    {'book_id': 'v2-b1c5d9e0b2c00cfa-2', 'name': 'Allman Brothers - Best Of _PVG_'},
    {'book_id': 'v2-10c9b38769bc4333-2', 'name': 'Barry Manilow - Anthology'},
    {'book_id': 'v2-ce9d957468e199fe-2', 'name': 'Barry Manilow - Barry Manilow _PVG Book_'},
    {'book_id': 'v2-ee63e83296645419-2', 'name': 'Beatles - 100 Hits For All Keyboards'},
    {'book_id': 'v2-504918da8c736ac3-2', 'name': 'Beatles - Essential Songs'},
    {'book_id': 'v2-b35285e7019e260e-2', 'name': 'Beatles - Singles Collection _PVG_'},
    {'book_id': 'v2-419995ff8edb29d6-2', 'name': 'Billy Joel - Complete Vol 1'},
    {'book_id': 'v2-dde323032f955172-2', 'name': 'Billy Joel - Greatest Hits'},
    {'book_id': 'v2-9a5487d438dc0e6a-2', 'name': 'Billy Joel - Greatest Hits Vol I And II'},
    {'book_id': 'v2-e1714150fcf3f966-2', 'name': 'Billy Joel - My Lives'},
    {'book_id': 'v2-e3d88bf7f64722be-2', 'name': 'Billy Joel - Songs In The Attic'},
    {'book_id': 'v2-d5a9286f0899e26e-2', 'name': 'Bob Seger - The New Best Of Bob Seger'},
    {'book_id': 'v2-09a39b6d0883b0a5-2', 'name': 'Bruce Springsteen - Greatest Hits'},
    {'book_id': 'v2-170195b568600092-2', 'name': 'Burl Ives - Song Book'},
    {'book_id': 'v2-1602c5f5f8f2ed15-2', 'name': 'Cole Porter - The Very Best Of Cole Porter'},
]

INVALID_CHARS = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']


def sanitize_filename(title):
    """Remove invalid characters from filename."""
    safe = title
    for char in INVALID_CHARS:
        safe = safe.replace(char, '')
    return safe


def main():
    print("=" * 90)
    print("STEP 1: VERIFYING S3 ARTIFACTS CONSISTENCY")
    print("=" * 90)

    all_consistent = True
    verified_books = []

    for book in books:
        book_id = book['book_id']
        book_name = book['name']
        artist = book_name.split(' - ')[0]

        # Get page_analysis
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
        page_data = json.loads(obj['Body'].read())
        page_songs = page_data.get('songs', [])
        page_titles = set(s.get('title', '') for s in page_songs)

        # Get output_files
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
        output_data = json.loads(obj['Body'].read())
        output_files = output_data.get('output_files', [])
        output_titles = set(of.get('song_title', '') for of in output_files)

        # Check consistency
        if page_titles == output_titles:
            status = "OK"
        else:
            status = "MISMATCH"
            all_consistent = False

        print(f"  [{status}] {book_name}: {len(page_songs)} songs")

        verified_books.append({
            'book_id': book_id,
            'name': book_name,
            'artist': artist,
            'songs': len(output_files),
            'output_files': output_files,
            'consistent': status == "OK"
        })

    if all_consistent:
        print("\n*** ALL 16 BOOKS HAVE CONSISTENT S3 ARTIFACTS ***")
    else:
        print("\n*** SOME BOOKS HAVE INCONSISTENCIES ***")

    print("\n" + "=" * 90)
    print("STEP 2: SYNCING LOCAL FILES WITH S3")
    print("=" * 90)

    for vb in verified_books:
        book_id = vb['book_id']
        book_name = vb['name']
        artist = vb['artist']
        output_files = vb['output_files']

        local_book_dir = FINAL_DIR / artist / book_name

        print(f"\n{book_name}:")

        # Create directory if needed
        local_book_dir.mkdir(parents=True, exist_ok=True)

        # Get existing local files
        existing_pdfs = {f.name: f for f in local_book_dir.iterdir() if f.suffix.lower() == '.pdf'}

        # Track what we need
        s3_filenames = set()
        downloaded = 0
        skipped = 0

        for of in output_files:
            song_title = of['song_title']
            output_uri = of['output_uri']

            # Sanitize title for filename
            safe_title = sanitize_filename(song_title)
            local_filename = f"{artist} - {safe_title}.pdf"
            s3_filenames.add(local_filename)

            local_path = local_book_dir / local_filename

            if local_path.exists():
                skipped += 1
                continue

            # Download from S3
            s3_key = output_uri.replace(f's3://{OUTPUT_BUCKET}/', '')
            try:
                s3.download_file(OUTPUT_BUCKET, s3_key, str(local_path))
                downloaded += 1
            except Exception as e:
                print(f"    ERROR downloading {song_title}: {e}")

        # Remove stale files
        removed = 0
        for filename, filepath in existing_pdfs.items():
            if filename not in s3_filenames:
                filepath.unlink()
                removed += 1

        print(f"  Downloaded: {downloaded}, Skipped (existing): {skipped}, Removed (stale): {removed}")

        # Verify final count
        final_pdfs = [f for f in local_book_dir.iterdir() if f.suffix.lower() == '.pdf']
        if len(final_pdfs) == len(output_files):
            print(f"  [OK] Local count matches S3: {len(final_pdfs)} songs")
        else:
            print(f"  [ERROR] Count mismatch: local={len(final_pdfs)}, S3={len(output_files)}")

        # Create/update manifest
        manifest = {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name.replace(f'{artist} - ', ''),
            'pipeline_version': 'v2',
            'songs': [
                {
                    'title': of.get('song_title'),
                    'pages': of.get('page_range'),
                    'file_size': of.get('file_size_bytes')
                }
                for of in output_files
            ],
            'total_songs': len(output_files)
        }

        with open(local_book_dir / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

    print("\n" + "=" * 90)
    print("SYNC COMPLETE")
    print("=" * 90)


if __name__ == '__main__':
    main()
