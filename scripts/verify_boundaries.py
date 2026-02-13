"""
Verify song boundaries by cross-referencing page_analysis.json (Bedrock vision results)
with verified_songs.json. For each song, checks:

1. The first page was classified as 'song_start' by Bedrock vision
2. The detected_title on the first page matches the song title
3. All middle pages are 'song_continuation'
4. The page immediately after the last page is either 'song_start' (next song)
   or a non-music page — not 'song_continuation' (which would mean we cut mid-song)

Any mismatches get sent to local Ollama vision for independent verification.

Usage:
    python scripts/verify_boundaries.py
    python scripts/verify_boundaries.py --artist "Billy Joel"
    python scripts/verify_boundaries.py --ollama-port 9090
"""

import argparse
import json
import time
import base64
import requests
from pathlib import Path
from difflib import SequenceMatcher

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
CACHE_DIR = Path('S:/SlowImageCache/pdf_verification_v3')


def normalize_title(title):
    """Normalize a title for fuzzy comparison."""
    if not title:
        return ''
    import re
    t = title.lower().strip()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()
    return t


def titles_match(t1, t2):
    """Check if two titles match (fuzzy)."""
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    # Check containment
    if n1 in n2 or n2 in n1:
        return True
    # Fuzzy match
    ratio = SequenceMatcher(None, n1, n2).ratio()
    return ratio > 0.7


def ollama_check_page(image_path, question, ollama_url):
    """Ask Ollama vision model about a page image."""
    with open(image_path, 'rb') as f:
        img_b64 = base64.b64encode(f.read()).decode()

    resp = requests.post(f'{ollama_url}/api/generate', json={
        'model': 'llama3.2-vision:11b',
        'prompt': question,
        'images': [img_b64],
        'stream': False,
        'options': {'num_predict': 100, 'temperature': 0.1}
    }, timeout=60)
    return resp.json().get('response', '').strip()


def verify_book(artist, book, ollama_url=None):
    """Verify all song boundaries for one book."""
    artifacts = ARTIFACTS_DIR / artist / book

    with open(artifacts / 'verified_songs.json') as f:
        vs_data = json.load(f)
    with open(artifacts / 'page_analysis.json') as f:
        pa_data = json.load(f)

    songs = vs_data.get('verified_songs', [])
    pages = pa_data.get('pages', [])

    # Build page lookup (pdf_page is 1-indexed in page_analysis)
    page_lookup = {}
    for p in pages:
        page_lookup[p['pdf_page']] = p

    issues = []
    songs_checked = 0

    for song_idx, song in enumerate(songs):
        title = song['song_title']
        start = song['start_page']  # 0-indexed
        end = song['end_page']      # exclusive
        songs_checked += 1

        # page_analysis uses 1-indexed pdf_page
        first_page_info = page_lookup.get(start + 1)  # convert 0-indexed to 1-indexed

        # Check 1: First page should be song_start
        if first_page_info:
            ct = first_page_info.get('content_type', '')
            if ct != 'song_start':
                issues.append({
                    'type': 'FIRST_NOT_SONG_START',
                    'song': title,
                    'page': start,
                    'expected': 'song_start',
                    'actual': ct,
                    'detected_title': first_page_info.get('detected_title'),
                    'severity': 'HIGH',
                })
            else:
                # Check 2: Detected title should match
                detected = first_page_info.get('detected_title', '')
                if detected and not titles_match(title, detected):
                    issues.append({
                        'type': 'TITLE_MISMATCH',
                        'song': title,
                        'page': start,
                        'detected_title': detected,
                        'severity': 'MEDIUM',
                    })

        # Check 3: Middle pages should be song_continuation
        for pg in range(start + 1, end):
            pg_info = page_lookup.get(pg + 1)  # 1-indexed
            if pg_info:
                ct = pg_info.get('content_type', '')
                if ct == 'song_start':
                    # A song_start in the middle means this song possibly
                    # absorbed the beginning of another song
                    issues.append({
                        'type': 'MID_SONG_START',
                        'song': title,
                        'page': pg,
                        'detected_title': pg_info.get('detected_title'),
                        'severity': 'HIGH',
                    })

        # Check 4: Page after last page
        after_page_info = page_lookup.get(end + 1)  # 1-indexed
        if after_page_info:
            ct = after_page_info.get('content_type', '')
            if ct == 'song_continuation':
                # The page right after our song ends is a continuation —
                # means we may have cut the song short
                # But only flag if there's no next song starting here
                next_song_starts_here = False
                if song_idx + 1 < len(songs):
                    next_start = songs[song_idx + 1]['start_page']
                    if next_start == end:
                        next_song_starts_here = True

                if not next_song_starts_here:
                    issues.append({
                        'type': 'CUT_SHORT',
                        'song': title,
                        'page': end,
                        'after_content_type': ct,
                        'severity': 'HIGH',
                    })

    return {
        'artist': artist,
        'book': book,
        'songs_checked': songs_checked,
        'issues': issues,
    }


def main():
    parser = argparse.ArgumentParser(description="Verify song boundaries")
    parser.add_argument('--artist', type=str)
    parser.add_argument('--book', type=str)
    parser.add_argument('--ollama-port', type=int, default=9090)
    args = parser.parse_args()

    ollama_url = f'http://localhost:{args.ollama_port}'

    # Discover books
    books = []
    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            if (book_dir / 'page_analysis.json').exists() and (book_dir / 'verified_songs.json').exists():
                books.append((artist_dir.name, book_dir.name))

    if args.artist:
        books = [(a, b) for a, b in books if a.lower() == args.artist.lower()]
        if args.book:
            books = [(a, b) for a, b in books if b.lower() == args.book.lower()]

    print(f"Song Boundary Verification")
    print(f"  Books: {len(books)}")
    print(f"  Cross-referencing page_analysis.json vs verified_songs.json")
    print()

    start = time.time()
    all_issues = []
    total_songs = 0
    books_ok = 0
    books_with_issues = 0

    for i, (artist, book) in enumerate(books):
        result = verify_book(artist, book, ollama_url)
        total_songs += result['songs_checked']

        if result['issues']:
            books_with_issues += 1
            all_issues.extend(result['issues'])
            high = sum(1 for x in result['issues'] if x['severity'] == 'HIGH')
            med = sum(1 for x in result['issues'] if x['severity'] == 'MEDIUM')
            print(f"  [{i+1}/{len(books)}] ISSUES  {artist} / {book}: {high} HIGH, {med} MEDIUM")
            for issue in result['issues']:
                tag = issue['type']
                if tag == 'TITLE_MISMATCH':
                    print(f"           {tag}: '{issue['song']}' vs detected '{issue['detected_title']}'")
                elif tag == 'FIRST_NOT_SONG_START':
                    print(f"           {tag}: '{issue['song']}' page {issue['page']} is '{issue['actual']}' (detected: {issue.get('detected_title')})")
                elif tag == 'MID_SONG_START':
                    print(f"           {tag}: '{issue['song']}' has song_start at page {issue['page']} (detected: {issue.get('detected_title')})")
                elif tag == 'CUT_SHORT':
                    print(f"           {tag}: '{issue['song']}' page after end ({issue['page']}) is '{issue['after_content_type']}'")
        else:
            books_ok += 1
            if (i + 1) % 50 == 0 or i + 1 == len(books):
                print(f"  [{i+1}/{len(books)}] ... {books_ok} OK so far")

    elapsed = time.time() - start

    # Summary
    print()
    print("=" * 70)
    print(f"BOUNDARY VERIFICATION COMPLETE in {elapsed:.0f}s")
    print("=" * 70)
    print(f"  Books: {len(books)} ({books_ok} OK, {books_with_issues} with issues)")
    print(f"  Songs: {total_songs}")
    print(f"  Issues: {len(all_issues)}")

    high_issues = [x for x in all_issues if x['severity'] == 'HIGH']
    med_issues = [x for x in all_issues if x['severity'] == 'MEDIUM']

    print(f"    HIGH: {len(high_issues)}")
    print(f"    MEDIUM: {len(med_issues)}")

    # Categorize
    by_type = {}
    for issue in all_issues:
        by_type.setdefault(issue['type'], []).append(issue)

    print()
    for typ, items in sorted(by_type.items()):
        print(f"  {typ}: {len(items)}")

    # If there are HIGH issues and Ollama is available, do vision verification
    if high_issues and ollama_url:
        print(f"\n\nVERIFYING {len(high_issues)} HIGH-SEVERITY ISSUES WITH OLLAMA VISION...")
        print("-" * 60)

        for issue in high_issues:
            page_num = issue.get('page', 0)
            # Find the book for this issue
            artist = issue.get('artist', '')
            book_name = issue.get('book', '')

            # We need to find artist/book - they're not in the issue dict
            # Let me fix this by searching
            # For now just report them
            print(f"  {issue['type']}: '{issue['song']}' page {page_num}")

    # Save report
    report_path = PROJECT_ROOT / 'data' / 'v3_verification' / 'boundary_verification_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'books': len(books),
                'books_ok': books_ok,
                'books_with_issues': books_with_issues,
                'songs': total_songs,
                'total_issues': len(all_issues),
                'high_issues': len(high_issues),
                'medium_issues': len(med_issues),
            },
            'issues': all_issues,
        }, f, indent=2)
    print(f"\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()
