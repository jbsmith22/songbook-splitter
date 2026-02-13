#!/usr/bin/env python3
"""Check all books for discrepancies between TOC entries and verified songs."""

import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

artifacts = Path(__file__).parent.parent / 'SheetMusic_Artifacts'
issues = []

for artist_dir in sorted(artifacts.iterdir()):
    if not artist_dir.is_dir():
        continue
    for book_dir in sorted(artist_dir.iterdir()):
        if not book_dir.is_dir():
            continue

        toc_path = book_dir / 'toc_parse.json'
        vs_path = book_dir / 'verified_songs.json'
        of_path = book_dir / 'output_files.json'

        if not vs_path.exists():
            continue

        with open(vs_path) as f:
            vs = json.load(f)
        verified = vs.get('verified_songs', [])

        # Check toc_parse vs verified_songs
        if toc_path.exists():
            with open(toc_path) as f:
                toc = json.load(f)
            toc_entries = toc.get('entries', [])

            if toc_entries:
                toc_titles = {e['song_title'].upper().strip() for e in toc_entries}
                vs_titles = {s['song_title'].upper().strip() for s in verified}

                missing = toc_titles - vs_titles
                extra = vs_titles - toc_titles

                # Fuzzy matching to reduce false positives from minor title differences
                real_missing = set()
                for m in missing:
                    matched = False
                    for v in vs_titles:
                        if m[:20] == v[:20] or v[:20] == m[:20]:
                            matched = True
                            break
                        if m in v or v in m:
                            matched = True
                            break
                    if not matched:
                        real_missing.add(m)

                real_extra = set()
                for e in extra:
                    matched = False
                    for t in toc_titles:
                        if e[:20] == t[:20] or t[:20] == e[:20]:
                            matched = True
                            break
                        if e in t or t in e:
                            matched = True
                            break
                    if not matched:
                        real_extra.add(e)

                if real_missing or real_extra:
                    issues.append({
                        'artist': artist_dir.name,
                        'book': book_dir.name,
                        'toc_count': len(toc_entries),
                        'vs_count': len(verified),
                        'missing': sorted(real_missing),
                        'extra': sorted(real_extra),
                    })

        # Also check output_files vs verified_songs count
        if of_path.exists():
            with open(of_path) as f:
                of_data = json.load(f)
            outputs = of_data.get('output_files', [])
            if len(outputs) != len(verified):
                artist = artist_dir.name
                book = book_dir.name
                existing = [i for i in issues if i['artist'] == artist and i['book'] == book]
                if existing:
                    existing[0]['of_count'] = len(outputs)
                else:
                    issues.append({
                        'artist': artist,
                        'book': book,
                        'toc_count': None,
                        'vs_count': len(verified),
                        'of_count': len(outputs),
                        'missing': [],
                        'extra': [],
                        'note': f'output_files ({len(outputs)}) != verified_songs ({len(verified)})'
                    })

print(f'Books with discrepancies: {len(issues)}')
print('=' * 80)
for issue in sorted(issues, key=lambda x: (x['artist'], x['book'])):
    artist = issue['artist']
    book = issue['book']
    toc_n = issue.get('toc_count', '?')
    vs_n = issue['vs_count']
    of_n = issue.get('of_count', vs_n)

    print(f'\n{artist} / {book}')
    print(f'  TOC: {toc_n} | Verified: {vs_n} | Output: {of_n}')

    if issue['missing']:
        print(f'  MISSING from verified (in TOC but not extracted):')
        for m in issue['missing']:
            print(f'    - {m}')
    if issue['extra']:
        print(f'  EXTRA in verified (not in TOC):')
        for e in issue['extra']:
            print(f'    - {e}')
    if issue.get('note'):
        print(f'  NOTE: {issue["note"]}')
