"""
Detailed analysis of Carole King - Tapestry artifacts
"""
import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'
book_id = '9518734e91bae95e'

print('='*80)
print('DETAILED ARTIFACT ANALYSIS: Carole King - Tapestry')
print(f'Book ID: {book_id}')
print('='*80)

# 1. TOC Discovery
print('\n1. TOC DISCOVERY (toc_discovery.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/toc_discovery.json')
    toc_discovery = json.loads(obj['Body'].read())

    print(f'Timestamp: {toc_discovery.get("timestamp", "N/A")}')
    print(f'Total pages scanned: {toc_discovery.get("total_pages", "N/A")}')
    print(f'TOC pages found: {len(toc_discovery.get("toc_pages", []))}')

    if toc_discovery.get('toc_pages'):
        print(f'\nTOC Page numbers:')
        for page_info in toc_discovery['toc_pages']:
            print(f'  - Page {page_info.get("page_number")}: confidence {page_info.get("confidence", 0):.2f}')
except Exception as e:
    print(f'Error: {e}')

# 2. TOC Parse
print('\n\n2. TOC PARSE (toc_parse.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/toc_parse.json')
    toc_parse = json.loads(obj['Body'].read())

    print(f'Timestamp: {toc_parse.get("timestamp", "N/A")}')
    print(f'Songs extracted from TOC: {len(toc_parse.get("songs", []))}')

    if toc_parse.get('songs'):
        print(f'\nSongs from Table of Contents:')
        for i, song in enumerate(toc_parse['songs'], 1):
            title = song.get('title', 'Untitled')
            page = song.get('page_number', '?')
            print(f'  {i:2d}. "{title}" - Page {page}')
except Exception as e:
    print(f'Error: {e}')

# 3. Page Mapping
print('\n\n3. PAGE MAPPING (page_mapping.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/page_mapping.json')
    page_mapping = json.loads(obj['Body'].read())

    print(f'Timestamp: {page_mapping.get("timestamp", "N/A")}')
    print(f'Total page ranges: {len(page_mapping.get("page_ranges", []))}')

    if page_mapping.get('page_ranges'):
        print(f'\nPage ranges for each song:')
        for mapping in page_mapping['page_ranges']:
            title = mapping.get('title', 'Untitled')
            start = mapping.get('start_page', '?')
            end = mapping.get('end_page', '?')
            pages = mapping.get('page_count', '?')
            print(f'  "{title}": pages {start}-{end} ({pages} pages)')
except Exception as e:
    print(f'Error: {e}')

# 4. Verified Songs
print('\n\n4. VERIFIED SONGS (verified_songs.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/verified_songs.json')
    verified_songs = json.loads(obj['Body'].read())

    print(f'Timestamp: {verified_songs.get("timestamp", "N/A")}')
    print(f'Verified songs: {len(verified_songs.get("songs", []))}')
    print(f'Failed songs: {len(verified_songs.get("failed", []))}')

    if verified_songs.get('songs'):
        print(f'\nVerified songs with metadata:')
        for song in verified_songs['songs']:
            title = song.get('title', 'Untitled')
            composer = song.get('composer', 'Unknown')
            pages = song.get('page_count', '?')
            status = song.get('verification_status', 'unknown')
            print(f'  "{title}"')
            print(f'    Composer: {composer}')
            print(f'    Pages: {pages}')
            print(f'    Status: {status}')
except Exception as e:
    print(f'Error: {e}')

# 5. Output Files
print('\n\n5. OUTPUT FILES (output_files.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/output_files.json')
    output_files = json.loads(obj['Body'].read())

    print(f'Timestamp: {output_files.get("timestamp", "N/A")}')
    print(f'Files generated: {len(output_files.get("files", []))}')

    if output_files.get('files'):
        print(f'\nGenerated output files:')
        for file_info in output_files['files']:
            filename = file_info.get('filename', 'unknown')
            size = file_info.get('size', 0)
            created = file_info.get('created', 'N/A')
            print(f'  {filename}')
            print(f'    Size: {size:,} bytes')
            print(f'    Created: {created}')
except Exception as e:
    print(f'Error: {e}')

# 6. Manifest
print('\n\n6. MANIFEST (manifest.json)')
print('-' * 80)
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'output/{book_id}/manifest.json')
    manifest = json.loads(obj['Body'].read())

    print(f'Book Name: {manifest.get("book_name", "N/A")}')
    print(f'Book ID: {manifest.get("book_id", "N/A")}')
    print(f'Source PDF: {manifest.get("source_pdf", "N/A")}')
    print(f'Total Songs: {len(manifest.get("songs", []))}')
    print(f'Created: {manifest.get("created_date", "N/A")}')
    print(f'Local Path: {manifest.get("local_path", "N/A")}')
    print(f'S3 Path: {manifest.get("s3_path", "N/A")}')

    if manifest.get('songs'):
        print(f'\nSongs in manifest:')
        for i, song in enumerate(manifest['songs'], 1):
            title = song.get('title', 'Untitled')
            output_path = song.get('output_path', 'N/A')
            page_start = song.get('page_start', '?')
            page_end = song.get('page_end', '?')
            print(f'  {i:2d}. "{title}"')
            print(f'      Pages: {page_start}-{page_end}')
            print(f'      Output: {output_path}')
except Exception as e:
    print(f'Error: {e}')

# 7. Check for TOC images
print('\n\n7. TOC IMAGES')
print('-' * 80)
try:
    # List all files in artifacts folder
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET, Prefix=f'artifacts/{book_id}/')

    toc_images = []
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if 'toc' in key.lower() and (key.endswith('.png') or key.endswith('.jpg')):
                    toc_images.append(key)

    if toc_images:
        print(f'Found {len(toc_images)} TOC images:')
        for img in toc_images:
            print(f'  s3://{BUCKET}/{img}')
    else:
        print('No TOC images found')
except Exception as e:
    print(f'Error: {e}')

print('\n' + '='*80)
print('END OF DETAILED ANALYSIS')
print('='*80)
