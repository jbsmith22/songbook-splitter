"""
Fix corrupted Unicode filenames in S3 output bucket.

8 song PDFs were uploaded with mangled Unicode characters.
This script uploads the correct local copies and deletes the corrupted versions.
"""

import boto3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
BUCKET = 'jsmith-output'

# Map: (artist_folder, book_folder, local_filename) for files with special chars
UNICODE_FILES = [
    ('Barry Manilow', 'Anthology', 'Barry Manilow - Paradise Café.pdf'),
    ('David Crosby', 'Songbook _lead Sheets_', 'David Crosby - Déjà Vu.pdf'),
    ('Eric Clapton', 'The Cream Of Clapton', 'Eric Clapton - The Cream Of Clapton \u2014 Odyssey Of A Guitar Player.pdf'),
    ('Neil Diamond', 'The Essential Neil Diamond', 'Neil Diamond - Desirée.pdf'),
    ('Pink Floyd', 'Anthology', 'Pink Floyd - Another Brick In The Wall \u2013 Part 2.pdf'),
    ('Various Artists', '100 Songs For Kids - _easy Guitar Songbook_', 'Various Artists - Frère Jacques (are You Sleeping-).pdf'),
    ('Various Artists', 'Oldies But Goodies', 'Various Artists - More (ti Guarderò Nel Cuore).pdf'),
    ('Yes', 'Complete Deluxe Edition', 'Yes - Würm.pdf'),
]

def main():
    s3 = boto3.client('s3')

    for artist, book, filename in UNICODE_FILES:
        local_path = OUTPUT_DIR / artist / book / filename
        correct_key = f'v3/{artist}/{book}/{filename}'

        print(f'\n--- {filename} ---')

        if not local_path.exists():
            print(f'  ERROR: Local file not found: {local_path}')
            continue

        # Find the corrupted S3 key by listing objects with the prefix
        prefix = f'v3/{artist}/{book}/{filename.split(" - ")[0]} - {filename.split(" - ")[1][:4]}'
        resp = s3.list_objects_v2(Bucket=BUCKET, Prefix=prefix)

        corrupted_keys = []
        for obj in resp.get('Contents', []):
            key = obj['Key']
            if key != correct_key:
                corrupted_keys.append(key)

        # Upload correct version
        print(f'  Uploading: {correct_key}')
        print(f'  From:      {local_path}')
        print(f'  Size:      {local_path.stat().st_size:,} bytes')

        s3.upload_file(
            str(local_path),
            BUCKET,
            correct_key,
            ExtraArgs={'ContentType': 'application/pdf'}
        )
        print(f'  Uploaded OK')

        # Delete corrupted versions
        for bad_key in corrupted_keys:
            print(f'  Deleting corrupted: {repr(bad_key)}')
            s3.delete_object(Bucket=BUCKET, Key=bad_key)
            print(f'  Deleted OK')

        if not corrupted_keys:
            print(f'  No corrupted version found (may have been same key)')

        # Verify
        try:
            head = s3.head_object(Bucket=BUCKET, Key=correct_key)
            print(f'  Verified: {head["ContentLength"]:,} bytes in S3')
        except Exception as e:
            print(f'  VERIFY FAILED: {e}')

    print('\n=== Done ===')


if __name__ == '__main__':
    main()
