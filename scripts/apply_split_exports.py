#!/usr/bin/env python3
"""
Apply manually corrected splits from exported v3_splits JSON files.

For each export:
1. Replace verified_songs in artifacts
2. Delete old output PDFs (local + S3)
3. Re-extract song PDFs from source
4. Update output_files.json with new sizes
5. Upload everything to S3
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

import boto3
import fitz  # PyMuPDF - more robust with corrupt PDFs than PyPDF2

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'


def delete_s3_prefix(s3, bucket, prefix):
    """Delete all objects under a prefix."""
    paginator = s3.get_paginator('list_objects_v2')
    to_delete = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            to_delete.append({'Key': obj['Key']})
    if not to_delete:
        return 0
    for i in range(0, len(to_delete), 1000):
        batch = to_delete[i:i+1000]
        s3.delete_objects(Bucket=bucket, Delete={'Objects': batch})
    return len(to_delete)


def apply_export(s3, export_path, artist, book):
    """Apply an exported splits file to a book."""
    print(f'\n{"="*60}')
    print(f'RE-SPLITTING: {artist} / {book}')
    print(f'  From: {export_path.name}')
    print(f'{"="*60}')

    export_data = json.load(open(export_path, encoding='utf-8'))
    new_verified_songs = export_data['verified_songs']
    book_dir = ARTIFACTS_DIR / artist / book

    # Get book_id from existing artifact
    of_data = json.load(open(book_dir / 'output_files.json'))
    book_id = of_data['book_id']
    old_count = len(of_data['output_files'])

    print(f'  book_id: {book_id}')
    print(f'  Old songs: {old_count} -> New songs: {len(new_verified_songs)}')

    # Source PDF
    source_pdf = INPUT_DIR / artist / f'{artist} - {book}.pdf'
    if not source_pdf.exists():
        print(f'  ERROR: Source PDF not found: {source_pdf}')
        return
    print(f'  Source: {source_pdf.name}')

    # Delete old output PDFs
    output_prefix = f'v3/{artist}/{book}/'
    deleted = delete_s3_prefix(s3, S3_OUTPUT_BUCKET, output_prefix)
    print(f'  Deleted {deleted} old S3 output PDFs')

    local_output_dir = OUTPUT_DIR / artist / book
    if local_output_dir.exists():
        old_local = len(list(local_output_dir.glob('*.pdf')))
        shutil.rmtree(local_output_dir)
        print(f'  Deleted {old_local} old local output PDFs')
    local_output_dir.mkdir(parents=True, exist_ok=True)

    # Extract new song PDFs using PyMuPDF (handles corrupt PDFs)
    new_output_files = []
    doc = fitz.open(str(source_pdf))
    total_pages = len(doc)
    print(f'  PDF pages: {total_pages}')

    for song in new_verified_songs:
        title = song['song_title']
        start = song['start_page']
        end = song['end_page']
        song_artist = song.get('artist', artist)

        safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-').replace('?', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '').replace('*', '')
        filename = f'{song_artist} - {safe_title}.pdf'
        local_path = local_output_dir / filename
        s3_key = f'v3/{artist}/{book}/{filename}'
        output_uri = f's3://{S3_OUTPUT_BUCKET}/{s3_key}'

        page_count = min(end, total_pages) - start
        if page_count <= 0:
            print(f'    SKIP: "{title}" [{start}-{end}] - 0 pages')
            continue

        # Extract pages using PyMuPDF
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=min(end, total_pages) - 1)
        new_doc.save(str(local_path))
        new_doc.close()

        file_size = local_path.stat().st_size
        s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)

        new_output_files.append({
            'song_title': title,
            'artist': song_artist,
            'output_uri': output_uri,
            'file_size_bytes': file_size,
            'page_range': [start, end],
        })

    doc.close()
    print(f'  Extracted: {len(new_output_files)} songs')

    # Update artifacts
    vs_data = json.load(open(book_dir / 'verified_songs.json'))
    vs_data['verified_songs'] = new_verified_songs
    with open(book_dir / 'verified_songs.json', 'w', encoding='utf-8') as f:
        json.dump(vs_data, f, indent=2, ensure_ascii=False)

    of_data['output_files'] = new_output_files
    with open(book_dir / 'output_files.json', 'w', encoding='utf-8') as f:
        json.dump(of_data, f, indent=2, ensure_ascii=False)

    # Update page_mapping if present in export
    if 'page_mapping' in export_data:
        pm_path = book_dir / 'page_mapping.json'
        pm_data = json.load(open(pm_path))
        pm_data['song_locations'] = export_data['page_mapping']['song_locations']
        pm_data['offset'] = export_data['page_mapping']['offset']
        pm_data['confidence'] = export_data['page_mapping']['confidence']
        with open(pm_path, 'w', encoding='utf-8') as f:
            json.dump(pm_data, f, indent=2, ensure_ascii=False)

    # Upload updated artifacts
    for name in ['verified_songs.json', 'output_files.json', 'page_mapping.json']:
        local = book_dir / name
        if local.exists():
            s3.upload_file(str(local), S3_ARTIFACTS_BUCKET, f'v3/{artist}/{book}/{name}')
    print(f'  Uploaded artifacts to S3')
    print(f'  Done!')


def main():
    if len(sys.argv) < 2:
        print('Usage: apply_split_exports.py <export1.json> <artist1> <book1> [<export2.json> <artist2> <book2> ...]')
        print('  Or: apply_split_exports.py --batch')
        sys.exit(1)

    s3 = boto3.client('s3', region_name='us-east-1')

    if sys.argv[1] == '--batch':
        # Hardcoded batch for current fixes
        jobs = [
            ('v3_splits_594e8e0eb2c37bd0 (1).json', 'Elvis Presley', 'The Compleat'),
            ('v3_splits_594e8e0eb2c37bd0 (2).json', 'Frank Zappa', 'The Frank Zappa Guitar Book'),
            ('v3_splits_594e8e0eb2c37bd0 (3).json', 'The Band', 'The Band And Music From Big Pink'),
        ]
        for export_name, artist, book in jobs:
            export_path = PROJECT_ROOT / export_name
            apply_export(s3, export_path, artist, book)
    else:
        # Parse args as triplets
        args = sys.argv[1:]
        for i in range(0, len(args), 3):
            export_path = PROJECT_ROOT / args[i]
            artist = args[i + 1]
            book = args[i + 2]
            apply_export(s3, export_path, artist, book)

    print(f'\nAll done!')


if __name__ == '__main__':
    main()
