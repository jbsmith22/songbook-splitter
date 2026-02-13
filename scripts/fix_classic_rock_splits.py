#!/usr/bin/env python3
"""
Fix Classic Rock 73 Songs: apply corrected splits, re-extract PDFs, rename with artists.

Changes:
1. BABY, I LOVE YOUR WAY: pages 8-17 → 8-13 (re-extract)
2. Alone Again Or (Love): NEW, pages 13-17
3. DON'T DO ME LIKE THAT: pages 74-76 → 74-79 (re-extract, absorbs "What If I Loved You")
4. What If I Loved You, Baby?: REMOVE (not a real song)
5. THE JOKER: pages 207-215 → 207-213 (re-extract)
6. Knockin' on Heaven's Door (Bob Dylan): NEW, pages 213-215
"""

import json
import sys
from pathlib import Path

import boto3
from pypdf import PdfReader, PdfWriter

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts' / 'Various Artists' / 'Classic Rock 73 Songs'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output' / 'Various Artists' / 'Classic Rock 73 Songs'
INPUT_PDF = PROJECT_ROOT / 'SheetMusic_Input' / 'Various Artists' / 'Various Artists - Classic Rock 73 songs.pdf'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'
S3_PREFIX = 'v3/Various Artists/Classic Rock 73 Songs/'

INVALID_CHARS = '?"<>|*'


def safe_filename(title, artist):
    """Build a safe filename from title and artist."""
    safe = title
    for ch in '/\\:' + INVALID_CHARS:
        safe = safe.replace(ch, '-' if ch in '/\\:' else '')
    return f'{artist} - {safe}.pdf'


def extract_pages(reader, start_page, end_page, output_path):
    """Extract pages [start_page, end_page) from reader and write to output_path."""
    writer = PdfWriter()
    for page_idx in range(start_page, end_page):
        writer.add_page(reader.pages[page_idx])
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path.stat().st_size


def find_s3_file(s3, bucket, prefix, search_term):
    """Find an S3 file by partial name match."""
    paginator = s3.get_paginator('list_objects_v2')
    search_lower = search_term.lower()
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            if search_lower in obj['Key'].lower():
                return obj['Key']
    return None


def main():
    dry_run = '--dry-run' in sys.argv

    print(f'FIX CLASSIC ROCK 73 SONGS SPLITS ({"DRY RUN" if dry_run else "LIVE"})')
    print('=' * 70)

    # Load corrected split data
    corrected_path = PROJECT_ROOT / 'v3_splits_a0ebbf6ec9ecc86e_corrected.json'
    with open(corrected_path) as f:
        corrected = json.load(f)

    new_verified = corrected['verified_songs']
    new_locations = corrected['page_mapping']['song_locations']
    print(f'Corrected data: {len(new_verified)} songs, {len(new_locations)} locations')

    # Load current output_files.json
    of_path = ARTIFACTS_DIR / 'output_files.json'
    with open(of_path) as f:
        of_data = json.load(f)
    current_outputs = of_data['output_files']
    print(f'Current output_files: {len(current_outputs)} entries')

    # Build lookup of current outputs by title
    current_by_title = {}
    for entry in current_outputs:
        current_by_title[entry['song_title'].upper()] = entry

    # Songs that need PDF re-extraction
    resplit_songs = {
        'BABY, I LOVE YOUR WAY',        # pages changed from 8-17 to 8-13
        "DON'T DO ME LIKE THAT",         # pages changed from 74-76 to 74-79
        'THE JOKER',                     # pages changed from 207-215 to 207-213
    }

    # New songs that need PDF extraction
    new_songs = {
        'ALONE AGAIN OR',                # pages 13-17, artist: Love
        "KNOCKIN' ON HEAVEN'S DOOR",     # pages 213-215, artist: Bob Dylan
    }

    # Song to delete
    delete_song = 'WHAT IF I LOVED YOU, BABY?'

    s3 = boto3.client('s3', region_name='us-east-1')

    # Open source PDF
    print(f'\nReading source PDF: {INPUT_PDF.name}')
    reader = PdfReader(str(INPUT_PDF))
    print(f'  {len(reader.pages)} pages')

    # === Step 1: Re-extract and create PDFs ===
    print('\n--- PDF EXTRACTION ---')
    new_output_files = []

    for song in new_verified:
        title = song['song_title']
        artist = song['artist']
        start = song['start_page']
        end = song['end_page']
        title_upper = title.upper()

        filename = safe_filename(title, artist)
        local_path = OUTPUT_DIR / filename
        s3_key = f'{S3_PREFIX}{filename}'
        s3_uri = f's3://{S3_OUTPUT_BUCKET}/{s3_key}'

        if title_upper in resplit_songs or title_upper in new_songs:
            # Need to extract PDF
            print(f'  EXTRACT: "{title}" by {artist} (pages {start}-{end})')
            print(f'    -> {filename}')

            if not dry_run:
                file_size = extract_pages(reader, start, end, local_path)
                print(f'    Local: {file_size:,} bytes')

                # Upload to S3
                s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)
                print(f'    S3: uploaded')

                # Delete old S3 file if title changed size
                if title_upper in resplit_songs:
                    old_entry = current_by_title.get(title_upper)
                    if old_entry:
                        old_key = old_entry['output_uri'].replace(f's3://{S3_OUTPUT_BUCKET}/', '')
                        if old_key != s3_key:
                            try:
                                s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=old_key)
                                print(f'    S3: deleted old key')
                            except Exception:
                                pass
            else:
                file_size = 0

            new_output_files.append({
                'song_title': title,
                'artist': artist,
                'output_uri': s3_uri,
                'file_size_bytes': file_size,
                'page_range': [start, end],
            })

        elif title_upper == delete_song.upper():
            # Skip - don't add to new output files
            continue
        else:
            # Unchanged song - keep existing output entry
            existing = current_by_title.get(title_upper)
            if existing:
                # Update artist if needed (already done by fix_va_artists.py)
                entry = dict(existing)
                entry['artist'] = artist
                new_output_files.append(entry)
            else:
                print(f'  WARNING: No existing output for "{title}"')
                new_output_files.append({
                    'song_title': title,
                    'artist': artist,
                    'output_uri': s3_uri,
                    'file_size_bytes': 0,
                    'page_range': [start, end],
                })

    print(f'\nNew output_files: {len(new_output_files)} entries')

    # === Step 2: Delete "What If I Loved You, Baby?" ===
    print('\n--- DELETE BOGUS SONG ---')
    wiily_entry = current_by_title.get(delete_song.upper())
    if wiily_entry:
        print(f'  Removing: "{wiily_entry["song_title"]}"')
        old_filename = wiily_entry['output_uri'].split('/')[-1]
        print(f'    File: {old_filename}')

        if not dry_run:
            # Delete from S3
            old_s3_key = wiily_entry['output_uri'].replace(f's3://{S3_OUTPUT_BUCKET}/', '')
            try:
                s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=old_s3_key)
                print(f'    S3: deleted')
            except Exception:
                # Try searching
                found = find_s3_file(s3, S3_OUTPUT_BUCKET, S3_PREFIX, 'What If')
                if found:
                    s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=found)
                    print(f'    S3: found and deleted "{found.split("/")[-1]}"')
                else:
                    print(f'    S3: NOT FOUND')

            # Delete local
            local_candidates = list(OUTPUT_DIR.glob('*What If*'))
            for lf in local_candidates:
                lf.unlink()
                print(f'    Local: deleted "{lf.name}"')
            if not local_candidates:
                print(f'    Local: NOT FOUND')
    else:
        print(f'  Not found in current output_files')

    # === Step 3: Write updated artifacts ===
    print('\n--- UPDATE ARTIFACTS ---')

    if not dry_run:
        # verified_songs.json
        vs_data = {
            'book_id': 'a0ebbf6ec9ecc86e',
            'verified_songs': new_verified,
        }
        with open(ARTIFACTS_DIR / 'verified_songs.json', 'w', encoding='utf-8') as f:
            json.dump(vs_data, f, indent=2, ensure_ascii=False)
        print(f'  verified_songs.json: {len(new_verified)} songs')

        # page_mapping.json
        pm_data = {
            'book_id': 'a0ebbf6ec9ecc86e',
            'offset': corrected['page_mapping']['offset'],
            'confidence': corrected['page_mapping']['confidence'],
            'samples_verified': corrected['page_mapping']['samples_verified'],
            'song_locations': new_locations,
            'mapping_method': corrected['page_mapping']['mapping_method'],
        }
        with open(ARTIFACTS_DIR / 'page_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(pm_data, f, indent=2, ensure_ascii=False)
        print(f'  page_mapping.json: {len(new_locations)} locations')

        # output_files.json
        of_data = {
            'book_id': 'a0ebbf6ec9ecc86e',
            'output_files': new_output_files,
        }
        with open(ARTIFACTS_DIR / 'output_files.json', 'w', encoding='utf-8') as f:
            json.dump(of_data, f, indent=2, ensure_ascii=False)
        print(f'  output_files.json: {len(new_output_files)} entries')

        # Upload all 3 artifacts to S3
        for name in ['verified_songs.json', 'page_mapping.json', 'output_files.json']:
            s3.upload_file(
                str(ARTIFACTS_DIR / name),
                S3_ARTIFACTS_BUCKET,
                f'{S3_PREFIX}{name}',
            )
        print(f'  Artifacts uploaded to S3')
    else:
        print(f'  (dry run - no changes)')

    print(f'\n{"=" * 70}')
    print(f'DONE: {len(new_output_files)} songs total')
    print(f'  - 2 new songs added (Alone Again Or, Knockin\' on Heaven\'s Door)')
    print(f'  - 3 songs re-extracted with corrected page ranges')
    print(f'  - 1 bogus song removed (What If I Loved You, Baby?)')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
