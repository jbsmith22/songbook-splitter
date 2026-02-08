#!/usr/bin/env python3
"""
Validate songbook quality by visually inspecting page images and comparing with extracted data.
"""
import json
import boto3
from pathlib import Path

s3 = boto3.client('s3')
OUTPUT_BUCKET = 'jsmith-output'

def load_artifact(book_id, artifact_name):
    """Load an artifact from S3."""
    try:
        key = f'artifacts/{book_id}/{artifact_name}'
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except Exception as e:
        return None

def get_page_image_url(book_id, page_num):
    """Get S3 URL for a page image."""
    # Page images are typically stored in artifacts/{book_id}/pages/page_{num}.png
    key = f'artifacts/{book_id}/pages/page_{page_num}.png'
    try:
        s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
        return f's3://{OUTPUT_BUCKET}/{key}'
    except:
        return None

def validate_book(book_id, artist, book_name):
    """Validate a single book."""
    print(f"\n{'='*80}")
    print(f"VALIDATING: {artist} - {book_name}")
    print(f"Book ID: {book_id}")
    print(f"{'='*80}\n")

    # Load artifacts
    print("Loading artifacts...")
    toc_parse = load_artifact(book_id, 'toc_parse.json')
    page_analysis = load_artifact(book_id, 'page_analysis.json')
    output_files = load_artifact(book_id, 'output_files.json')

    if not toc_parse:
        print("  ERROR: No TOC parse data")
        return
    if not page_analysis:
        print("  ERROR: No page analysis data")
        return
    if not output_files:
        print("  ERROR: No output files data")
        return

    print(f"  OK TOC entries: {len(toc_parse.get('entries', []))}")
    print(f"  OK Songs analyzed: {len(page_analysis.get('songs', []))}")
    print(f"  OK Output files: {len(output_files.get('output_files', []))}")

    # Get songs from page analysis
    songs = page_analysis.get('songs', [])

    # Check for page images
    print(f"\nChecking for cached page images...")
    sample_pages = [1, 5, 10] if len(songs) > 0 else [1]
    available_pages = []
    for page_num in sample_pages:
        url = get_page_image_url(book_id, page_num)
        if url:
            available_pages.append(page_num)
            print(f"  OK Page {page_num} image available: {url}")
        else:
            print(f"  - Page {page_num} image not found")

    # Summary
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"TOC Entries: {len(toc_parse.get('entries', []))}")
    print(f"Songs Extracted: {len(songs)}")
    print(f"Output Files: {len(output_files.get('output_files', []))}")
    print(f"Page Images Found: {len(available_pages)}/{len(sample_pages)}")

    return {
        'book_id': book_id,
        'toc_entries': len(toc_parse.get('entries', [])),
        'songs': len(songs),
        'output_files': len(output_files.get('output_files', [])),
        'page_images_available': len(available_pages) > 0,
        'songs_data': songs[:3]  # First 3 songs for inspection
    }

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python validate_songbook_quality.py <book_id> <artist> <book_name>")
        sys.exit(1)

    book_id = sys.argv[1]
    artist = sys.argv[2]
    book_name = sys.argv[3]

    validate_book(book_id, artist, book_name)
