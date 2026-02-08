"""
Split PDFs for books that have verified_songs.json but no output_files.

This runs the PDF splitter and manifest generator locally using existing
verified_songs.json data, without re-running the full pipeline.
"""
import sys
import json
import tempfile
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import boto3
from app.services.pdf_splitter import PDFSplitterService
from app.models import PageRange

# Configuration
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'

s3 = boto3.client('s3')


def split_book(book_id: str, source_pdf_path: str, artist: str, book_name: str):
    """Split a single book using existing verified_songs.json."""
    print(f"\n{'='*60}")
    print(f"Splitting: {source_pdf_path}")
    print(f"Book ID: {book_id}")
    print(f"{'='*60}")

    # Load verified songs from S3
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/verified_songs.json')
        verified_data = json.loads(obj['Body'].read())
        verified_songs = verified_data.get('verified_songs', [])
        print(f"Found {len(verified_songs)} verified songs")
    except Exception as e:
        print(f"ERROR: Could not load verified_songs.json: {e}")
        return False

    if not verified_songs:
        print("No songs to split")
        return False

    # Convert to PageRange objects
    page_ranges = [
        PageRange(
            song_title=song['song_title'],
            start_page=song['start_page'],
            end_page=song['end_page'],
            artist=song.get('artist', artist)
        )
        for song in verified_songs
    ]

    # Download PDF to temp file
    with tempfile.TemporaryDirectory() as temp_dir:
        pdf_path = Path(temp_dir) / 'input.pdf'
        print(f"Downloading PDF from s3://{INPUT_BUCKET}/{source_pdf_path}...")
        s3.download_file(INPUT_BUCKET, source_pdf_path, str(pdf_path))

        # Split PDF - uses S3 directly with output_bucket
        splitter = PDFSplitterService(output_bucket=OUTPUT_BUCKET)
        output_files = splitter.split_pdf(
            str(pdf_path),
            page_ranges,
            book_artist=artist,
            book_name=book_name
        )

        print(f"Generated {len(output_files)} split PDFs")

        # Build output_files.json from the returned OutputFile objects
        uploaded_files = [
            {
                'song_title': of.song_title,
                'file_path': of.output_uri,  # OutputFile uses output_uri
                'page_range': list(of.page_range),  # page_range is a tuple
                'file_size_bytes': of.file_size_bytes,
                'artist': of.artist
            }
            for of in output_files
        ]

        # Create and upload output_files.json
        output_manifest = {'output_files': uploaded_files}
        manifest_key = f'artifacts/{book_id}/output_files.json'
        s3.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=manifest_key,
            Body=json.dumps(output_manifest, indent=2)
        )
        print(f"Created output_files.json with {len(uploaded_files)} songs")

        return True


def main():
    # Books to process (from the v2 test batch)
    books = [
        {
            'book_id': 'v2-dc4c90d5e3d7da00-2',
            'source_pdf': 'Beatles/Beatles - Abbey Road.pdf',
            'artist': 'Beatles',
            'book_name': 'Beatles - Abbey Road'
        },
        {
            'book_id': 'v2-891cfa3eccc19933-2',
            'source_pdf': 'Billy Joel/Billy Joel - 52nd Street.pdf',
            'artist': 'Billy Joel',
            'book_name': 'Billy Joel - 52nd Street'
        },
        {
            'book_id': 'v2-6790e3106cc63c95-2',
            'source_pdf': 'Elton John/Elton John - Greatest Hits 1970-2002.pdf',
            'artist': 'Elton John',
            'book_name': 'Elton John - Greatest Hits 1970-2002'
        },
        {
            'book_id': 'v2-c2a89cc21678f463-2',
            'source_pdf': 'Queen/Queen - Greatest Hits.pdf',
            'artist': 'Queen',
            'book_name': 'Queen - Greatest Hits'
        },
    ]

    success_count = 0
    for book in books:
        try:
            if split_book(book['book_id'], book['source_pdf'], book['artist'], book['book_name']):
                success_count += 1
        except Exception as e:
            print(f"ERROR splitting {book['book_id']}: {e}")

    print(f"\n{'='*60}")
    print(f"COMPLETE: Split {success_count}/{len(books)} books successfully")
    print(f"{'='*60}")

    print("\nTo update the v2 provenance viewer, run:")
    print("  py scripts/analysis/generate_v2_provenance.py")


if __name__ == '__main__':
    main()
