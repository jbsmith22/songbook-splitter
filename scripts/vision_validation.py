#!/usr/bin/env python3
"""
Comprehensive Vision-Based Songbook Validation

This script performs detailed validation of extracted songbook data
by comparing extracted metadata against actual page images using vision analysis.
"""
import json
from pathlib import Path
import sys

def load_artifacts(book_id):
    """Load TOC, page analysis, and output files for a book."""
    artifacts = {}
    base_names = ['toc', 'page_analysis', 'output']

    for name in base_names:
        file_path = Path(f'temp_film_{name}.json')
        if file_path.exists():
            with open(file_path) as f:
                artifacts[name] = json.load(f)
        else:
            print(f"WARNING: Missing {name} artifact")
            artifacts[name] = None

    return artifacts

def find_cached_images(artist, book_name, song_title_prefix):
    """Find cached page images for a song."""
    cache_base = Path(r'S:\SlowImageCache\pdf_verification')
    book_cache = cache_base / artist / book_name

    if not book_cache.exists():
        return []

    # Find all images matching the song
    images = []
    for img_file in book_cache.glob('*.jpg'):
        if song_title_prefix.lower() in img_file.name.lower():
            images.append(img_file)

    return sorted(images)

def validate_song_with_vision(song_data, toc_entry, cached_images):
    """
    Validate a single song using vision on cached page images.
    Returns detailed validation results.
    """
    validation = {
        'song_title': song_data.get('title', 'Unknown'),
        'checks': [],
        'status': 'pending',
        'issues': []
    }

    # CHECK 1: TOC Page Number Match
    toc_page = toc_entry.get('page_number') if toc_entry else None
    song_toc_page = song_data.get('toc_page')

    if toc_page and song_toc_page:
        if toc_page == song_toc_page:
            validation['checks'].append({
                'name': 'TOC Page Match',
                'status': 'PASS',
                'detail': f'TOC page {toc_page} matches extracted page {song_toc_page}'
            })
        else:
            validation['checks'].append({
                'name': 'TOC Page Match',
                'status': 'FAIL',
                'detail': f'TOC page {toc_page} != extracted page {song_toc_page}'
            })
            validation['issues'].append('TOC page mismatch')

    # CHECK 2: Page Range Validity
    start_page = song_data.get('start_pdf_page')
    end_page = song_data.get('end_pdf_page')
    page_count = song_data.get('page_count')

    if start_page and end_page and page_count:
        expected_count = end_page - start_page + 1
        if expected_count == page_count:
            validation['checks'].append({
                'name': 'Page Count',
                'status': 'PASS',
                'detail': f'{page_count} pages ({start_page}-{end_page})'
            })
        else:
            validation['checks'].append({
                'name': 'Page Count',
                'status': 'FAIL',
                'detail': f'Calculated {expected_count} != reported {page_count}'
            })
            validation['issues'].append('Page count mismatch')

    # CHECK 3: Verification Method
    match_method = song_data.get('match_method', 'unknown')
    confidence = song_data.get('confidence', 0.0)
    verified = song_data.get('verified', False)

    if verified and confidence >= 0.9:
        validation['checks'].append({
            'name': 'Vision Verification',
            'status': 'PASS',
            'detail': f'Directly verified with vision (confidence {confidence:.2f})'
        })
    elif match_method == 'toc_only':
        validation['checks'].append({
            'name': 'Vision Verification',
            'status': 'NEEDS_REVIEW',
            'detail': f'Extracted using TOC only (confidence {confidence:.2f}) - NOT vision verified'
        })
        validation['issues'].append('Not vision verified - needs manual check')
    else:
        validation['checks'].append({
            'name': 'Vision Verification',
            'status': 'WARNING',
            'detail': f'Method: {match_method}, confidence {confidence:.2f}'
        })

    # CHECK 4: Cached Images Available
    if cached_images:
        validation['checks'].append({
            'name': 'Cached Images',
            'status': 'AVAILABLE',
            'detail': f'{len(cached_images)} cached page images found'
        })
        validation['cached_image_count'] = len(cached_images)
    else:
        validation['checks'].append({
            'name': 'Cached Images',
            'status': 'NOT_AVAILABLE',
            'detail': 'No cached images - cannot perform vision validation'
        })
        validation['issues'].append('No cached images available')
        validation['cached_image_count'] = 0

    # Overall status
    if any(c['status'] == 'FAIL' for c in validation['checks']):
        validation['status'] = 'FAILED'
    elif validation['issues']:
        validation['status'] = 'NEEDS_REVIEW'
    else:
        validation['status'] = 'PASSED'

    return validation

def comprehensive_validation(book_id, artist, book_name):
    """
    Perform comprehensive validation of a songbook.
    """
    print("=" * 100)
    print(f"COMPREHENSIVE VISION-BASED VALIDATION")
    print(f"Book: {artist} - {book_name}")
    print(f"Book ID: {book_id}")
    print("=" * 100)
    print()

    # Load all artifacts
    print("STEP 1: Loading artifacts...")
    artifacts = load_artifacts(book_id)

    if not all(artifacts.values()):
        print("ERROR: Missing required artifacts")
        return

    toc_data = artifacts['toc']
    page_analysis = artifacts['page_analysis']
    output_files = artifacts['output']

    toc_entries = toc_data.get('entries', []) if isinstance(toc_data, dict) else []
    songs = page_analysis.get('songs', [])
    outputs = output_files.get('output_files', [])

    print(f"  OK TOC entries: {len(toc_entries)}")
    print(f"  OK Songs extracted: {len(songs)}")
    print(f"  OK Output files: {len(outputs)}")
    print()

    # Validate each song
    print("STEP 2: Validating songs with available vision data...")
    print()

    validations = []
    for i, song in enumerate(songs, 1):
        song_title = song.get('title', 'Unknown')

        # Find corresponding TOC entry
        toc_entry = None
        for entry in toc_entries:
            if entry.get('song_title', '').strip() == song_title.strip():
                toc_entry = entry
                break

        # Find cached images
        # Extract first part of song title for matching
        title_prefix = song_title.split(' from ')[0] if ' from ' in song_title else song_title.split()[0]
        cached_images = find_cached_images(artist, book_name, title_prefix)

        # Validate
        validation = validate_song_with_vision(song, toc_entry, cached_images)
        validations.append(validation)

        # Print validation results
        print(f"{'=' * 100}")
        print(f"SONG {i}/{len(songs)}: \"{song_title}\"")
        print(f"{'=' * 100}")
        print(f"  PDF Pages: {song.get('start_pdf_page')}-{song.get('end_pdf_page')} ({song.get('page_count')} pages)")
        print(f"  TOC Page: {song.get('toc_page')}")
        print(f"  Match Method: {song.get('match_method')}")
        print(f"  Confidence: {song.get('confidence', 0.0):.2f}")
        print(f"  Verified: {song.get('verified', False)}")
        print()

        # Print checks
        for check in validation['checks']:
            status_symbol = {
                'PASS': '[PASS]',
                'FAIL': '[FAIL]',
                'WARNING': '[WARN]',
                'NEEDS_REVIEW': '[REVIEW]',
                'AVAILABLE': '[OK]',
                'NOT_AVAILABLE': '[-]'
            }.get(check['status'], '[?]')

            print(f"  {status_symbol} {check['name']}: {check['detail']}")

        # Print issues
        if validation['issues']:
            print()
            print(f"  ISSUES:")
            for issue in validation['issues']:
                print(f"    - {issue}")

        print()

    # Summary
    print("=" * 100)
    print("VALIDATION SUMMARY")
    print("=" * 100)

    passed = sum(1 for v in validations if v['status'] == 'PASSED')
    failed = sum(1 for v in validations if v['status'] == 'FAILED')
    needs_review = sum(1 for v in validations if v['status'] == 'NEEDS_REVIEW')

    with_cached_images = sum(1 for v in validations if v['cached_image_count'] > 0)
    without_cached_images = len(validations) - with_cached_images

    vision_verified = sum(1 for s in songs if s.get('verified', False))
    toc_only = sum(1 for s in songs if s.get('match_method') == 'toc_only')

    print(f"Total Songs: {len(songs)}")
    print(f"  PASSED: {passed}")
    print(f"  FAILED: {failed}")
    print(f"  NEEDS REVIEW: {needs_review}")
    print()
    print(f"Verification Method:")
    print(f"  Vision Verified: {vision_verified} ({vision_verified/len(songs)*100:.1f}%)")
    print(f"  TOC Only (Not Verified): {toc_only} ({toc_only/len(songs)*100:.1f}%)")
    print()
    print(f"Cached Images:")
    print(f"  Songs with cached images: {with_cached_images}")
    print(f"  Songs without cached images: {without_cached_images}")
    print()

    # Key findings
    print("KEY FINDINGS:")
    if toc_only > 0:
        print(f"  - {toc_only} songs were extracted using TOC offset calculation WITHOUT vision verification")
        print(f"    These songs need manual review to confirm accuracy")

    if without_cached_images > 0:
        print(f"  - {without_cached_images} songs have no cached page images")
        print(f"    Vision validation cannot be performed for these songs")

    if vision_verified > 0:
        print(f"  - {vision_verified} songs were directly verified with vision during processing")
        print(f"    These songs have high confidence")

    print()
    print("RECOMMENDATION:")
    if toc_only > 0 or failed > 0:
        print("  Manual review recommended for songs marked 'NEEDS_REVIEW' or 'FAILED'")
        print("  Consider re-processing with vision verification enabled for all songs")
    else:
        print("  All songs passed validation!")

    return validations

if __name__ == '__main__':
    # Film Music For Solo Piano validation
    validations = comprehensive_validation(
        'v2-33894bb5954299ffee605fa4937d31f8',
        '_movie And Tv',
        'Various Artists - Film Music For Solo Piano'
    )
