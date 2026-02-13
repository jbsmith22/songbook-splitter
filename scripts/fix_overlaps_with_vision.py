#!/usr/bin/env python3
"""
Fix song page overlaps using ImageCache + Bedrock vision.

For each book with page overlaps in verified_songs.json:
1. Identify the specific overlap pages
2. Load those pages from S:/SlowImageCache/pdf_verification_v2/
3. Send to Bedrock vision to determine what song is on each page
4. Determine the correct boundary
5. Report recommended fixes (and optionally apply them)
"""

import json
import sys
import base64
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import boto3

sys.stdout.reconfigure(line_buffering=True)

# === PATHS ===
PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
CACHE_BASE = Path('S:/SlowImageCache/pdf_verification_v2')

# === Cache name mapping (v3 artifact name -> cache directory name) ===
CACHE_NAME_MAP = {
    ('Frank Zappa', 'The Frank Zappa Guitar Book'):
        ('Frank Zappa', 'The Frank Zappa Guitar Book _transcriptions By Steve Vai_'),
    ('Elvis Presley', 'The Compleat'):
        ('Elvis Presley', 'The Compleat _PVG Book_'),
    ('Various Artists', '62 Stars 62 Hits 60s Compilation'):
        ('Various Artists', '62 Stars 62 Hits _60s Compilation_'),
    ('Various Artists', 'Best Of The 70s And 80s _solo Piano_'):
        ('Various Artists', 'Best Of The 70s And 80s _Solo Piano_'),
    ('Various Artists', 'Country Classics'):
        ('Various Artists', 'Country Classics _PVG_'),
    ('Various Artists', 'Songs Of The 60s'):
        ('Various Artists', 'Songs Of The 60s _PVG_'),
}

VISION_MODEL_ID = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'


def get_cache_dir(artist: str, book: str) -> Optional[Path]:
    """Get the cache directory for a book, applying name mapping."""
    mapped = CACHE_NAME_MAP.get((artist, book), (artist, book))
    cache_dir = CACHE_BASE / mapped[0] / mapped[1]
    if cache_dir.exists():
        return cache_dir
    return None


def load_cache_image(cache_dir: Path, page_idx: int) -> Optional[str]:
    """Load a cached page image and return as base64 string."""
    image_path = cache_dir / f'page_{page_idx:04d}.jpg'
    if not image_path.exists():
        return None
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def analyze_page_with_vision(bedrock, image_b64: str, song_a_title: str,
                              song_b_title: str) -> Dict:
    """Ask Bedrock vision what song is on this page."""
    prompt = f"""Look at this sheet music page carefully.

Two songs that could be on this page:
A) "{song_a_title}"
B) "{song_b_title}"

Determine:
1. Is this a "song_start" page (has a LARGE PROMINENT title at the TOP, music begins here)?
   Or "song_continuation" (music continues from a previous page)?
2. Which song (A or B) does this page belong to? Look at any title text on the page.
3. What is the actual title shown on the page (if visible)?

Respond with ONLY valid JSON:
{{"content_type": "song_start" or "song_continuation", "belongs_to": "A" or "B", "visible_title": "<title if visible, else null>", "confidence": <0.0-1.0>, "reasoning": "<brief explanation>"}}"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 400,
        "temperature": 0,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_b64
                    }
                },
                {"type": "text", "text": prompt}
            ]
        }]
    }

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = bedrock.invoke_model(
                modelId=VISION_MODEL_ID,
                body=json.dumps(request_body)
            )
            response_body = json.loads(response['body'].read())
            text = response_body['content'][0]['text']

            # Parse JSON from response
            text = text.strip()
            if text.startswith('```'):
                text = text.split('\n', 1)[1].rsplit('```', 1)[0].strip()
            return json.loads(text)

        except Exception as e:
            if 'ThrottlingException' in str(e) and attempt < max_retries - 1:
                wait = 2 ** attempt + 1
                print(f'      Throttled, retrying in {wait}s...')
                time.sleep(wait)
                continue
            return {'error': str(e), 'belongs_to': '?', 'confidence': 0}


def find_overlaps(verified_songs: List[Dict]) -> List[Tuple[int, int]]:
    """Find pairs of songs with overlapping page ranges. Returns (idx_a, idx_b) pairs."""
    overlaps = []
    sorted_songs = sorted(enumerate(verified_songs), key=lambda x: x[1].get('start_page', 0))

    for i in range(len(sorted_songs) - 1):
        idx_a, song_a = sorted_songs[i]
        idx_b, song_b = sorted_songs[i + 1]
        if song_a.get('end_page', 0) > song_b.get('start_page', 0):
            overlaps.append((idx_a, idx_b))

    return overlaps


def analyze_overlap(bedrock, cache_dir: Path, song_a: Dict, song_b: Dict) -> Dict:
    """Analyze an overlap between two songs using vision on the overlap pages."""
    overlap_start = song_b['start_page']
    overlap_end = min(song_a['end_page'], song_b['end_page'])

    results = {
        'song_a': song_a['song_title'],
        'song_a_range': [song_a['start_page'], song_a['end_page']],
        'song_b': song_b['song_title'],
        'song_b_range': [song_b['start_page'], song_b['end_page']],
        'overlap_pages': list(range(overlap_start, overlap_end)),
        'page_analyses': [],
        'recommendation': None,
    }

    # Analyze each overlap page
    for page_idx in range(overlap_start, overlap_end):
        print(f'      Analyzing page {page_idx}...')
        image_b64 = load_cache_image(cache_dir, page_idx)
        if not image_b64:
            results['page_analyses'].append({
                'page': page_idx,
                'error': 'No cached image',
                'belongs_to': '?'
            })
            continue

        analysis = analyze_page_with_vision(
            bedrock, image_b64,
            song_a['song_title'], song_b['song_title']
        )
        analysis['page'] = page_idx
        results['page_analyses'].append(analysis)

    # Determine recommendation based on analyses
    # For a 1-page overlap, the key question is: does the overlap page
    # belong to song A (extend A, shrink B) or song B (shrink A, extend B)?
    for analysis in results['page_analyses']:
        belongs = analysis.get('belongs_to', '?')
        content = analysis.get('content_type', '?')
        page = analysis.get('page', -1)

        if belongs == 'B' or content == 'song_start':
            # Page belongs to B: song A should end before this page
            results['recommendation'] = {
                'action': f'Set song A end_page to {page} (was {song_a["end_page"]})',
                'new_a_end': page,
                'new_b_start': page,
                'boundary_page': page,
                'reason': f'Page {page} is start of "{song_b["song_title"]}"'
            }
            break
        elif belongs == 'A':
            # Page belongs to A: song B should start after this page
            results['recommendation'] = {
                'action': f'Set song B start_page to {page + 1} (was {song_b["start_page"]})',
                'new_a_end': page + 1,
                'new_b_start': page + 1,
                'boundary_page': page + 1,
                'reason': f'Page {page} still belongs to "{song_a["song_title"]}"'
            }

    return results


def main():
    print('=' * 80)
    print('FIX SONG OVERLAPS USING IMAGECACHE + BEDROCK VISION')
    print('=' * 80)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

    # Find all books with overlaps
    all_results = []
    books_fixed = 0
    total_overlaps_analyzed = 0

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name

            vs_path = book_dir / 'verified_songs.json'
            if not vs_path.exists():
                continue

            with open(vs_path) as f:
                vs_data = json.load(f)

            songs = vs_data.get('verified_songs', [])
            overlaps = find_overlaps(songs)

            if not overlaps:
                continue

            # Skip completely broken books (all songs same range)
            unique_ranges = set((s['start_page'], s['end_page']) for s in songs)
            if len(unique_ranges) <= 2 and len(songs) > 5:
                print(f'  SKIP (broken): {artist} / {book} - {len(songs)} songs, '
                      f'{len(unique_ranges)} unique ranges')
                continue

            print(f'  {artist} / {book}: {len(overlaps)} overlaps')

            cache_dir = get_cache_dir(artist, book)
            if not cache_dir:
                print(f'    WARNING: No cache found, skipping')
                continue

            book_result = {
                'artist': artist,
                'book': book,
                'overlaps': [],
            }

            for idx_a, idx_b in overlaps:
                song_a = songs[idx_a]
                song_b = songs[idx_b]
                print(f'    Overlap: "{song_a["song_title"]}" [{song_a["start_page"]}-{song_a["end_page"]}] '
                      f'vs "{song_b["song_title"]}" [{song_b["start_page"]}-{song_b["end_page"]}]')

                result = analyze_overlap(bedrock, cache_dir, song_a, song_b)
                book_result['overlaps'].append(result)
                total_overlaps_analyzed += 1

                if result.get('recommendation'):
                    rec = result['recommendation']
                    print(f'      -> {rec["reason"]}')
                    print(f'      -> {rec["action"]}')
                else:
                    print(f'      -> No clear recommendation')

            all_results.append(book_result)
            books_fixed += 1

    # Save results
    report_dir = PROJECT_ROOT / 'data' / 'v3_verification'
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / 'overlap_analysis_results.json'
    with open(report_path, 'w') as f:
        json.dump({
            'generated': datetime.now().isoformat(),
            'total_books': books_fixed,
            'total_overlaps_analyzed': total_overlaps_analyzed,
            'results': all_results,
        }, f, indent=2)

    print()
    print('=' * 80)
    print(f'Analysis complete: {books_fixed} books, {total_overlaps_analyzed} overlaps')
    print(f'Results saved to: {report_path}')
    print('=' * 80)


if __name__ == '__main__':
    main()
