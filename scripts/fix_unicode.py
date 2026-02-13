#!/usr/bin/env python3
"""
Fix non-ASCII characters in song titles and filenames.
Uses explicit mapping provided by user.
Rename local files, S3 objects, and update metadata.
"""

import json
import sys
from pathlib import Path

import boto3

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'

INVALID_CHARS = '?"<>|*'

# Explicit title replacements: (artist, book, substring_match) -> new_title
TITLE_MAP = [
    ('Barry Manilow', 'Anthology', 'Paradise Caf', 'Paradise Cafe'),
    ('David Crosby', 'Songbook _lead Sheets_', 'VU', 'Deja Vu'),
    ('Eric Clapton', 'The Cream Of Clapton', 'Odyssey', 'The Cream of Clapton Odyssey of a Guitar Player'),
    ('Neil Diamond', 'The Essential Neil Diamond', 'DESIR', 'Desiree'),
    ('Pink Floyd', 'Anthology', 'Brick', 'Another Brick in the Wall Part 2'),
    ('Various Artists', '100 Songs For Kids - _easy Guitar Songbook_', 'Jacques', 'Frere Jacques Are You Sleeping'),
    ('Various Artists', 'Oldies But Goodies', 'Guarder', 'More Ti Guardero Nel Cuore'),
    ('Yes', 'Complete Deluxe Edition', 'RM', 'Wurm'),
]


def is_ascii(text):
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def safe_filename(title, artist):
    """Build a safe filename from title and artist."""
    safe = title
    for ch in '/\\:' + INVALID_CHARS:
        safe = safe.replace(ch, '-' if ch in '/\\:' else '')
    return f'{artist} - {safe}.pdf'


def find_local_file(directory, search_term):
    """Find a local file by partial name match (case-insensitive)."""
    if not directory.exists():
        return None
    search_lower = search_term.lower()
    for f in directory.iterdir():
        if f.is_file() and search_lower in f.name.lower():
            return f
    return None


def get_new_title(artist, book, title):
    """Look up the replacement title from the explicit map."""
    for map_artist, map_book, match_str, new_title in TITLE_MAP:
        if artist == map_artist and book == map_book and match_str in title:
            return new_title
    return None


def main():
    dry_run = '--dry-run' in sys.argv
    mode = 'DRY RUN' if dry_run else 'LIVE'

    print(f'FIX UNICODE CHARACTERS ({mode})')
    print('=' * 70)

    s3 = boto3.client('s3', region_name='us-east-1')

    total_fixes = 0

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name

            of_path = book_dir / 'output_files.json'
            vs_path = book_dir / 'verified_songs.json'
            if not of_path.exists():
                continue

            with open(of_path) as f:
                of_data = json.load(f)
            with open(vs_path) as f:
                vs_data = json.load(f)

            book_changed = False
            output_dir = OUTPUT_DIR / artist / book

            for i, entry in enumerate(of_data.get('output_files', [])):
                title = entry['song_title']

                if is_ascii(title):
                    continue

                new_title = get_new_title(artist, book, title)
                if new_title is None:
                    print(f'\n  WARNING: No mapping for {artist} / {book}: "{title}"')
                    continue

                old_filename = safe_filename(title, entry.get('artist', artist))
                new_filename = safe_filename(new_title, entry.get('artist', artist))
                old_s3_key = f'v3/{artist}/{book}/{old_filename}'
                new_s3_key = f'v3/{artist}/{book}/{new_filename}'
                new_uri = f's3://{S3_OUTPUT_BUCKET}/{new_s3_key}'

                print(f'\n  {artist} / {book}: "{title}" -> "{new_title}"')
                print(f'    File: {old_filename} -> {new_filename}')

                if not dry_run:
                    # Update output_files.json entry
                    entry['song_title'] = new_title
                    entry['output_uri'] = new_uri

                    # Update verified_songs.json
                    if i < len(vs_data.get('verified_songs', [])):
                        vs_data['verified_songs'][i]['song_title'] = new_title

                    # Rename S3 output file
                    try:
                        s3.copy_object(
                            Bucket=S3_OUTPUT_BUCKET,
                            Key=new_s3_key,
                            CopySource={'Bucket': S3_OUTPUT_BUCKET, 'Key': old_s3_key},
                        )
                        s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=old_s3_key)
                        print(f'    S3: renamed')
                    except Exception as e:
                        # Try to find by partial match
                        print(f'    S3 copy failed ({e}), trying search...')
                        prefix = f'v3/{artist}/{book}/'
                        paginator = s3.get_paginator('list_objects_v2')
                        search = new_title[:15]
                        for page in paginator.paginate(Bucket=S3_OUTPUT_BUCKET, Prefix=prefix):
                            for obj in page.get('Contents', []):
                                if search.lower() in obj['Key'].lower():
                                    actual_key = obj['Key']
                                    if actual_key != new_s3_key:
                                        s3.copy_object(
                                            Bucket=S3_OUTPUT_BUCKET,
                                            Key=new_s3_key,
                                            CopySource={'Bucket': S3_OUTPUT_BUCKET, 'Key': actual_key},
                                        )
                                        s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=actual_key)
                                        print(f'    S3: found as "{actual_key}", renamed')
                                    break

                    # Rename local file
                    old_local = output_dir / old_filename
                    new_local = output_dir / new_filename
                    if old_local.exists():
                        old_local.rename(new_local)
                        entry['file_size_bytes'] = new_local.stat().st_size
                        print(f'    Local: renamed')
                    else:
                        found = find_local_file(output_dir, new_title[:15])
                        if found and found.name != new_filename:
                            found.rename(new_local)
                            entry['file_size_bytes'] = new_local.stat().st_size
                            print(f'    Local: found as "{found.name}", renamed')
                        elif found:
                            print(f'    Local: already correct name')
                        else:
                            print(f'    Local: NOT FOUND')

                book_changed = True
                total_fixes += 1

            if book_changed and not dry_run:
                # Save updated artifacts
                with open(of_path, 'w', encoding='utf-8') as f:
                    json.dump(of_data, f, indent=2, ensure_ascii=False)
                with open(vs_path, 'w', encoding='utf-8') as f:
                    json.dump(vs_data, f, indent=2, ensure_ascii=False)

                # Upload to S3
                for name in ['output_files.json', 'verified_songs.json']:
                    s3.upload_file(
                        str(book_dir / name),
                        S3_ARTIFACTS_BUCKET,
                        f'v3/{artist}/{book}/{name}',
                    )
                print(f'    Artifacts uploaded')

    # Also fix Pink Floyd Wots filename mismatch
    print(f'\n--- Fix Pink Floyd Wots filename mismatch ---')
    pf_of = ARTIFACTS_DIR / 'Pink Floyd' / 'Anthology' / 'output_files.json'
    with open(pf_of) as f:
        pf_data = json.load(f)

    for entry in pf_data['output_files']:
        if 'Wots' in entry['song_title']:
            old_uri = entry['output_uri']
            # The actual file uses no space: "Wots...Uh"
            if 'Wots... Uh' in old_uri:
                new_uri = old_uri.replace('Wots... Uh', 'Wots...Uh')
                print(f'  URI: {old_uri}')
                print(f'    -> {new_uri}')
                if not dry_run:
                    entry['output_uri'] = new_uri
            break

    if not dry_run:
        with open(pf_of, 'w', encoding='utf-8') as f:
            json.dump(pf_data, f, indent=2, ensure_ascii=False)
        s3.upload_file(str(pf_of), S3_ARTIFACTS_BUCKET, 'v3/Pink Floyd/Anthology/output_files.json')
        print(f'  Artifact uploaded')

    print(f'\n{"=" * 70}')
    print(f'Total unicode fixes: {total_fixes}')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
