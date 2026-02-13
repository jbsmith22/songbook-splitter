#!/usr/bin/env python3
"""
Fix 4 books identified during verification:
1. Delete Tom Lehrer / Book Covers (not a real book)
2. Delete John Denver / Back Home Again (just a TOC page)
3. Fix Neil Young / Decade (remove 12 phantom songs at pages 90-91)
4. Re-split Pink Floyd / Anthology from manually corrected splits
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime

import boto3
import PyPDF2

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'
S3_INPUT_BUCKET = 'jsmith-input'
DYNAMO_TABLE = 'jsmith-pipeline-ledger'


def delete_book_everywhere(s3, dynamo_table, artist, book, book_id):
    """Delete a book from local filesystem, S3, and DynamoDB."""
    print(f'\n{"="*60}')
    print(f'DELETING: {artist} / {book} (book_id: {book_id})')
    print(f'{"="*60}')

    # 1. Local artifacts
    local_artifacts = ARTIFACTS_DIR / artist / book
    if local_artifacts.exists():
        shutil.rmtree(local_artifacts)
        print(f'  Deleted local artifacts: {local_artifacts}')
    else:
        print(f'  No local artifacts found')

    # Check if artist dir is now empty
    artist_artifacts_dir = ARTIFACTS_DIR / artist
    if artist_artifacts_dir.exists() and not list(artist_artifacts_dir.iterdir()):
        artist_artifacts_dir.rmdir()
        print(f'  Removed empty artist artifacts dir: {artist_artifacts_dir}')

    # 2. Local output PDFs
    local_output = OUTPUT_DIR / artist / book
    if local_output.exists():
        count = len(list(local_output.glob('*.pdf')))
        shutil.rmtree(local_output)
        print(f'  Deleted local output: {count} PDFs from {local_output}')
    else:
        print(f'  No local output found')

    # 3. S3 artifacts
    prefix = f'v3/{artist}/{book}/'
    deleted = delete_s3_prefix(s3, S3_ARTIFACTS_BUCKET, prefix)
    print(f'  Deleted {deleted} S3 artifacts from s3://{S3_ARTIFACTS_BUCKET}/{prefix}')

    # 4. S3 output PDFs
    deleted = delete_s3_prefix(s3, S3_OUTPUT_BUCKET, prefix)
    print(f'  Deleted {deleted} S3 outputs from s3://{S3_OUTPUT_BUCKET}/{prefix}')

    # 5. DynamoDB entry
    try:
        dynamo_table.delete_item(Key={'book_id': book_id})
        print(f'  Deleted DynamoDB entry for book_id: {book_id}')
    except Exception as e:
        print(f'  DynamoDB delete error: {e}')


def delete_s3_prefix(s3, bucket, prefix):
    """Delete all objects under a prefix."""
    paginator = s3.get_paginator('list_objects_v2')
    to_delete = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            to_delete.append({'Key': obj['Key']})

    if not to_delete:
        return 0

    # Delete in batches of 1000
    count = 0
    for i in range(0, len(to_delete), 1000):
        batch = to_delete[i:i+1000]
        s3.delete_objects(Bucket=bucket, Delete={'Objects': batch})
        count += len(batch)
    return count


def fix_neil_young_decade(s3, dynamo_table):
    """Remove the 12 phantom songs that all map to pages [90-91]."""
    artist = 'Neil Young'
    book = 'Decade'

    print(f'\n{"="*60}')
    print(f'FIXING: {artist} / {book} (removing phantom songs)')
    print(f'{"="*60}')

    book_dir = ARTIFACTS_DIR / artist / book

    # Load current artifacts
    vs_data = json.load(open(book_dir / 'verified_songs.json'))
    of_data = json.load(open(book_dir / 'output_files.json'))
    book_id = vs_data['book_id']

    songs = vs_data['verified_songs']
    output_files = of_data['output_files']

    # Identify phantom songs (all at [90, 91])
    keep_songs = []
    keep_outputs = []
    remove_songs = []

    for i, song in enumerate(songs):
        if song['start_page'] == 90 and song['end_page'] == 91:
            remove_songs.append(song)
        else:
            keep_songs.append(song)
            if i < len(output_files):
                keep_outputs.append(output_files[i])

    print(f'  Original songs: {len(songs)}')
    print(f'  Keeping: {len(keep_songs)}')
    print(f'  Removing: {len(remove_songs)}')

    for song in remove_songs:
        print(f'    - "{song["song_title"]}" [{song["start_page"]}-{song["end_page"]}]')

    # Delete output PDFs for removed songs
    for i, song in enumerate(songs):
        if song['start_page'] == 90 and song['end_page'] == 91:
            if i < len(output_files):
                of_entry = output_files[i]
                output_uri = of_entry.get('output_uri', '')
                s3_key = output_uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')

                # Delete from S3
                if s3_key:
                    try:
                        s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=s3_key)
                        print(f'    Deleted S3: {s3_key}')
                    except Exception as e:
                        print(f'    S3 delete error: {e}')

                # Delete local
                parts = s3_key.split('/')
                if len(parts) >= 4:
                    local_path = OUTPUT_DIR / '/'.join(parts[1:])
                    if local_path.exists():
                        local_path.unlink()
                        print(f'    Deleted local: {local_path.name}')

    # Update artifacts
    vs_data['verified_songs'] = keep_songs
    of_data['output_files'] = keep_outputs

    with open(book_dir / 'verified_songs.json', 'w', encoding='utf-8') as f:
        json.dump(vs_data, f, indent=2, ensure_ascii=False)
    with open(book_dir / 'output_files.json', 'w', encoding='utf-8') as f:
        json.dump(of_data, f, indent=2, ensure_ascii=False)

    # Upload updated artifacts to S3
    for name in ['verified_songs.json', 'output_files.json']:
        s3.upload_file(str(book_dir / name), S3_ARTIFACTS_BUCKET, f'v3/{artist}/{book}/{name}')
        print(f'  Uploaded: v3/{artist}/{book}/{name}')

    print(f'  Done: {len(keep_songs)} songs remaining')


def resplit_pink_floyd(s3, dynamo_table):
    """Re-split Pink Floyd / Anthology using manually corrected splits."""
    artist = 'Pink Floyd'
    book = 'Anthology'

    print(f'\n{"="*60}')
    print(f'RE-SPLITTING: {artist} / {book}')
    print(f'{"="*60}')

    # Load the exported splits
    export_path = PROJECT_ROOT / 'v3_splits_594e8e0eb2c37bd0.json'
    export_data = json.load(open(export_path))

    new_verified_songs = export_data['verified_songs']
    book_id = '23c2eabd71cb94c2'  # Pink Floyd Anthology's actual book_id

    print(f'  New song count: {len(new_verified_songs)}')

    # Source PDF
    source_pdf = INPUT_DIR / artist / f'{artist} - {book}.pdf'
    if not source_pdf.exists():
        print(f'  ERROR: Source PDF not found: {source_pdf}')
        return
    print(f'  Source PDF: {source_pdf}')

    # Delete old output PDFs (local + S3)
    output_prefix = f'v3/{artist}/{book}/'
    deleted = delete_s3_prefix(s3, S3_OUTPUT_BUCKET, output_prefix)
    print(f'  Deleted {deleted} old S3 output PDFs')

    local_output_dir = OUTPUT_DIR / artist / book
    if local_output_dir.exists():
        old_count = len(list(local_output_dir.glob('*.pdf')))
        shutil.rmtree(local_output_dir)
        print(f'  Deleted {old_count} old local output PDFs')
    local_output_dir.mkdir(parents=True, exist_ok=True)

    # Extract new song PDFs
    new_output_files = []
    with open(source_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)
        print(f'  Source PDF has {total_pages} pages')

        for song in new_verified_songs:
            title = song['song_title']
            start = song['start_page']
            end = song['end_page']
            song_artist = song.get('artist', artist)

            # Build filename
            safe_title = title.replace('/', '-').replace('\\', '-').replace(':', '-')
            filename = f'{song_artist} - {safe_title}.pdf'
            local_path = local_output_dir / filename
            s3_key = f'v3/{artist}/{book}/{filename}'
            output_uri = f's3://{S3_OUTPUT_BUCKET}/{s3_key}'

            # Extract pages
            writer = PyPDF2.PdfWriter()
            page_count = 0
            for page_idx in range(start, min(end, total_pages)):
                writer.add_page(reader.pages[page_idx])
                page_count += 1

            if page_count == 0:
                print(f'    SKIP: "{title}" [{start}-{end}] - 0 pages')
                continue

            with open(local_path, 'wb') as out:
                writer.write(out)

            file_size = local_path.stat().st_size

            # Upload to S3
            s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)

            new_output_files.append({
                'song_title': title,
                'artist': song_artist,
                'output_uri': output_uri,
                'file_size_bytes': file_size,
                'page_range': [start, end],
            })

            print(f'    Extracted: "{title}" [{start}-{end}] ({page_count}p, {file_size:,}b)')

    print(f'  Total songs extracted: {len(new_output_files)}')

    # Update artifacts
    book_dir = ARTIFACTS_DIR / artist / book

    # Update verified_songs.json
    vs_data = json.load(open(book_dir / 'verified_songs.json'))
    vs_data['verified_songs'] = new_verified_songs
    with open(book_dir / 'verified_songs.json', 'w', encoding='utf-8') as f:
        json.dump(vs_data, f, indent=2, ensure_ascii=False)

    # Update output_files.json
    of_data = json.load(open(book_dir / 'output_files.json'))
    of_data['output_files'] = new_output_files
    with open(book_dir / 'output_files.json', 'w', encoding='utf-8') as f:
        json.dump(of_data, f, indent=2, ensure_ascii=False)

    # Update page_mapping.json with corrected data
    if 'page_mapping' in export_data:
        pm_data = json.load(open(book_dir / 'page_mapping.json'))
        pm_data['song_locations'] = export_data['page_mapping']['song_locations']
        pm_data['offset'] = export_data['page_mapping']['offset']
        pm_data['confidence'] = export_data['page_mapping']['confidence']
        with open(book_dir / 'page_mapping.json', 'w', encoding='utf-8') as f:
            json.dump(pm_data, f, indent=2, ensure_ascii=False)

    # Upload all updated artifacts to S3
    for name in ['verified_songs.json', 'output_files.json', 'page_mapping.json']:
        local = book_dir / name
        if local.exists():
            s3.upload_file(str(local), S3_ARTIFACTS_BUCKET, f'v3/{artist}/{book}/{name}')
            print(f'  Uploaded artifact: v3/{artist}/{book}/{name}')

    print(f'  Done: {len(new_output_files)} songs')


def main():
    print('=' * 60)
    print('FIX FOUR BOOKS')
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 60)

    s3 = boto3.client('s3', region_name='us-east-1')
    dynamo = boto3.resource('dynamodb', region_name='us-east-1')
    dynamo_table = dynamo.Table(DYNAMO_TABLE)

    # 1. Delete Tom Lehrer / Book Covers
    delete_book_everywhere(s3, dynamo_table, 'Tom Lehrer', 'Book Covers', 'fc19f63800564dea')

    # 2. Delete John Denver / Back Home Again
    delete_book_everywhere(s3, dynamo_table, 'John Denver', 'Back Home Again', '19180cc0756ff16a')

    # 3. Fix Neil Young / Decade
    fix_neil_young_decade(s3, dynamo_table)

    # 4. Re-split Pink Floyd / Anthology
    resplit_pink_floyd(s3, dynamo_table)

    print(f'\n{"="*60}')
    print('ALL DONE')
    print(f'{"="*60}')


if __name__ == '__main__':
    main()
