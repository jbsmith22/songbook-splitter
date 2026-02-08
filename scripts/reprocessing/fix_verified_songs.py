"""
Fix verified_songs.json for books that have page_analysis.json with songs
but empty verified_songs.json.
"""
import json
import boto3
import tempfile
from pathlib import Path

OUTPUT_BUCKET = 'jsmith-output'
s3 = boto3.client('s3')

def fix_book(book_id: str):
    """Generate verified_songs.json from page_analysis.json."""
    print(f"Fixing {book_id}...")

    # Download page_analysis.json
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
        pa = json.loads(obj['Body'].read())
    except Exception as e:
        print(f"  ERROR: Could not load page_analysis.json: {e}")
        return False

    songs = pa.get('songs', [])
    if not songs:
        print(f"  No songs in page_analysis.json")
        return False

    # Create verified_songs structure
    verified_songs = {
        'verified_songs': [
            {
                'song_title': s['title'],
                'start_page': s['start_pdf_page'] - 1,  # 0-indexed
                'end_page': s['end_pdf_page'] - 1,  # 0-indexed
                'artist': s.get('artist', '')
            }
            for s in songs
        ]
    }

    # Upload to S3
    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=f'artifacts/{book_id}/verified_songs.json',
        Body=json.dumps(verified_songs, indent=2)
    )

    print(f"  Created verified_songs.json with {len(songs)} songs")
    return True


def main():
    book_ids = [
        'v2-dc4c90d5e3d7da00-2',  # Beatles
        'v2-891cfa3eccc19933-2',  # Billy Joel
        'v2-6790e3106cc63c95-2',  # Elton John
    ]

    for book_id in book_ids:
        fix_book(book_id)

    print("\nDone! Now run split_existing_books.py to create the actual PDFs.")


if __name__ == '__main__':
    main()
