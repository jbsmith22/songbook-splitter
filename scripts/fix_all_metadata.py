#!/usr/bin/env python3
"""
Comprehensive metadata fix script.
Canonical truth = artifact folder names on disk.

1. Fix DynamoDB artist, book_name, source_pdf_uri to match artifact folder names
2. Fix S3 input PDF keys to match artifact folder names
3. Update output_files.json file_size_bytes to match actual local file sizes
4. Upload corrected output_files.json to S3
"""

import json
import sys
from pathlib import Path

import boto3

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'
S3_INPUT_BUCKET = 'jsmith-input'
DYNAMO_TABLE = 'jsmith-pipeline-ledger'


def build_s3_inventory(s3, bucket, prefix):
    """Build lowercase -> actual key mapping for an S3 prefix."""
    paginator = s3.get_paginator('list_objects_v2')
    keys = {}
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            keys[key.lower()] = key
    return keys


def fix_dynamo_and_s3_input(s3, dynamo_table, s3_input_keys, dry_run=False):
    """Fix DynamoDB entries and S3 input keys to match artifact folder names."""
    print('\n' + '=' * 70)
    print('PHASE 1: Fix DynamoDB + S3 input casing')
    print('=' * 70)

    dynamo_fixed = 0
    s3_fixed = 0
    errors = 0

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name  # canonical artist name

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name  # canonical book name

            of_path = book_dir / 'output_files.json'
            if not of_path.exists():
                continue

            with open(of_path) as f:
                of_data = json.load(f)
            book_id = of_data.get('book_id')
            if not book_id:
                continue

            # --- Fix DynamoDB ---
            try:
                resp = dynamo_table.get_item(Key={'book_id': book_id})
            except Exception as e:
                print(f'  ERROR getting {book_id}: {e}')
                errors += 1
                continue

            item = resp.get('Item')
            if not item:
                print(f'  MISSING DynamoDB: {artist} / {book} ({book_id})')
                errors += 1
                continue

            db_artist = item.get('artist', '')
            db_book = item.get('book_name', '')
            db_source_uri = item.get('source_pdf_uri', '')

            # Build the correct source_pdf_uri
            # Find the actual input PDF filename (case-insensitive search)
            correct_source_uri = ''
            input_artist_dir = INPUT_DIR / artist
            # Windows is case-insensitive, so this finds the folder regardless of case
            if input_artist_dir.exists():
                for pdf in input_artist_dir.glob('*.pdf'):
                    # Match by book name (case-insensitive)
                    # Input filename: "{Artist} - {Book}.pdf"
                    # The artist part in filename may differ from folder name
                    pdf_lower = pdf.name.lower()
                    expected_lower = f'{artist} - {book}.pdf'.lower()
                    if pdf_lower == expected_lower:
                        # Use artifact casing for the S3 key
                        correct_filename = f'{artist} - {book}.pdf'
                        correct_source_uri = f's3://{S3_INPUT_BUCKET}/v3/{artist}/{correct_filename}'
                        break

            updates = {}
            if db_artist != artist:
                updates['artist'] = artist
            if db_book != book:
                updates['book_name'] = book
            if correct_source_uri and db_source_uri != correct_source_uri:
                updates['source_pdf_uri'] = correct_source_uri

            if updates:
                print(f'  DynamoDB fix: {artist} / {book}')
                for key, val in updates.items():
                    old_val = item.get(key, '')
                    print(f'    {key}: "{old_val}" -> "{val}"')

                if not dry_run:
                    expr_parts = []
                    expr_vals = {}
                    expr_names = {}
                    for i, (key, val) in enumerate(updates.items()):
                        expr_parts.append(f'#{chr(97+i)} = :{chr(97+i)}')
                        expr_names[f'#{chr(97+i)}'] = key
                        expr_vals[f':{chr(97+i)}'] = val

                    try:
                        dynamo_table.update_item(
                            Key={'book_id': book_id},
                            UpdateExpression='SET ' + ', '.join(expr_parts),
                            ExpressionAttributeNames=expr_names,
                            ExpressionAttributeValues=expr_vals,
                        )
                        dynamo_fixed += 1
                    except Exception as e:
                        print(f'    ERROR updating: {e}')
                        errors += 1
                else:
                    dynamo_fixed += 1

            # --- Fix S3 input key ---
            if correct_source_uri:
                correct_s3_key = correct_source_uri.replace(f's3://{S3_INPUT_BUCKET}/', '')
                correct_lower = correct_s3_key.lower()

                # Check if correct key already exists
                if correct_lower in s3_input_keys:
                    actual_key = s3_input_keys[correct_lower]
                    if actual_key != correct_s3_key:
                        print(f'  S3 input fix: "{actual_key}" -> "{correct_s3_key}"')
                        if not dry_run:
                            try:
                                s3.copy_object(
                                    Bucket=S3_INPUT_BUCKET,
                                    Key=correct_s3_key,
                                    CopySource={'Bucket': S3_INPUT_BUCKET, 'Key': actual_key},
                                )
                                s3.delete_object(Bucket=S3_INPUT_BUCKET, Key=actual_key)
                                # Update inventory
                                del s3_input_keys[correct_lower]
                                s3_input_keys[correct_lower] = correct_s3_key
                                s3_fixed += 1
                            except Exception as e:
                                print(f'    ERROR: {e}')
                                errors += 1
                        else:
                            s3_fixed += 1

    print(f'\n  DynamoDB fixes: {dynamo_fixed}')
    print(f'  S3 input fixes: {s3_fixed}')
    print(f'  Errors: {errors}')
    return dynamo_fixed + s3_fixed


def fix_output_file_sizes(s3, dry_run=False):
    """Update output_files.json file_size_bytes to match actual local file sizes."""
    print('\n' + '=' * 70)
    print('PHASE 2: Fix output_files.json file sizes')
    print('=' * 70)

    total_fixed = 0
    books_fixed = 0
    artifacts_uploaded = 0

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name

            of_path = book_dir / 'output_files.json'
            if not of_path.exists():
                continue

            with open(of_path) as f:
                of_data = json.load(f)

            output_files = of_data.get('output_files', [])
            book_changed = False

            for entry in output_files:
                output_uri = entry.get('output_uri', '')
                recorded_size = entry.get('file_size_bytes', 0)

                # Derive local path from output_uri
                s3_key = output_uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')
                parts = s3_key.split('/')
                if len(parts) >= 4:
                    local_path = OUTPUT_DIR / '/'.join(parts[1:])  # skip 'v3/'
                else:
                    continue

                if local_path.exists():
                    actual_size = local_path.stat().st_size
                    if actual_size != recorded_size:
                        if not dry_run:
                            entry['file_size_bytes'] = actual_size
                        book_changed = True
                        total_fixed += 1

            if book_changed:
                books_fixed += 1
                if not dry_run:
                    with open(of_path, 'w', encoding='utf-8') as f:
                        json.dump(of_data, f, indent=2, ensure_ascii=False)

                    s3_key = f'v3/{artist}/{book}/output_files.json'
                    s3.upload_file(str(of_path), S3_ARTIFACTS_BUCKET, s3_key)
                    artifacts_uploaded += 1

    print(f'  Size fixes: {total_fixed} entries across {books_fixed} books')
    print(f'  Artifacts uploaded: {artifacts_uploaded}')
    return total_fixed


def main():
    dry_run = '--dry-run' in sys.argv
    mode = 'DRY RUN' if dry_run else 'LIVE'

    print('=' * 70)
    print(f'COMPREHENSIVE METADATA FIX ({mode})')
    print('=' * 70)

    s3 = boto3.client('s3', region_name='us-east-1')
    dynamo = boto3.resource('dynamodb', region_name='us-east-1')
    dynamo_table = dynamo.Table(DYNAMO_TABLE)

    # Build S3 input inventory once
    print('Loading S3 input inventory...')
    s3_input_keys = build_s3_inventory(s3, S3_INPUT_BUCKET, 'v3/')
    print(f'  {len(s3_input_keys)} S3 input objects')

    # Phase 1: DynamoDB + S3 input casing
    fix_dynamo_and_s3_input(s3, dynamo_table, s3_input_keys, dry_run=dry_run)

    # Phase 2: Output file sizes
    fix_output_file_sizes(s3, dry_run=dry_run)

    print('\n' + '=' * 70)
    print('ALL DONE')
    print('=' * 70)


if __name__ == '__main__':
    main()
