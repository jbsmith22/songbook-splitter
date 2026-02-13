#!/usr/bin/env python3
"""
Comprehensive V3 Pipeline Data Verification.

Physically verifies every file and metadata record across:
- Input PDFs (local + S3)
- 6 artifact JSONs per book (local + S3, structure validation)
- Cross-artifact consistency (song counts, page ranges, overlaps)
- Output song PDFs (local + S3, size match, page count)
- DynamoDB ledger entries
- Global checks (duplicates, orphans, unprocessed inputs)
"""

import json
import sys
import time
from pathlib import Path
from decimal import Decimal
from datetime import datetime
from collections import defaultdict

import boto3
import PyPDF2

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# === PATHS ===
PROJECT_ROOT = Path(__file__).parent.parent
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

# === S3 ===
S3_INPUT_BUCKET = 'jsmith-input'
S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'

# === DynamoDB ===
DYNAMO_TABLE = 'jsmith-pipeline-ledger'

# === Expected artifacts ===
EXPECTED_ARTIFACTS = [
    'toc_discovery.json',
    'toc_parse.json',
    'page_analysis.json',
    'page_mapping.json',
    'verified_songs.json',
    'output_files.json',
]

# === Report output ===
REPORT_DIR = PROJECT_ROOT / 'data' / 'v3_verification'


class VerificationReport:
    """Collects all verification issues and stats."""

    def __init__(self):
        self.books_checked = 0
        self.books_clean = 0
        self.issues = []  # list of (artist, book, category, message)
        self.stats = defaultdict(int)
        self.book_details = []

    def add_issue(self, artist, book, category, message):
        self.issues.append((artist, book, category, message))

    def add_stat(self, key, value=1):
        self.stats[key] += value

    def summary(self):
        return {
            'books_checked': self.books_checked,
            'books_clean': self.books_clean,
            'books_with_issues': self.books_checked - self.books_clean,
            'total_issues': len(self.issues),
            'stats': dict(self.stats),
        }


def load_s3_inventory(s3, bucket, prefix='v3/'):
    """Pre-load all S3 keys and sizes into a dict for fast lookup."""
    print(f'  Loading S3 inventory: s3://{bucket}/{prefix}')
    inventory = {}
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            inventory[obj['Key']] = obj['Size']
    print(f'    {len(inventory)} objects')
    return inventory


def validate_toc_discovery(data, artist, book, report):
    """Validate toc_discovery.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'toc_discovery: not a dict')
        return
    required = ['book_id', 'toc_pages', 'extracted_text']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'toc_discovery: missing key "{key}"')
    if 'toc_pages' in data and not isinstance(data['toc_pages'], list):
        report.add_issue(artist, book, 'SCHEMA', 'toc_discovery: toc_pages is not a list')
    if 'extracted_text' in data and not isinstance(data['extracted_text'], dict):
        report.add_issue(artist, book, 'SCHEMA', 'toc_discovery: extracted_text is not a dict')


def validate_toc_parse(data, artist, book, report):
    """Validate toc_parse.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'toc_parse: not a dict')
        return
    required = ['book_id', 'entries']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'toc_parse: missing key "{key}"')
    entries = data.get('entries', [])
    if not isinstance(entries, list):
        report.add_issue(artist, book, 'SCHEMA', 'toc_parse: entries is not a list')
    elif len(entries) > 0:
        first = entries[0]
        if not isinstance(first, dict):
            report.add_issue(artist, book, 'SCHEMA', 'toc_parse: entry is not a dict')
        else:
            for key in ['song_title', 'page_number']:
                if key not in first:
                    report.add_issue(artist, book, 'SCHEMA', f'toc_parse: entry missing "{key}"')
    report.add_stat('toc_entries', len(entries))


def validate_page_analysis(data, artist, book, report):
    """Validate page_analysis.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'page_analysis: not a dict')
        return
    required = ['book_id', 'total_pages', 'pages']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'page_analysis: missing key "{key}"')
    total_pages = data.get('total_pages', 0)
    pages_list = data.get('pages', [])
    if not isinstance(pages_list, list):
        report.add_issue(artist, book, 'SCHEMA', 'page_analysis: pages is not a list')
    elif len(pages_list) != total_pages and total_pages > 0:
        report.add_issue(artist, book, 'CONSISTENCY',
                         f'page_analysis: total_pages={total_pages} but pages list has {len(pages_list)} entries')
    return data


def validate_page_mapping(data, artist, book, report):
    """Validate page_mapping.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'page_mapping: not a dict')
        return
    required = ['book_id', 'offset', 'song_locations']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'page_mapping: missing key "{key}"')
    locations = data.get('song_locations', [])
    if not isinstance(locations, list):
        report.add_issue(artist, book, 'SCHEMA', 'page_mapping: song_locations is not a list')
    elif len(locations) > 0:
        first = locations[0]
        if not isinstance(first, dict):
            report.add_issue(artist, book, 'SCHEMA', 'page_mapping: song_location is not a dict')
        else:
            for key in ['song_title', 'pdf_index']:
                if key not in first:
                    report.add_issue(artist, book, 'SCHEMA', f'page_mapping: location missing "{key}"')


def validate_verified_songs(data, artist, book, report):
    """Validate verified_songs.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'verified_songs: not a dict')
        return
    required = ['book_id', 'verified_songs']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'verified_songs: missing key "{key}"')
    songs = data.get('verified_songs', [])
    if not isinstance(songs, list):
        report.add_issue(artist, book, 'SCHEMA', 'verified_songs: verified_songs is not a list')
    elif len(songs) > 0:
        first = songs[0]
        if not isinstance(first, dict):
            report.add_issue(artist, book, 'SCHEMA', 'verified_songs: song entry is not a dict')
        else:
            for key in ['song_title', 'start_page', 'end_page']:
                if key not in first:
                    report.add_issue(artist, book, 'SCHEMA', f'verified_songs: song missing "{key}"')


def validate_output_files(data, artist, book, report):
    """Validate output_files.json structure."""
    if not isinstance(data, dict):
        report.add_issue(artist, book, 'SCHEMA', 'output_files: not a dict')
        return
    required = ['book_id', 'output_files']
    for key in required:
        if key not in data:
            report.add_issue(artist, book, 'SCHEMA', f'output_files: missing key "{key}"')
    files = data.get('output_files', [])
    if not isinstance(files, list):
        report.add_issue(artist, book, 'SCHEMA', 'output_files: output_files is not a list')
    elif len(files) > 0:
        first = files[0]
        if not isinstance(first, dict):
            report.add_issue(artist, book, 'SCHEMA', 'output_files: file entry is not a dict')
        else:
            for key in ['song_title', 'output_uri', 'file_size_bytes', 'page_range']:
                if key not in first:
                    report.add_issue(artist, book, 'SCHEMA', f'output_files: file missing "{key}"')


VALIDATORS = {
    'toc_discovery.json': validate_toc_discovery,
    'toc_parse.json': validate_toc_parse,
    'page_analysis.json': validate_page_analysis,
    'page_mapping.json': validate_page_mapping,
    'verified_songs.json': validate_verified_songs,
    'output_files.json': validate_output_files,
}


def get_pdf_page_count(pdf_path):
    """Get page count from a PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except Exception:
        return None


def verify_book(artist, book_name, report, s3_artifacts_inv, s3_output_inv, s3_input_inv, dynamo_table):
    """Run all verification checks for a single book."""
    book_dir = ARTIFACTS_DIR / artist / book_name
    issues_before = len(report.issues)

    # =========================================================
    # 1. INPUT PDF CHECK
    # =========================================================
    input_filename = f'{artist} - {book_name}.pdf'
    local_input = INPUT_DIR / artist / input_filename
    s3_input_key = f'v3/{artist}/{input_filename}'

    if local_input.exists():
        local_input_size = local_input.stat().st_size
        report.add_stat('input_pdfs_local')
    else:
        local_input_size = None
        report.add_issue(artist, book_name, 'INPUT', f'Missing local input PDF: {input_filename}')

    if s3_input_key in s3_input_inv:
        s3_input_size = s3_input_inv[s3_input_key]
        report.add_stat('input_pdfs_s3')
    else:
        s3_input_size = None
        report.add_issue(artist, book_name, 'INPUT', f'Missing S3 input PDF: {s3_input_key}')

    if local_input_size and s3_input_size and local_input_size != s3_input_size:
        report.add_issue(artist, book_name, 'INPUT',
                         f'Input PDF size mismatch: local={local_input_size}, S3={s3_input_size}')

    # =========================================================
    # 2. ARTIFACT JSON CHECKS (existence, valid JSON, S3 mirror, schema)
    # =========================================================
    artifact_data = {}  # store parsed data for cross-checks

    for artifact_name in EXPECTED_ARTIFACTS:
        local_path = book_dir / artifact_name
        s3_key = f'v3/{artist}/{book_name}/{artifact_name}'

        # Local existence + valid JSON
        if local_path.exists():
            local_size = local_path.stat().st_size
            report.add_stat('artifacts_local')
            try:
                with open(local_path, encoding='utf-8') as f:
                    data = json.load(f)
                if not data:
                    report.add_issue(artist, book_name, 'ARTIFACT', f'{artifact_name}: empty JSON')
                else:
                    artifact_data[artifact_name] = data
                    # Schema validation
                    validator = VALIDATORS.get(artifact_name)
                    if validator:
                        validator(data, artist, book_name, report)
            except json.JSONDecodeError as e:
                report.add_issue(artist, book_name, 'ARTIFACT', f'{artifact_name}: invalid JSON: {e}')
        else:
            report.add_issue(artist, book_name, 'ARTIFACT', f'Missing local artifact: {artifact_name}')
            local_size = None

        # S3 existence
        if s3_key in s3_artifacts_inv:
            s3_size = s3_artifacts_inv[s3_key]
            report.add_stat('artifacts_s3')
        else:
            report.add_issue(artist, book_name, 'ARTIFACT', f'Missing S3 artifact: {s3_key}')
            s3_size = None

        # Size match
        if local_size and s3_size and local_size != s3_size:
            report.add_issue(artist, book_name, 'ARTIFACT',
                             f'{artifact_name}: size mismatch local={local_size} vs S3={s3_size}')

    # =========================================================
    # 3. CROSS-ARTIFACT CONSISTENCY
    # =========================================================
    # All artifacts should have the same book_id
    book_ids = set()
    for name, data in artifact_data.items():
        bid = data.get('book_id')
        if bid:
            book_ids.add(bid)
    if len(book_ids) > 1:
        report.add_issue(artist, book_name, 'CONSISTENCY',
                         f'Multiple book_ids across artifacts: {book_ids}')
    book_id = book_ids.pop() if book_ids else None

    # verified_songs count == output_files count
    vs_data = artifact_data.get('verified_songs.json', {})
    of_data = artifact_data.get('output_files.json', {})
    vs_songs = vs_data.get('verified_songs', [])
    of_files = of_data.get('output_files', [])
    vs_count = len(vs_songs)
    of_count = len(of_files)

    if vs_count > 0 and of_count > 0 and vs_count != of_count:
        report.add_issue(artist, book_name, 'CONSISTENCY',
                         f'Song count mismatch: verified_songs={vs_count}, output_files={of_count}')

    report.add_stat('total_songs_verified', vs_count)
    report.add_stat('total_songs_output', of_count)

    # page_analysis page count consistency
    pa_data = artifact_data.get('page_analysis.json', {})
    total_pages = pa_data.get('total_pages', 0)
    pages_list = pa_data.get('pages', [])

    # Check input PDF page count matches page_analysis.total_pages
    if total_pages > 0 and local_input.exists():
        pdf_pages = get_pdf_page_count(local_input)
        if pdf_pages is not None and pdf_pages != total_pages:
            report.add_issue(artist, book_name, 'CONSISTENCY',
                             f'Input PDF has {pdf_pages} pages but page_analysis says {total_pages}')

    # Check page ranges in verified_songs: no overlaps, within bounds
    if vs_songs and total_pages > 0:
        ranges = []
        for song in vs_songs:
            start = song.get('start_page', 0)
            end = song.get('end_page', 0)
            title = song.get('song_title', '?')

            if start > end:
                report.add_issue(artist, book_name, 'CONSISTENCY',
                                 f'Song "{title}": start_page {start} > end_page {end}')

            # Check bounds (pages are 0-indexed PDF page indices)
            if end > total_pages:  # end_page is exclusive, so == total_pages is valid
                report.add_issue(artist, book_name, 'CONSISTENCY',
                                 f'Song "{title}": end_page {end} > total_pages {total_pages}')

            ranges.append((start, end, title))

        # Check for overlaps (sort by start page)
        ranges.sort(key=lambda x: x[0])
        for i in range(len(ranges) - 1):
            _, end_a, title_a = ranges[i]
            start_b, _, title_b = ranges[i + 1]
            if end_a > start_b:
                report.add_issue(artist, book_name, 'OVERLAP',
                                 f'Page overlap: "{title_a}" ends at {end_a}, '
                                 f'"{title_b}" starts at {start_b}')

    # =========================================================
    # 4. OUTPUT PDF CHECKS
    # =========================================================
    missing_local_outputs = 0
    missing_s3_outputs = 0
    size_mismatches = 0
    page_count_mismatches = 0

    for song_file in of_files:
        output_uri = song_file.get('output_uri', '')
        expected_size = song_file.get('file_size_bytes', 0)
        page_range = song_file.get('page_range', [])
        song_title = song_file.get('song_title', '?')

        # Parse S3 key from URI
        s3_key = output_uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')

        # S3 existence + size
        if s3_key in s3_output_inv:
            s3_size = s3_output_inv[s3_key]
            if expected_size > 0 and s3_size != expected_size:
                size_mismatches += 1
                report.add_issue(artist, book_name, 'OUTPUT',
                                 f'S3 size mismatch for "{song_title}": '
                                 f'recorded={expected_size}, actual={s3_size}')
        else:
            missing_s3_outputs += 1

        # Local existence + size + page count
        # Parse local path from S3 key: v3/Artist/Book/filename.pdf -> Artist/Book/filename.pdf
        parts = s3_key.split('/')
        if len(parts) >= 4:
            local_path = OUTPUT_DIR / '/'.join(parts[1:])  # skip 'v3/'
            if local_path.exists():
                local_size = local_path.stat().st_size
                if expected_size > 0 and local_size != expected_size:
                    size_mismatches += 1
                    report.add_issue(artist, book_name, 'OUTPUT',
                                     f'Local size mismatch for "{song_title}": '
                                     f'recorded={expected_size}, actual={local_size}')

                # PDF page count check
                if len(page_range) == 2:
                    expected_pages = page_range[1] - page_range[0]  # exclusive end
                    actual_pages = get_pdf_page_count(local_path)
                    if actual_pages is not None and actual_pages != expected_pages:
                        page_count_mismatches += 1
                        report.add_issue(artist, book_name, 'PAGE_COUNT',
                                         f'"{song_title}": expected {expected_pages} pages '
                                         f'(range {page_range}), got {actual_pages}')
            else:
                missing_local_outputs += 1

    if missing_local_outputs > 0:
        report.add_issue(artist, book_name, 'OUTPUT',
                         f'{missing_local_outputs} output PDFs missing locally')
    if missing_s3_outputs > 0:
        report.add_issue(artist, book_name, 'OUTPUT',
                         f'{missing_s3_outputs} output PDFs missing from S3')

    report.add_stat('output_pdfs_checked', of_count)
    report.add_stat('output_size_mismatches', size_mismatches)
    report.add_stat('output_page_count_mismatches', page_count_mismatches)

    # =========================================================
    # 5. DYNAMODB LEDGER CHECK
    # =========================================================
    if book_id:
        try:
            resp = dynamo_table.get_item(Key={'book_id': book_id})
            if 'Item' not in resp:
                report.add_issue(artist, book_name, 'DYNAMO', f'No DynamoDB entry for book_id={book_id}')
            else:
                item = resp['Item']
                # Check key fields exist
                for field in ['artist', 'book_name', 'status']:
                    if field not in item:
                        report.add_issue(artist, book_name, 'DYNAMO',
                                         f'DynamoDB entry missing field: {field}')
                # Verify artist/book_name match
                db_artist = item.get('artist', '')
                db_book = item.get('book_name', '')
                if db_artist != artist:
                    report.add_issue(artist, book_name, 'DYNAMO',
                                     f'DynamoDB artist mismatch: "{db_artist}" vs "{artist}"')
                if db_book != book_name:
                    report.add_issue(artist, book_name, 'DYNAMO',
                                     f'DynamoDB book_name mismatch: "{db_book}" vs "{book_name}"')
                report.add_stat('dynamo_entries_found')
        except Exception as e:
            report.add_issue(artist, book_name, 'DYNAMO', f'DynamoDB error: {e}')
    else:
        report.add_issue(artist, book_name, 'DYNAMO', 'No book_id found in artifacts')

    # Track per-book result
    book_issues = len(report.issues) - issues_before
    if book_issues == 0:
        report.books_clean += 1

    return book_id, vs_count


def main():
    start_time = time.time()

    print('=' * 80)
    print('COMPREHENSIVE V3 PIPELINE DATA VERIFICATION')
    print('=' * 80)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    report = VerificationReport()

    # =========================================================
    # PHASE 1: Pre-load S3 inventories
    # =========================================================
    print('PHASE 1: Loading S3 inventories...')
    s3 = boto3.client('s3', region_name='us-east-1')

    s3_input_inv = load_s3_inventory(s3, S3_INPUT_BUCKET, prefix='v3/')
    s3_artifacts_inv = load_s3_inventory(s3, S3_ARTIFACTS_BUCKET, prefix='v3/')
    s3_output_inv = load_s3_inventory(s3, S3_OUTPUT_BUCKET, prefix='v3/')

    report.stats['s3_input_objects'] = len(s3_input_inv)
    report.stats['s3_artifact_objects'] = len(s3_artifacts_inv)
    report.stats['s3_output_objects'] = len(s3_output_inv)

    # DynamoDB
    dynamo = boto3.resource('dynamodb', region_name='us-east-1')
    dynamo_table = dynamo.Table(DYNAMO_TABLE)

    print()

    # =========================================================
    # PHASE 2: Per-book verification
    # =========================================================
    print('PHASE 2: Verifying each book...')
    print()

    all_book_ids = []
    all_output_uris = set()  # track all referenced output URIs

    book_list = []
    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        if artist.startswith('batch_results'):
            continue
        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book_list.append((artist, book_dir.name))

    total = len(book_list)
    print(f'Found {total} books to verify')
    print()

    for i, (artist, book_name) in enumerate(book_list, 1):
        report.books_checked += 1

        if i % 25 == 0 or i == total:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (total - i) / rate if rate > 0 else 0
            print(f'  [{i}/{total}] {artist} / {book_name}  '
                  f'({elapsed:.0f}s elapsed, ~{eta:.0f}s remaining)')

        book_id, song_count = verify_book(
            artist, book_name, report,
            s3_artifacts_inv, s3_output_inv, s3_input_inv,
            dynamo_table
        )

        if book_id:
            all_book_ids.append(book_id)

        # Track referenced output URIs
        of_path = ARTIFACTS_DIR / artist / book_name / 'output_files.json'
        if of_path.exists():
            try:
                with open(of_path) as f:
                    of_data = json.load(f)
                for entry in of_data.get('output_files', []):
                    uri = entry.get('output_uri', '')
                    s3_key = uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')
                    if s3_key:
                        all_output_uris.add(s3_key)
            except Exception:
                pass

    print()

    # =========================================================
    # PHASE 3: Global checks
    # =========================================================
    print('PHASE 3: Global checks...')

    # Duplicate book_ids
    seen_ids = {}
    for bid in all_book_ids:
        if bid in seen_ids:
            report.add_issue('GLOBAL', 'GLOBAL', 'DUPLICATE',
                             f'Duplicate book_id: {bid}')
        seen_ids[bid] = True
    report.stats['unique_book_ids'] = len(seen_ids)

    # Orphan S3 output PDFs (in S3 but not referenced by any output_files.json)
    s3_output_pdfs = {k for k in s3_output_inv if k.endswith('.pdf')}
    orphan_s3 = s3_output_pdfs - all_output_uris
    report.stats['orphan_s3_output_pdfs'] = len(orphan_s3)
    if orphan_s3:
        # Report first 20 as examples
        for key in sorted(orphan_s3)[:20]:
            report.add_issue('GLOBAL', 'GLOBAL', 'ORPHAN', f'Orphan S3 output: {key}')
        if len(orphan_s3) > 20:
            report.add_issue('GLOBAL', 'GLOBAL', 'ORPHAN',
                             f'...and {len(orphan_s3) - 20} more orphan S3 output PDFs')

    # Unprocessed input PDFs
    local_input_count = 0
    for artist_dir in INPUT_DIR.iterdir():
        if not artist_dir.is_dir():
            continue
        for pdf in artist_dir.glob('*.pdf'):
            local_input_count += 1
    report.stats['total_input_pdfs'] = local_input_count
    report.stats['processed_books'] = total
    report.stats['unprocessed_inputs'] = local_input_count - total

    print(f'  Total input PDFs: {local_input_count}')
    print(f'  Processed books: {total}')
    print(f'  Unprocessed: {local_input_count - total}')
    print(f'  Unique book_ids: {len(seen_ids)}')
    print(f'  Orphan S3 output PDFs: {len(orphan_s3)}')

    print()

    # =========================================================
    # PHASE 4: Generate reports
    # =========================================================
    print('PHASE 4: Generating reports...')
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    elapsed = time.time() - start_time

    # JSON report
    json_report = {
        'generated': datetime.now().isoformat(),
        'duration_seconds': round(elapsed, 1),
        'summary': report.summary(),
        'issues': [
            {'artist': a, 'book': b, 'category': c, 'message': m}
            for a, b, c, m in report.issues
        ],
    }

    json_path = REPORT_DIR / 'v3_verification_report.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(json_report, f, indent=2, default=str)
    print(f'  JSON: {json_path}')

    # Text summary
    txt_path = REPORT_DIR / 'v3_verification_report.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('V3 PIPELINE COMPREHENSIVE VERIFICATION REPORT\n')
        f.write('=' * 70 + '\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Duration: {elapsed:.1f} seconds\n\n')

        f.write('SUMMARY\n')
        f.write('-' * 70 + '\n')
        f.write(f'  Books checked:        {report.books_checked}\n')
        f.write(f'  Clean (no issues):    {report.books_clean}\n')
        f.write(f'  With issues:          {report.books_checked - report.books_clean}\n')
        f.write(f'  Total issues found:   {len(report.issues)}\n\n')

        f.write('STATISTICS\n')
        f.write('-' * 70 + '\n')
        for key, val in sorted(report.stats.items()):
            f.write(f'  {key}: {val}\n')
        f.write('\n')

        # Group issues by category
        by_category = defaultdict(list)
        for artist, book, category, message in report.issues:
            by_category[category].append((artist, book, message))

        f.write('ISSUES BY CATEGORY\n')
        f.write('-' * 70 + '\n')
        for category in sorted(by_category.keys()):
            items = by_category[category]
            f.write(f'\n  [{category}] ({len(items)} issues)\n')
            for artist, book, message in items:
                if artist == 'GLOBAL':
                    f.write(f'    {message}\n')
                else:
                    f.write(f'    {artist} / {book}: {message}\n')

        # Group issues by book
        by_book = defaultdict(list)
        for artist, book, category, message in report.issues:
            if artist != 'GLOBAL':
                by_book[(artist, book)].append((category, message))

        if by_book:
            f.write('\n\nISSUES BY BOOK\n')
            f.write('-' * 70 + '\n')
            for (artist, book), items in sorted(by_book.items()):
                f.write(f'\n  {artist} / {book}:\n')
                for category, message in items:
                    f.write(f'    [{category}] {message}\n')

    print(f'  TXT: {txt_path}')

    # Final console output
    print()
    print('=' * 80)
    print('VERIFICATION COMPLETE')
    print('=' * 80)
    print(f'  Duration:           {elapsed:.1f}s')
    print(f'  Books checked:      {report.books_checked}')
    print(f'  Clean (no issues):  {report.books_clean}')
    print(f'  With issues:        {report.books_checked - report.books_clean}')
    print(f'  Total issues:       {len(report.issues)}')
    print()

    if report.issues:
        # Print issue category summary
        by_cat = defaultdict(int)
        for _, _, cat, _ in report.issues:
            by_cat[cat] += 1
        print('  Issue categories:')
        for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
            print(f'    {cat}: {count}')
        print()

    print(f'  Reports saved to: {REPORT_DIR}')

    return 0 if not report.issues else 1


if __name__ == '__main__':
    sys.exit(main())
