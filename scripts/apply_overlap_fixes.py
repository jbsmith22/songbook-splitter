#!/usr/bin/env python3
"""
Apply overlap fixes based on vision analysis results.

For each book with clear recommendations:
1. Update verified_songs.json with corrected page ranges
2. Update output_files.json with corrected page_range
3. Re-extract the affected song PDFs from the source PDF
4. Upload fixed artifacts + PDFs to S3
"""

import json
import sys
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

import boto3
import PyPDF2

sys.stdout.reconfigure(line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'


def extract_pages(source_pdf: Path, start_page: int, end_page: int, output_path: Path):
    """Extract pages [start_page, end_page) from source PDF to output_path."""
    with open(source_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        writer = PyPDF2.PdfWriter()
        for page_idx in range(start_page, end_page):
            if page_idx < len(reader.pages):
                writer.add_page(reader.pages[page_idx])
        with open(output_path, 'wb') as out:
            writer.write(out)


def apply_fixes(dry_run: bool = False):
    print('=' * 80)
    print('APPLY OVERLAP FIXES')
    print(f'Mode: {"DRY RUN" if dry_run else "LIVE"}')
    print('=' * 80)
    print()

    # Load analysis results
    results_path = PROJECT_ROOT / 'data' / 'v3_verification' / 'overlap_analysis_results.json'
    with open(results_path) as f:
        analysis = json.load(f)

    s3 = boto3.client('s3', region_name='us-east-1')

    fixes_applied = 0
    pdfs_regenerated = 0

    for book_result in analysis['results']:
        artist = book_result['artist']
        book = book_result['book']

        # Collect all fixes for this book
        fixes = []
        for overlap in book_result['overlaps']:
            rec = overlap.get('recommendation')
            if not rec:
                continue
            fixes.append({
                'song_a': overlap['song_a'],
                'song_b': overlap['song_b'],
                'song_a_range': overlap['song_a_range'],
                'song_b_range': overlap['song_b_range'],
                'new_a_end': rec.get('new_a_end'),
                'new_b_start': rec.get('new_b_start'),
                'reason': rec.get('reason', ''),
            })

        if not fixes:
            continue

        # Skip broken books where songs are crammed into 1-2 pages
        # (fixes would create zero-page or negative ranges)
        vs_path_check = ARTIFACTS_DIR / artist / book / 'verified_songs.json'
        with open(vs_path_check) as f:
            vs_check = json.load(f)
        songs_check = vs_check.get('verified_songs', [])
        unique_ranges = set((s['start_page'], s['end_page']) for s in songs_check)
        if len(unique_ranges) <= 2 and len(songs_check) > 5:
            print(f'SKIP (broken): {artist} / {book} - needs re-processing, not boundary fixes')
            continue

        # Validate no fix would create start >= end
        skip_book = False
        for fix in fixes:
            if fix.get('new_a_end') is not None:
                for s in songs_check:
                    if s['song_title'] == fix['song_a'] and s['start_page'] == fix['song_a_range'][0]:
                        if s['start_page'] >= fix['new_a_end']:
                            print(f'SKIP (invalid): {artist} / {book} - fix would create 0-page song "{fix["song_a"]}"')
                            skip_book = True
                            break
                if skip_book:
                    break
        if skip_book:
            continue

        print(f'{artist} / {book}: {len(fixes)} fixes')

        # Load current artifacts
        book_dir = ARTIFACTS_DIR / artist / book
        vs_path = book_dir / 'verified_songs.json'
        of_path = book_dir / 'output_files.json'

        with open(vs_path) as f:
            vs_data = json.load(f)
        with open(of_path) as f:
            of_data = json.load(f)

        songs = vs_data['verified_songs']
        output_files = of_data['output_files']

        # Build a lookup from song_title to index
        # (handle potential duplicates by tracking which ones we've already fixed)
        affected_songs = set()  # indices of songs that need PDF re-extraction

        for fix in fixes:
            # Find song A and update its end_page
            for i, song in enumerate(songs):
                if song['song_title'] == fix['song_a'] and \
                   song['start_page'] == fix['song_a_range'][0] and \
                   song['end_page'] == fix['song_a_range'][1]:
                    old_end = song['end_page']
                    new_end = fix['new_a_end']
                    if old_end != new_end:
                        print(f'  Fix: "{fix["song_a"]}" end_page {old_end} -> {new_end}')
                        if not dry_run:
                            song['end_page'] = new_end
                            # Update output_files page_range too
                            if i < len(output_files):
                                output_files[i]['page_range'] = [song['start_page'], new_end]
                        affected_songs.add(i)
                    break

            # Find song B and update its start_page (if changed)
            if fix.get('new_b_start') and fix['new_b_start'] != fix['song_b_range'][0]:
                for i, song in enumerate(songs):
                    if song['song_title'] == fix['song_b'] and \
                       song['start_page'] == fix['song_b_range'][0] and \
                       song['end_page'] == fix['song_b_range'][1]:
                        old_start = song['start_page']
                        new_start = fix['new_b_start']
                        print(f'  Fix: "{fix["song_b"]}" start_page {old_start} -> {new_start}')
                        if not dry_run:
                            song['start_page'] = new_start
                            if i < len(output_files):
                                output_files[i]['page_range'] = [new_start, song['end_page']]
                        affected_songs.add(i)
                        break

        if dry_run:
            print(f'  Would update {len(affected_songs)} song PDFs')
            fixes_applied += len(fixes)
            continue

        # Save updated artifacts
        with open(vs_path, 'w', encoding='utf-8') as f:
            json.dump(vs_data, f, indent=2, ensure_ascii=False)
        with open(of_path, 'w', encoding='utf-8') as f:
            json.dump(of_data, f, indent=2, ensure_ascii=False)
        print(f'  Updated artifacts: verified_songs.json, output_files.json')

        # Re-extract affected song PDFs
        source_pdf = INPUT_DIR / artist / f'{artist} - {book}.pdf'
        if not source_pdf.exists():
            print(f'  WARNING: Source PDF not found: {source_pdf}')
            continue

        for idx in affected_songs:
            song = songs[idx]
            of_entry = output_files[idx]
            output_uri = of_entry['output_uri']

            # Parse local output path
            s3_key = output_uri.replace(f's3://{S3_OUTPUT_BUCKET}/', '')
            parts = s3_key.split('/')
            local_path = OUTPUT_DIR / '/'.join(parts[1:])  # skip 'v3/'

            start = song['start_page']
            end = song['end_page']
            page_count = end - start

            print(f'  Re-extracting: "{song["song_title"]}" pages [{start}-{end}) = {page_count} pages')
            local_path.parent.mkdir(parents=True, exist_ok=True)
            extract_pages(source_pdf, start, end, local_path)

            # Update file size
            new_size = local_path.stat().st_size
            of_entry['file_size_bytes'] = new_size

            # Upload to S3
            s3.upload_file(str(local_path), S3_OUTPUT_BUCKET, s3_key)
            print(f'    -> {local_path.name} ({new_size:,} bytes) -> S3')
            pdfs_regenerated += 1

        # Re-save output_files.json with updated sizes
        with open(of_path, 'w', encoding='utf-8') as f:
            json.dump(of_data, f, indent=2, ensure_ascii=False)

        # Upload fixed artifacts to S3
        for artifact_name in ['verified_songs.json', 'output_files.json']:
            local = book_dir / artifact_name
            s3_key = f'v3/{artist}/{book}/{artifact_name}'
            s3.upload_file(str(local), S3_ARTIFACTS_BUCKET, s3_key)
            print(f'  Uploaded artifact: {s3_key}')

        fixes_applied += len(fixes)

    print()
    print('=' * 80)
    print(f'Fixes applied: {fixes_applied}')
    print(f'PDFs regenerated: {pdfs_regenerated}')
    print('=' * 80)


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    apply_fixes(dry_run=dry_run)
