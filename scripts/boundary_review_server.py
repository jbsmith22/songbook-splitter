#!/usr/bin/env python3
"""
Local server for the Boundary Review viewer.
Serves static files AND handles split execution via API.

Usage:
    python scripts/boundary_review_server.py
    python scripts/boundary_review_server.py --port 8080
    python scripts/boundary_review_server.py --dry-run

Then open: http://localhost:8080/web/editors/boundary_review.html
"""

import argparse
import json
import os
import shutil
import sys
import time
import traceback
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import unquote

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'

DRY_RUN = False


def sanitize_filename(title, artist):
    """Create a safe filename from song title and artist."""
    safe = title.replace('/', '-').replace('\\', '-').replace(':', '-')
    safe = safe.replace('?', '').replace('"', '').replace('<', '')
    safe = safe.replace('>', '').replace('|', '').replace('*', '')
    return f'{artist} - {safe}.pdf'


def apply_absorption_fix(artist, book, split_pages, merge_pages=None):
    """
    Fix song boundaries by splitting and/or merging.

    For each split_page:
    1. Find the song in verified_songs that contains this page
    2. Truncate that song to end at split_page
    3. Insert a new song starting at split_page, ending at the original end
    4. The new song's title comes from page_analysis.json detected_title

    For each merge_page:
    1. Find the song starting at merge_page
    2. Extend the previous song's end_page to cover it
    3. Remove the merged song

    Merges are applied first, then splits (to avoid index conflicts).
    Returns dict with results.
    """
    book_dir = ARTIFACTS_DIR / artist / book
    result = {
        'artist': artist,
        'book': book,
        'status': 'ok',
        'changes': [],
        'errors': [],
    }

    # Load artifacts
    try:
        vs_path = book_dir / 'verified_songs.json'
        of_path = book_dir / 'output_files.json'
        pa_path = book_dir / 'page_analysis.json'

        with open(vs_path, encoding='utf-8') as f:
            vs_data = json.load(f)
        with open(of_path, encoding='utf-8') as f:
            of_data = json.load(f)
        with open(pa_path, encoding='utf-8') as f:
            pa_data = json.load(f)
    except Exception as e:
        result['status'] = 'error'
        result['errors'].append(f'Failed to load artifacts: {e}')
        return result

    songs = vs_data['verified_songs']
    book_id = vs_data.get('book_id', of_data.get('book_id', ''))

    # Build page_analysis lookup (1-indexed pdf_page -> info)
    pa_lookup = {}
    for p in pa_data.get('pages', []):
        pa_lookup[p['pdf_page']] = p

    # === Process merges first (in reverse order to avoid index shifts) ===
    if merge_pages:
        for merge_page in sorted(merge_pages, reverse=True):
            # Find the song starting at this page
            merge_idx = None
            for i, song in enumerate(songs):
                if song['start_page'] == merge_page:
                    merge_idx = i
                    break

            if merge_idx is None:
                result['errors'].append(f'Merge page {merge_page}: no song starts here')
                continue

            if merge_idx == 0:
                result['errors'].append(f'Merge page {merge_page}: cannot merge the first song')
                continue

            merged_song = songs[merge_idx]
            prev_song = songs[merge_idx - 1]
            old_prev_end = prev_song['end_page']

            # Extend previous song to cover the merged one
            prev_song['end_page'] = merged_song['end_page']
            songs.pop(merge_idx)

            change = {
                'action': 'merge',
                'page': merge_page,
                'merged_song': merged_song['song_title'],
                'into_song': prev_song['song_title'],
                'new_range': [prev_song['start_page'], prev_song['end_page']],
            }
            result['changes'].append(change)
            print(f'  Merge "{merged_song["song_title"]}" into "{prev_song["song_title"]}" -> [{prev_song["start_page"]}-{prev_song["end_page"]}]')

    # === Process splits (in reverse order to avoid index shifts) ===
    split_pages_sorted = sorted(split_pages, key=lambda s: s['page'])

    for split_info in reversed(split_pages_sorted):
        split_page = split_info['page']  # 0-indexed
        detected_title = split_info.get('detected_title')

        # If no detected title provided, look it up from page_analysis
        if not detected_title:
            pa_info = pa_lookup.get(split_page + 1)  # page_analysis is 1-indexed
            if pa_info:
                detected_title = pa_info.get('detected_title', f'Unknown (page {split_page})')
            else:
                detected_title = f'Unknown (page {split_page})'

        # Find the song that contains this page
        containing_idx = None
        for i, song in enumerate(songs):
            if song['start_page'] <= split_page < song['end_page']:
                containing_idx = i
                break

        if containing_idx is None:
            result['errors'].append(
                f'Page {split_page}: no song contains this page'
            )
            continue

        old_song = songs[containing_idx]
        old_end = old_song['end_page']
        old_title = old_song['song_title']

        if split_page == old_song['start_page']:
            result['errors'].append(
                f'Page {split_page}: is already the start of "{old_title}"'
            )
            continue

        # Truncate the absorbing song
        old_song['end_page'] = split_page

        # Create the new song
        new_song = {
            'song_title': detected_title,
            'start_page': split_page,
            'end_page': old_end,
            'artist': old_song.get('artist', artist),
        }

        # Insert after the truncated song
        songs.insert(containing_idx + 1, new_song)

        change = {
            'action': 'split',
            'page': split_page,
            'original_song': old_title,
            'original_range': [old_song['start_page'], old_end],
            'truncated_to': [old_song['start_page'], split_page],
            'new_song': detected_title,
            'new_range': [split_page, old_end],
        }
        result['changes'].append(change)
        print(f'  Split "{old_title}" at page {split_page} -> new song "{detected_title}" [{split_page}-{old_end}]')

    if not result['changes']:
        result['status'] = 'no_changes'
        return result

    if DRY_RUN:
        result['status'] = 'dry_run'
        print(f'  DRY RUN — not writing anything')
        return result

    # === Now re-extract PDFs ===
    source_pdf = INPUT_DIR / artist / f'{artist} - {book}.pdf'
    if not source_pdf.exists():
        result['status'] = 'error'
        result['errors'].append(f'Source PDF not found: {source_pdf}')
        return result

    try:
        import fitz  # PyMuPDF
    except ImportError:
        result['status'] = 'error'
        result['errors'].append('PyMuPDF (fitz) not installed. Run: pip install PyMuPDF')
        return result

    # Delete old output PDFs locally
    local_output_dir = OUTPUT_DIR / artist / book
    if local_output_dir.exists():
        old_count = len(list(local_output_dir.glob('*.pdf')))
        shutil.rmtree(local_output_dir)
        print(f'  Deleted {old_count} old local PDFs')
    local_output_dir.mkdir(parents=True, exist_ok=True)

    # Re-extract all songs from source PDF
    doc = fitz.open(str(source_pdf))
    total_pages = len(doc)
    new_output_files = []

    for song in songs:
        title = song['song_title']
        start = song['start_page']
        end = song['end_page']
        song_artist = song.get('artist', artist)

        filename = sanitize_filename(title, song_artist)
        local_path = local_output_dir / filename
        s3_key = f'v3/{artist}/{book}/{filename}'
        output_uri = f's3://{S3_OUTPUT_BUCKET}/{s3_key}'

        page_count = min(end, total_pages) - start
        if page_count <= 0:
            print(f'    SKIP: "{title}" [{start}-{end}] — 0 pages')
            continue

        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start, to_page=min(end, total_pages) - 1)
        new_doc.save(str(local_path))
        new_doc.close()

        file_size = local_path.stat().st_size
        new_output_files.append({
            'song_title': title,
            'artist': song_artist,
            'output_uri': output_uri,
            'file_size_bytes': file_size,
            'page_range': [start, end],
        })

    doc.close()
    print(f'  Extracted {len(new_output_files)} song PDFs locally')

    # Update verified_songs.json
    vs_data['verified_songs'] = songs
    with open(vs_path, 'w', encoding='utf-8') as f:
        json.dump(vs_data, f, indent=2, ensure_ascii=False)

    # Update output_files.json
    of_data['output_files'] = new_output_files
    with open(of_path, 'w', encoding='utf-8') as f:
        json.dump(of_data, f, indent=2, ensure_ascii=False)

    print(f'  Updated local artifacts')

    # Upload to S3
    try:
        import boto3
        s3 = boto3.client('s3', region_name='us-east-1')

        # Delete old S3 output
        output_prefix = f'v3/{artist}/{book}/'
        paginator = s3.get_paginator('list_objects_v2')
        to_delete = []
        for page in paginator.paginate(Bucket=S3_OUTPUT_BUCKET, Prefix=output_prefix):
            for obj in page.get('Contents', []):
                to_delete.append({'Key': obj['Key']})
        if to_delete:
            for i in range(0, len(to_delete), 1000):
                s3.delete_objects(Bucket=S3_OUTPUT_BUCKET, Delete={'Objects': to_delete[i:i+1000]})
            print(f'  Deleted {len(to_delete)} old S3 output PDFs')

        # Upload new song PDFs
        for entry in new_output_files:
            uri = entry['output_uri']
            s3_key = uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')
            local_path = local_output_dir / sanitize_filename(entry['song_title'], entry['artist'])
            s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)
        print(f'  Uploaded {len(new_output_files)} song PDFs to S3')

        # Upload updated artifacts
        for name in ['verified_songs.json', 'output_files.json']:
            local = book_dir / name
            if local.exists():
                s3.upload_file(str(local), S3_ARTIFACTS_BUCKET, f'v3/{artist}/{book}/{name}')
        print(f'  Uploaded artifacts to S3')

    except Exception as e:
        result['errors'].append(f'S3 upload failed: {e}')
        print(f'  WARNING: S3 upload failed: {e}')
        print(f'  Local files are updated. Re-run with AWS credentials to sync S3.')

    result['new_song_count'] = len(new_output_files)
    result['old_song_count'] = len(of_data['output_files'])  # already updated, but we logged it
    return result


class BoundaryReviewHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves static files and handles API calls."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PROJECT_ROOT), **kwargs)

    def do_POST(self):
        if self.path == '/api/apply-fix':
            self.handle_apply_fix()
        elif self.path == '/api/preview-fix':
            self.handle_preview_fix()
        else:
            self.send_error(404, 'Not found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_preview_fix(self):
        """Preview what a fix would do without executing it."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            artist = body['artist']
            book = body['book']
            split_pages = body.get('splits', [])
            merge_pages = body.get('merges', [])

            # Load current state
            book_dir = ARTIFACTS_DIR / artist / book
            with open(book_dir / 'verified_songs.json', encoding='utf-8') as f:
                vs_data = json.load(f)
            with open(book_dir / 'page_analysis.json', encoding='utf-8') as f:
                pa_data = json.load(f)

            songs = [dict(s) for s in vs_data['verified_songs']]  # deep copy
            pa_lookup = {p['pdf_page']: p for p in pa_data.get('pages', [])}

            changes = []

            # Preview merges first (reverse order)
            for merge_page in sorted(merge_pages, reverse=True):
                for i, song in enumerate(songs):
                    if song['start_page'] == merge_page and i > 0:
                        prev = songs[i - 1]
                        changes.append({
                            'action': 'merge',
                            'page': merge_page,
                            'merged_song': song['song_title'],
                            'into_song': prev['song_title'],
                        })
                        prev['end_page'] = song['end_page']
                        songs.pop(i)
                        break

            # Preview splits (reverse order)
            for split_info in sorted(split_pages, key=lambda s: s['page'], reverse=True):
                split_page = split_info['page']
                detected_title = split_info.get('detected_title')
                if not detected_title:
                    pa_info = pa_lookup.get(split_page + 1)
                    detected_title = pa_info.get('detected_title', '?') if pa_info else '?'

                for i, song in enumerate(songs):
                    if song['start_page'] <= split_page < song['end_page']:
                        old_end = song['end_page']
                        song['end_page'] = split_page
                        new_song = {
                            'song_title': detected_title,
                            'start_page': split_page,
                            'end_page': old_end,
                            'artist': song.get('artist', artist),
                        }
                        songs.insert(i + 1, new_song)
                        changes.append({
                            'action': 'split',
                            'original': song['song_title'],
                            'new_song': detected_title,
                            'page': split_page,
                            'original_range': [song['start_page'], old_end],
                        })
                        break

            response = {
                'status': 'preview',
                'changes': changes,
                'new_song_count': len(songs),
                'old_song_count': len(vs_data['verified_songs']),
            }
            self.send_json(200, response)

        except Exception as e:
            self.send_json(500, {'status': 'error', 'error': str(e)})

    def handle_apply_fix(self):
        """Execute boundary fixes (splits and/or merges)."""
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))

            artist = body['artist']
            book = body['book']
            split_pages = body.get('splits', [])
            merge_pages = body.get('merges', [])

            print(f'\n=== APPLY FIX: {artist} / {book} ({len(split_pages)} splits, {len(merge_pages)} merges) ===')

            result = apply_absorption_fix(artist, book, split_pages, merge_pages)
            self.send_json(200, result)

        except Exception as e:
            traceback.print_exc()
            self.send_json(500, {'status': 'error', 'error': str(e)})

    def send_json(self, code, data):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Suppress routine static file logs, show API calls
        if '/api/' in (args[0] if args else ''):
            super().log_message(format, *args)


def main():
    parser = argparse.ArgumentParser(description='Boundary Review server')
    parser.add_argument('--port', type=int, default=8080)
    parser.add_argument('--dry-run', action='store_true', help='Preview only, do not modify files')
    args = parser.parse_args()

    global DRY_RUN
    DRY_RUN = args.dry_run

    os.chdir(PROJECT_ROOT)

    server = HTTPServer(('localhost', args.port), BoundaryReviewHandler)
    url = f'http://localhost:{args.port}/web/editors/boundary_review.html'
    print(f'Boundary Review Server')
    print(f'  Serving: {PROJECT_ROOT}')
    print(f'  Port: {args.port}')
    print(f'  Dry run: {DRY_RUN}')
    print(f'  Open: {url}')
    print(f'  Press Ctrl+C to stop\n')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nShutting down.')
        server.shutdown()


if __name__ == '__main__':
    main()
