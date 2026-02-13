"""
Comprehensive verification of all V3 pipeline artifacts.

Checks:
1. All 6 artifact JSON files exist locally and in S3
2. Artifact JSON is valid and non-empty
3. Song counts match between verified_songs.json and output_files.json
4. Output PDFs exist locally for each song in output_files.json
5. Output PDFs exist in S3 for each song in output_files.json
6. DynamoDB ledger has an entry for each book
"""

import json
import sys
from pathlib import Path
from decimal import Decimal

import boto3

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'
DYNAMO_TABLE = 'jsmith-pipeline-ledger'

EXPECTED_ARTIFACTS = [
    'toc_discovery.json',
    'toc_parse.json',
    'page_analysis.json',
    'page_mapping.json',
    'verified_songs.json',
    'output_files.json',
]


def verify_book(artist, book_name, s3, dynamo_table, s3_output_keys):
    """Verify a single book. Returns list of issues."""
    issues = []
    book_dir = ARTIFACTS_DIR / artist / book_name

    # 1. Check local artifacts exist and are valid JSON
    for artifact in EXPECTED_ARTIFACTS:
        path = book_dir / artifact
        if not path.exists():
            issues.append(f'MISSING local artifact: {artifact}')
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            if not data:
                issues.append(f'EMPTY artifact: {artifact}')
        except json.JSONDecodeError as e:
            issues.append(f'INVALID JSON in {artifact}: {e}')

    # 2. Check S3 artifacts exist
    for artifact in EXPECTED_ARTIFACTS:
        s3_key = f'v3/{artist}/{book_name}/{artifact}'
        try:
            s3.head_object(Bucket=S3_ARTIFACTS_BUCKET, Key=s3_key)
        except Exception:
            issues.append(f'MISSING S3 artifact: {s3_key}')

    # 3. Check verified_songs vs output_files consistency
    vs_path = book_dir / 'verified_songs.json'
    of_path = book_dir / 'output_files.json'

    vs_count = 0
    of_count = 0
    output_files_data = []

    if vs_path.exists():
        try:
            with open(vs_path) as f:
                vs_data = json.load(f)
            songs = vs_data.get('verified_songs', vs_data)
            if isinstance(songs, list):
                vs_count = len(songs)
        except (json.JSONDecodeError, KeyError):
            pass

    if of_path.exists():
        try:
            with open(of_path) as f:
                of_data = json.load(f)
            output_files_data = of_data.get('output_files', [])
            of_count = len(output_files_data)
        except (json.JSONDecodeError, KeyError):
            pass

    if vs_count > 0 and of_count > 0 and vs_count != of_count:
        issues.append(f'SONG COUNT MISMATCH: verified_songs={vs_count}, output_files={of_count}')

    # 4. Check local output PDFs exist
    missing_local = 0
    for song in output_files_data:
        uri = song.get('output_uri', '')
        # Extract artist/book/filename from s3://jsmith-output/v3/Artist/Book/file.pdf
        parts = uri.replace('s3://jsmith-output/', '').split('/')
        if len(parts) >= 3:
            local_path = OUTPUT_DIR / '/'.join(parts[1:])  # skip 'v3/'
            if not local_path.exists():
                missing_local += 1

    if missing_local > 0:
        issues.append(f'MISSING {missing_local} local output PDFs')

    # 5. Check S3 output PDFs exist (use pre-fetched set)
    missing_s3 = 0
    for song in output_files_data:
        uri = song.get('output_uri', '')
        s3_key = uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')
        if s3_key not in s3_output_keys:
            missing_s3 += 1

    if missing_s3 > 0:
        issues.append(f'MISSING {missing_s3} S3 output PDFs')

    # 6. Check DynamoDB entry
    try:
        resp = dynamo_table.get_item(Key={
            'artist': artist,
            'book_name': book_name,
        })
        if 'Item' not in resp:
            issues.append('MISSING DynamoDB ledger entry')
    except Exception as e:
        issues.append(f'DynamoDB error: {e}')

    return issues, vs_count, of_count


def main():
    print('V3 Pipeline Artifact Verification')
    print('=' * 70)

    # Pre-fetch all S3 output keys for fast lookup
    print('Loading S3 output inventory...')
    s3 = boto3.client('s3')
    paginator = s3.get_paginator('list_objects_v2')
    s3_output_keys = set()
    for page in paginator.paginate(Bucket=S3_OUTPUT_BUCKET, Prefix='v3/'):
        for obj in page.get('Contents', []):
            s3_output_keys.add(obj['Key'])
    print(f'  {len(s3_output_keys)} objects in S3 output bucket')

    # DynamoDB
    dynamo = boto3.resource('dynamodb', region_name='us-east-1')
    dynamo_table = dynamo.Table(DYNAMO_TABLE)

    # Scan all books
    books_checked = 0
    books_clean = 0
    books_with_issues = 0
    total_songs_vs = 0
    total_songs_of = 0
    all_issues = []

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        if artist.startswith('batch_results'):
            continue

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book_name = book_dir.name

            issues, vs_count, of_count = verify_book(
                artist, book_name, s3, dynamo_table, s3_output_keys
            )
            total_songs_vs += vs_count
            total_songs_of += of_count
            books_checked += 1

            if issues:
                books_with_issues += 1
                all_issues.append((artist, book_name, issues))
                print(f'  ISSUES: {artist} / {book_name}')
                for issue in issues:
                    print(f'    - {issue}')
            else:
                books_clean += 1

    # Summary
    print(f'\n{"=" * 70}')
    print(f'VERIFICATION SUMMARY')
    print(f'{"=" * 70}')
    print(f'  Books checked:      {books_checked}')
    print(f'  Clean (no issues):  {books_clean}')
    print(f'  With issues:        {books_with_issues}')
    print(f'  Total songs (verified_songs): {total_songs_vs}')
    print(f'  Total songs (output_files):   {total_songs_of}')
    print(f'  S3 output objects:  {len(s3_output_keys)}')

    if all_issues:
        print(f'\n  ISSUES DETAIL:')
        for artist, book, issues in all_issues:
            print(f'    {artist} / {book}:')
            for issue in issues:
                print(f'      - {issue}')
    else:
        print(f'\n  ALL {books_checked} BOOKS PASSED VERIFICATION')

    return 0 if not all_issues else 1


if __name__ == '__main__':
    sys.exit(main())
