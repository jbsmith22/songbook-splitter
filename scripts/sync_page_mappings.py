"""
Regenerate page_mapping.json from verified_songs.json for books where
boundary fixes were applied via boundary_review_server.py.

The server updates verified_songs.json and output_files.json but not
page_mapping.json. This script brings page_mapping back into sync.

Usage:
    py scripts/sync_page_mappings.py          # dry run
    py scripts/sync_page_mappings.py --apply  # write changes
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'

DRY_RUN = '--apply' not in sys.argv


def sync_book(artist, book):
    """Sync page_mapping.json with verified_songs.json for one book.
    Returns (changed, details_str) or (False, reason)."""
    book_dir = ARTIFACTS_DIR / artist / book
    vs_path = book_dir / 'verified_songs.json'
    pm_path = book_dir / 'page_mapping.json'
    of_path = book_dir / 'output_files.json'

    if not vs_path.exists() or not pm_path.exists():
        return False, 'missing artifacts'

    with open(vs_path, 'r', encoding='utf-8') as f:
        vs_data = json.load(f)
    with open(pm_path, 'r', encoding='utf-8') as f:
        pm_data = json.load(f)
    with open(of_path, 'r', encoding='utf-8') as f:
        of_data = json.load(f)

    vs_songs = vs_data.get('verified_songs', [])
    pm_songs = pm_data.get('song_locations', [])
    of_songs = of_data.get('output_files', [])
    offset = pm_data.get('offset', 0)

    # Check if verified_songs and output_files are in sync
    vs_of_match = len(vs_songs) == len(of_songs)
    if vs_of_match:
        for vs, of in zip(vs_songs, of_songs):
            pr = of.get('page_range', [])
            if len(pr) == 2 and (pr[0] != vs['start_page'] or pr[1] != vs['end_page']):
                vs_of_match = False
                break

    # Check if page_mapping already matches verified_songs
    pm_matches = len(pm_songs) == len(vs_songs)
    if pm_matches:
        for vs, pm in zip(vs_songs, pm_songs):
            if pm['song_title'] != vs['song_title'] or pm['pdf_index'] != vs['start_page']:
                pm_matches = False
                break

    if pm_matches:
        return False, 'already in sync'

    # Regenerate page_mapping song_locations from verified_songs
    new_locations = []
    for song in vs_songs:
        pdf_index = song['start_page']
        printed_page = pdf_index + offset + 1
        new_locations.append({
            'song_title': song['song_title'],
            'printed_page': printed_page,
            'pdf_index': pdf_index,
            'artist': song.get('artist', artist),
        })

    old_count = len(pm_songs)
    new_count = len(new_locations)

    pm_data['song_locations'] = new_locations
    pm_data['samples_verified'] = new_count

    details = f'{old_count} -> {new_count} songs'

    if not DRY_RUN:
        with open(pm_path, 'w', encoding='utf-8') as f:
            json.dump(pm_data, f, indent=2, ensure_ascii=False)
        details += ' [WRITTEN]'

    return True, details


def main():
    if DRY_RUN:
        print('=== DRY RUN (use --apply to write changes) ===\n')
    else:
        print('=== APPLYING CHANGES ===\n')

    changed = 0
    skipped = 0
    errors = 0

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name
            try:
                was_changed, details = sync_book(artist, book)
                if was_changed:
                    print(f'  SYNC: {artist} / {book} — {details}')
                    changed += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f'  ERROR: {artist} / {book} — {e}')
                errors += 1

    print(f'\nResults: {changed} synced, {skipped} already OK, {errors} errors')


if __name__ == '__main__':
    main()
