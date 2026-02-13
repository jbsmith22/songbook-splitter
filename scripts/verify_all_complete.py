"""
Comprehensive verification of ALL songbook data.
Physically opens every metadata file, cross-references all fields,
checks for physical output PDFs, and reports all issues.

Usage:
    python scripts/verify_all_complete.py
"""

import json
import os
import sys
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
INPUT_DIR = PROJECT_ROOT / 'SheetMusic_Input'

EXPECTED_ARTIFACTS = [
    'toc_discovery.json', 'toc_parse.json', 'page_analysis.json',
    'page_mapping.json', 'verified_songs.json', 'output_files.json'
]

issues = []
warnings = []
stats = {
    'total_artists': 0,
    'total_books': 0,
    'total_songs': 0,
    'complete_books': 0,
    'missing_artifacts': 0,
    'metadata_mismatches': 0,
    'missing_output_pdfs': 0,
    'missing_input_pdfs': 0,
    'books_with_issues': set(),
}


def add_issue(artist, book, msg):
    issues.append(f"  [{artist} / {book}] {msg}")
    stats['books_with_issues'].add(f"{artist}/{book}")


def add_warning(artist, book, msg):
    warnings.append(f"  [{artist} / {book}] {msg}")


def load_json(path):
    """Load and return JSON, or None on error."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        return {'_error': str(e)}


def verify_book(artist, book, book_dir):
    """Verify all metadata and physical files for a single book."""
    book_issues = 0

    # 1. Check all 6 artifacts exist
    present = []
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        path = book_dir / artifact
        if path.exists() and path.stat().st_size > 0:
            present.append(artifact)
        else:
            missing.append(artifact)

    if missing:
        add_issue(artist, book, f"Missing artifacts: {', '.join(missing)}")
        stats['missing_artifacts'] += len(missing)
        book_issues += 1

    is_complete = len(missing) == 0
    if is_complete:
        stats['complete_books'] += 1

    # 2. Load all metadata files
    vs_data = None
    of_data = None
    pm_data = None

    vs_path = book_dir / 'verified_songs.json'
    of_path = book_dir / 'output_files.json'
    pm_path = book_dir / 'page_mapping.json'

    if vs_path.exists():
        vs_data = load_json(vs_path)
        if vs_data and '_error' in vs_data:
            add_issue(artist, book, f"verified_songs.json parse error: {vs_data['_error']}")
            vs_data = None
            book_issues += 1

    if of_path.exists():
        of_data = load_json(of_path)
        if of_data and '_error' in of_data:
            add_issue(artist, book, f"output_files.json parse error: {of_data['_error']}")
            of_data = None
            book_issues += 1

    if pm_path.exists():
        pm_data = load_json(pm_path)
        if pm_data and '_error' in pm_data:
            add_issue(artist, book, f"page_mapping.json parse error: {pm_data['_error']}")
            pm_data = None
            book_issues += 1

    if not vs_data or not of_data or not pm_data:
        return is_complete, 0, book_issues > 0

    # 3. Extract song lists
    vs_songs = vs_data.get('verified_songs', [])
    of_songs = of_data.get('output_files', [])
    pm_songs = pm_data.get('song_locations', [])

    song_count = len(vs_songs)
    stats['total_songs'] += song_count

    # 4. Check song count consistency
    if len(vs_songs) != len(of_songs):
        add_issue(artist, book, f"Song count mismatch: verified_songs={len(vs_songs)}, output_files={len(of_songs)}")
        stats['metadata_mismatches'] += 1
        book_issues += 1

    if len(vs_songs) != len(pm_songs):
        add_issue(artist, book, f"Song count mismatch: verified_songs={len(vs_songs)}, page_mapping={len(pm_songs)}")
        stats['metadata_mismatches'] += 1
        book_issues += 1

    # 5. Check song title consistency
    vs_titles = [s['song_title'] for s in vs_songs]
    of_titles = [s['song_title'] for s in of_songs]
    pm_titles = [s['song_title'] for s in pm_songs]

    if vs_titles != of_titles:
        vs_set = set(vs_titles)
        of_set = set(of_titles)
        only_vs = vs_set - of_set
        only_of = of_set - vs_set
        if only_vs:
            add_issue(artist, book, f"Songs in verified_songs but not output_files: {only_vs}")
        if only_of:
            add_issue(artist, book, f"Songs in output_files but not verified_songs: {only_of}")
        if not only_vs and not only_of:
            add_issue(artist, book, f"Song ORDER differs between verified_songs and output_files")
        stats['metadata_mismatches'] += 1
        book_issues += 1

    if set(vs_titles) != set(pm_titles):
        vs_set = set(vs_titles)
        pm_set = set(pm_titles)
        only_vs = vs_set - pm_set
        only_pm = pm_set - vs_set
        if only_vs:
            add_issue(artist, book, f"Songs in verified_songs but not page_mapping: {only_vs}")
        if only_pm:
            add_issue(artist, book, f"Songs in page_mapping but not verified_songs: {only_pm}")
        stats['metadata_mismatches'] += 1
        book_issues += 1

    # 6. Check page range consistency (verified_songs vs output_files, positional)
    if len(vs_songs) == len(of_songs):
        for i, (vs_song, of_song) in enumerate(zip(vs_songs, of_songs)):
            pr = of_song.get('page_range', [])
            if len(pr) == 2:
                if pr[0] != vs_song['start_page'] or pr[1] != vs_song['end_page']:
                    add_issue(artist, book,
                        f"Page range mismatch for #{i} '{vs_song['song_title']}': "
                        f"verified=[{vs_song['start_page']},{vs_song['end_page']}), "
                        f"output_files=[{pr[0]},{pr[1]})")
                    stats['metadata_mismatches'] += 1
                    book_issues += 1
            if vs_song['song_title'] != of_song['song_title']:
                add_issue(artist, book,
                    f"Title mismatch at #{i}: verified='{vs_song['song_title']}', "
                    f"output_files='{of_song['song_title']}'")
                stats['metadata_mismatches'] += 1
                book_issues += 1

    # 7. Check pdf_index consistency (verified_songs vs page_mapping, positional)
    if len(vs_songs) == len(pm_songs):
        for i, (vs_song, pm_song) in enumerate(zip(vs_songs, pm_songs)):
            if pm_song['pdf_index'] != vs_song['start_page']:
                add_issue(artist, book,
                    f"pdf_index mismatch for #{i} '{vs_song['song_title']}': "
                    f"verified start_page={vs_song['start_page']}, "
                    f"page_mapping pdf_index={pm_song['pdf_index']}")
                stats['metadata_mismatches'] += 1
                book_issues += 1
            if pm_song['song_title'] != vs_song['song_title']:
                add_issue(artist, book,
                    f"Title mismatch at #{i}: verified='{vs_song['song_title']}', "
                    f"page_mapping='{pm_song['song_title']}'")
                stats['metadata_mismatches'] += 1
                book_issues += 1

    # 8. Check for sequential page boundaries (no gaps, no overlaps)
    for i in range(len(vs_songs) - 1):
        curr = vs_songs[i]
        next_s = vs_songs[i + 1]
        if curr['end_page'] != next_s['start_page']:
            if curr['end_page'] > next_s['start_page']:
                add_issue(artist, book,
                    f"Page OVERLAP: '{curr['song_title']}' ends at {curr['end_page']} "
                    f"but '{next_s['song_title']}' starts at {next_s['start_page']}")
                book_issues += 1
            # Gaps are acceptable (pages between songs)

    # 9. Check book_id consistency across files
    vs_id = vs_data.get('book_id')
    of_id = of_data.get('book_id')
    pm_id = pm_data.get('book_id')
    if vs_id != of_id or vs_id != pm_id:
        add_issue(artist, book,
            f"book_id mismatch: verified={vs_id}, output={of_id}, mapping={pm_id}")
        book_issues += 1

    # 10. Check physical output PDFs exist locally
    output_book_dir = OUTPUT_DIR / artist / book
    if output_book_dir.exists():
        local_pdfs_lower = {f.name.lower(): f.name for f in output_book_dir.iterdir() if f.suffix == '.pdf'}
        expected_pdfs = set()
        for of_song in of_songs:
            uri = of_song.get('output_uri', '')
            filename = uri.split('/')[-1] if '/' in uri else ''
            if filename:
                expected_pdfs.add(filename)

        # Case-insensitive comparison (Windows filesystem is case-insensitive)
        missing_pdfs = {f for f in expected_pdfs if f.lower() not in local_pdfs_lower}
        extra_pdfs = {v for k, v in local_pdfs_lower.items() if k not in {f.lower() for f in expected_pdfs}}
        if missing_pdfs:
            add_warning(artist, book, f"Missing {len(missing_pdfs)} local output PDFs")
            stats['missing_output_pdfs'] += len(missing_pdfs)
        if extra_pdfs:
            add_warning(artist, book, f"Extra {len(extra_pdfs)} local output PDFs not in metadata: {extra_pdfs}")
    else:
        if of_songs:
            add_warning(artist, book, f"No local output directory (expected {len(of_songs)} PDFs)")
            stats['missing_output_pdfs'] += len(of_songs)

    # 11. Check input PDF exists
    input_pdf = INPUT_DIR / artist / f"{artist} - {book}.pdf"
    if not input_pdf.exists():
        add_warning(artist, book, "No local input PDF")
        stats['missing_input_pdfs'] += 1

    return is_complete, song_count, book_issues > 0


def main():
    print("=" * 80)
    print("COMPREHENSIVE SONGBOOK VERIFICATION")
    print("Physically reading every metadata file across all books")
    print("=" * 80)
    print()

    # Scan all artists and books
    artists_seen = set()
    book_results = []

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        if artist.startswith('batch_results'):
            continue

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name
            artists_seen.add(artist)
            stats['total_books'] += 1

            is_complete, song_count, has_issues = verify_book(artist, book, book_dir)
            book_results.append({
                'artist': artist,
                'book': book,
                'is_complete': is_complete,
                'song_count': song_count,
                'has_issues': has_issues,
            })

    stats['total_artists'] = len(artists_seen)

    # Print results
    print(f"SUMMARY")
    print(f"  Artists: {stats['total_artists']}")
    print(f"  Books: {stats['total_books']}")
    print(f"  Complete (6/6 artifacts): {stats['complete_books']}")
    print(f"  Total songs: {stats['total_songs']}")
    print()

    if issues:
        print(f"ISSUES ({len(issues)}):")
        for issue in sorted(issues):
            print(issue)
        print()

    if warnings:
        print(f"WARNINGS ({len(warnings)}):")
        for w in sorted(warnings):
            print(w)
        print()

    books_with_issues = stats['books_with_issues']
    if books_with_issues:
        print(f"BOOKS WITH ISSUES ({len(books_with_issues)}):")
        for b in sorted(books_with_issues):
            print(f"  {b}")
    else:
        print("ALL BOOKS CLEAN - no metadata issues found!")

    print()
    print(f"Missing artifacts: {stats['missing_artifacts']}")
    print(f"Metadata mismatches: {stats['metadata_mismatches']}")
    print(f"Missing local output PDFs: {stats['missing_output_pdfs']}")
    print(f"Missing local input PDFs: {stats['missing_input_pdfs']}")


if __name__ == '__main__':
    main()
