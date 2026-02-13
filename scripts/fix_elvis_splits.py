#!/usr/bin/env python3
"""
Fix Elvis Presley / The Compleat: add missing "Don't" and "Love Me Tender".

Changes:
1. Baby I Don't Care: pages 71-77 → 71-74 (re-extract)
2. Don't: NEW, pages 74-77
3. Love Me: pages 151-155 → 151-153 (re-extract)
4. Love Me Tender: NEW, pages 153-155
"""

import json
import sys
from pathlib import Path

import boto3
from pypdf import PdfReader, PdfWriter

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts' / 'Elvis Presley' / 'The Compleat'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output' / 'Elvis Presley' / 'The Compleat'
INPUT_PDF = PROJECT_ROOT / 'SheetMusic_Input' / 'Elvis Presley' / 'Elvis Presley - The Compleat.pdf'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'
S3_PREFIX = 'v3/Elvis Presley/The Compleat/'

BOOK_ID = '56b73750ba517905'
ARTIST = 'Elvis Presley'

INVALID_CHARS = '?"<>|*'


def safe_filename(title, artist):
    safe = title
    for ch in '/\\:' + INVALID_CHARS:
        safe = safe.replace(ch, '-' if ch in '/\\:' else '')
    return f'{artist} - {safe}.pdf'


def extract_pages(reader, start_page, end_page, output_path):
    writer = PdfWriter()
    for page_idx in range(start_page, end_page):
        writer.add_page(reader.pages[page_idx])
    with open(output_path, 'wb') as f:
        writer.write(f)
    return output_path.stat().st_size


def main():
    dry_run = '--dry-run' in sys.argv
    print(f'FIX ELVIS PRESLEY / THE COMPLEAT ({"DRY RUN" if dry_run else "LIVE"})')
    print('=' * 70)

    # Load current artifacts
    with open(ARTIFACTS_DIR / 'verified_songs.json') as f:
        vs_data = json.load(f)
    with open(ARTIFACTS_DIR / 'output_files.json') as f:
        of_data = json.load(f)
    with open(ARTIFACTS_DIR / 'page_mapping.json') as f:
        pm_data = json.load(f)

    songs = vs_data['verified_songs']
    outputs = of_data['output_files']
    locations = pm_data['song_locations']

    print(f'Current: {len(songs)} songs')

    # Build output lookup by title
    output_by_title = {e['song_title'].upper(): e for e in outputs}

    s3 = boto3.client('s3', region_name='us-east-1')

    # Check source PDF
    if not INPUT_PDF.exists():
        print(f'ERROR: Source PDF not found: {INPUT_PDF}')
        sys.exit(1)
    reader = PdfReader(str(INPUT_PDF))
    print(f'Source PDF: {len(reader.pages)} pages')

    # === Fix 1: Split "Baby I Don't Care" (71-77) ===
    bidc_idx = next(i for i, s in enumerate(songs) if "BABY I DON'T CARE" in s['song_title'].upper())
    bidc = songs[bidc_idx]
    print(f'\n[{bidc_idx}] "{bidc["song_title"]}": pages {bidc["start_page"]}-{bidc["end_page"]}')

    # Shrink Baby I Don't Care to 71-74
    bidc['end_page'] = 74
    print(f'  -> pages {bidc["start_page"]}-{bidc["end_page"]}')

    # Insert "Don't" at 74-77
    dont_song = {
        'song_title': "Don't",
        'start_page': 74,
        'end_page': 77,
        'artist': ARTIST,
    }
    songs.insert(bidc_idx + 1, dont_song)
    print(f'  + "Don\'t": pages 74-77')

    # === Fix 2: Split "Love Me" (151-155) ===
    lm_idx = next(i for i, s in enumerate(songs) if s['song_title'].upper() == 'LOVE ME')
    lm = songs[lm_idx]
    print(f'\n[{lm_idx}] "{lm["song_title"]}": pages {lm["start_page"]}-{lm["end_page"]}')

    # Shrink Love Me to 151-153
    lm['end_page'] = 153
    print(f'  -> pages {lm["start_page"]}-{lm["end_page"]}')

    # Insert "Love Me Tender" at 153-155
    lmt_song = {
        'song_title': 'Love Me Tender',
        'start_page': 153,
        'end_page': 155,
        'artist': ARTIST,
    }
    songs.insert(lm_idx + 1, lmt_song)
    print(f'  + "Love Me Tender": pages 153-155')

    print(f'\nNew total: {len(songs)} songs')

    # === Extract/re-extract PDFs ===
    print('\n--- PDF EXTRACTION ---')

    affected = {
        "BABY I DON'T CARE": (71, 74),
        "DON'T": (74, 77),
        "LOVE ME": (151, 153),
        "LOVE ME TENDER": (153, 155),
    }

    new_outputs = []
    for song in songs:
        title = song['song_title']
        title_upper = title.upper()
        start = song['start_page']
        end = song['end_page']
        filename = safe_filename(title, ARTIST)
        s3_key = f'{S3_PREFIX}{filename}'
        s3_uri = f's3://{S3_OUTPUT_BUCKET}/{s3_key}'

        if title_upper in affected:
            print(f'  EXTRACT: "{title}" (pages {start}-{end})')
            print(f'    -> {filename}')

            if not dry_run:
                local_path = OUTPUT_DIR / filename
                file_size = extract_pages(reader, start, end, local_path)
                print(f'    Local: {file_size:,} bytes')

                s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)
                print(f'    S3: uploaded')

                # Delete old S3 file if it had different name/size
                if title_upper in output_by_title:
                    old_entry = output_by_title[title_upper]
                    old_key = old_entry['output_uri'].replace(f's3://{S3_OUTPUT_BUCKET}/', '')
                    if old_key != s3_key:
                        try:
                            s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=old_key)
                            print(f'    S3: deleted old key')
                        except Exception:
                            pass
            else:
                file_size = 0

            new_outputs.append({
                'song_title': title,
                'artist': ARTIST,
                'output_uri': s3_uri,
                'file_size_bytes': file_size,
                'page_range': [start, end],
            })
        else:
            # Keep existing entry
            existing = output_by_title.get(title_upper)
            if existing:
                new_outputs.append(existing)
            else:
                print(f'  WARNING: No existing output for "{title}"')

    # === Update page_mapping locations ===
    # Add new locations for Don't and Love Me Tender
    dont_loc = {
        'song_title': "Don't",
        'printed_page': 73,
        'pdf_index': 74,
        'artist': ARTIST,
    }
    lmt_loc = {
        'song_title': 'Love Me Tender',
        'printed_page': 152,
        'pdf_index': 153,
        'artist': ARTIST,
    }
    locations.append(dont_loc)
    locations.append(lmt_loc)
    locations.sort(key=lambda x: x['pdf_index'])

    # === Write artifacts ===
    print('\n--- UPDATE ARTIFACTS ---')
    if not dry_run:
        vs_data['verified_songs'] = songs
        with open(ARTIFACTS_DIR / 'verified_songs.json', 'w', encoding='utf-8') as f:
            json.dump(vs_data, f, indent=2, ensure_ascii=False)
        print(f'  verified_songs.json: {len(songs)} songs')

        pm_data['song_locations'] = locations
        with open(ARTIFACTS_DIR / 'page_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(pm_data, f, indent=2, ensure_ascii=False)
        print(f'  page_mapping.json: {len(locations)} locations')

        of_data['output_files'] = new_outputs
        with open(ARTIFACTS_DIR / 'output_files.json', 'w', encoding='utf-8') as f:
            json.dump(of_data, f, indent=2, ensure_ascii=False)
        print(f'  output_files.json: {len(new_outputs)} entries')

        for name in ['verified_songs.json', 'page_mapping.json', 'output_files.json']:
            s3.upload_file(
                str(ARTIFACTS_DIR / name),
                S3_ARTIFACTS_BUCKET,
                f'{S3_PREFIX}{name}',
            )
        print(f'  Artifacts uploaded to S3')
    else:
        print(f'  (dry run - no changes)')

    # Verify contiguity
    print('\nVerifying page contiguity:')
    gaps = 0
    for i in range(len(songs) - 1):
        if songs[i]['end_page'] != songs[i+1]['start_page']:
            print(f'  GAP: "{songs[i]["song_title"]}" ends {songs[i]["end_page"]}, "{songs[i+1]["song_title"]}" starts {songs[i+1]["start_page"]}')
            gaps += 1
    if gaps == 0:
        print('  All contiguous.')

    print(f'\n{"=" * 70}')
    print(f'DONE: {len(new_outputs)} songs')
    print(f'  + Don\'t (pages 74-77)')
    print(f'  + Love Me Tender (pages 153-155)')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
