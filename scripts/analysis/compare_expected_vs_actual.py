"""
Compare expected songs (from TOC) vs actual files present for Carole King - Tapestry
"""
import json
import boto3
from pathlib import Path

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'
book_id = '9518734e91bae95e'

print('='*80)
print('EXPECTED vs ACTUAL FILES: Carole King - Tapestry')
print('='*80)

# Load the complete page lineage data
with open('data/analysis/complete_page_lineage.json', 'r') as f:
    data = json.load(f)

# Find Carole King - Tapestry
book_data = None
for book in data['books']:
    if 'Carole King' in book.get('book_name', '') and 'Tapestry' in book.get('book_name', ''):
        book_data = book
        break

if not book_data:
    print('Book not found!')
    exit()

# Get expected songs from TOC
toc_entries = book_data.get('toc_entries', [])
extracted_songs = book_data.get('extracted_songs', [])
local_songs = book_data.get('local_songs', [])

print(f'\n1. SONGS FROM TABLE OF CONTENTS ({len(toc_entries)} expected)')
print('-'*80)
for i, entry in enumerate(toc_entries, 1):
    print(f'{i:2d}. {entry["title"]:50s} (TOC page {entry["toc_page"]})')

print(f'\n2. SONGS IN EXTRACTION LIST ({len(extracted_songs)} extracted)')
print('-'*80)
extracted_titles = set()
for song in extracted_songs:
    title = song['title']
    extracted_titles.add(title.lower())
    pages = f"{song['page_start']}-{song['page_end']}"
    print(f'  {title:50s} Pages {pages:8s} ({song["page_count"]} pages)')

print(f'\n3. ACTUAL LOCAL FILES ({len(local_songs)} files)')
print('-'*80)
# Check local folder
archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
local_folder = archive_root / 'Carole King' / 'Carole King - Tapestry'

if local_folder.exists():
    actual_files = list(local_folder.glob('*.pdf'))
    print(f'Location: {local_folder}')
    print(f'Files present: {len(actual_files)}\n')

    for i, file in enumerate(sorted(actual_files), 1):
        size_mb = file.stat().st_size / (1024*1024)
        print(f'{i:2d}. {file.name:60s} {size_mb:6.2f} MB')
else:
    print('Local folder not found!')
    actual_files = []

print(f'\n4. ACTUAL S3 FILES')
print('-'*80)
# List S3 files
s3_path = 'archive/completed/Carole King/Carole King - Tapestry'
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=BUCKET, Prefix=s3_path + '/')

s3_files = []
for page in pages:
    if 'Contents' in page:
        for obj in page['Contents']:
            if obj['Key'].endswith('.pdf'):
                s3_files.append({
                    'key': obj['Key'],
                    'filename': obj['Key'].split('/')[-1],
                    'size': obj['Size'] / (1024*1024)
                })

print(f'Location: s3://{BUCKET}/{s3_path}')
print(f'Files present: {len(s3_files)}\n')

for i, file in enumerate(sorted(s3_files, key=lambda x: x['filename']), 1):
    print(f'{i:2d}. {file["filename"]:60s} {file["size"]:6.2f} MB')

print(f'\n5. COMPARISON ANALYSIS')
print('-'*80)

# Check which TOC entries are missing from extraction list
print('\nSongs in TOC but NOT in extraction list:')
toc_titles = {entry['title'].lower() for entry in toc_entries}
missing_from_extraction = toc_titles - extracted_titles
if missing_from_extraction:
    for title in sorted(missing_from_extraction):
        print(f'  - {title}')
else:
    print('  None - all TOC songs were extracted')

# Check which files exist that match TOC entries
print('\nTOC entries matched to actual files:')
local_filenames = {f.name.lower() for f in actual_files}
for entry in toc_entries:
    title = entry['title']
    # Try to find matching file
    found = False
    for filename in local_filenames:
        if title.lower().replace(' ', '').replace('?', '') in filename.replace(' ', '').replace('?', '').replace('-', ''):
            found = True
            break
    status = '[FOUND]' if found else '[MISSING]'
    print(f'  {status} - {title}')

# Compare local vs S3
print('\nLocal vs S3 file comparison:')
local_names = {f.name for f in actual_files}
s3_names = {f['filename'] for f in s3_files}

if local_names == s3_names:
    print('  [OK] Local and S3 have identical files')
else:
    missing_s3 = local_names - s3_names
    extra_s3 = s3_names - local_names
    if missing_s3:
        print(f'  [ERROR] In local but not S3: {missing_s3}')
    if extra_s3:
        print(f'  [WARNING] In S3 but not local: {extra_s3}')

print('\n' + '='*80)
print('END OF COMPARISON')
print('='*80)
