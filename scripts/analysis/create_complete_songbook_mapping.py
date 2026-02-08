"""
Create comprehensive CSV mapping: Source PDF -> Local Folder -> S3 Folder
"""
from pathlib import Path
import json
import csv
import boto3

print('Creating comprehensive songbook mapping...')

# Get all source PDFs
sheet_music = Path('d:/Work/songbook-splitter/SheetMusic')
all_source_pdfs = {p.relative_to(sheet_music).as_posix(): None for p in sheet_music.glob('**/*.pdf')}
print(f'Found {len(all_source_pdfs)} source PDFs in SheetMusic')

# Get all local folders (both current and archived)
processed_songs = Path('d:/Work/songbook-splitter/ProcessedSongs')
archive_songs = Path('d:/Work/songbook-splitter/ProcessedSongs_Archive')

local_folders = set()
for folder in processed_songs.glob('*/*'):
    if folder.is_dir():
        local_folders.add(folder.relative_to(processed_songs).as_posix())

for folder in archive_songs.glob('*/*'):
    if folder.is_dir():
        local_folders.add(folder.relative_to(archive_songs).as_posix())

print(f'Found {len(local_folders)} local folders (ProcessedSongs + Archive)')

# Get all S3 folders (active and archived)
print('\nQuerying S3 for all folders...')
s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

s3_folders = set()
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=BUCKET)

for page in pages:
    if 'Contents' not in page:
        continue
    for obj in page['Contents']:
        key = obj['Key']
        if key.startswith('output/') or key.startswith('artifacts/'):
            continue
        if '/' in key and key.endswith('.pdf'):
            folder = '/'.join(key.split('/')[:2])
            s3_folders.add(folder)

print(f'Found {len(s3_folders)} S3 folders')

# Query DynamoDB for complete mappings
print('\nQuerying DynamoDB for all records...')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

mappings = {}  # source_pdf -> {local, s3, book_id}

scan_kwargs = {}
record_count = 0

while True:
    response = table.scan(**scan_kwargs)
    for item in response['Items']:
        record_count += 1
        if record_count % 100 == 0:
            print(f'  Processed {record_count} DynamoDB records...')

        source_uri = item.get('source_pdf_uri', '')
        local_path = item.get('local_output_path', '')
        s3_path = item.get('s3_output_path', '')
        book_id = item.get('book_id', '')

        if source_uri:
            # Normalize source URI to relative path
            source_path = source_uri.replace('s3://jsmith-output/', '')

            mappings[source_path] = {
                'local': local_path,
                's3': s3_path,
                'book_id': book_id,
                'source': source_path
            }

    if 'LastEvaluatedKey' not in response:
        break
    scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']

print(f'Processed {record_count} total DynamoDB records')
print(f'Found {len(mappings)} unique source->local->s3 mappings')

# Build comprehensive mapping
rows = []

# Create reverse indexes for faster lookup
local_to_mapping = {m['local']: m for m in mappings.values() if m['local']}
s3_to_mapping = {m['s3']: m for m in mappings.values() if m['s3']}

# 1. Add all source PDFs with their mappings
print('\nMapping source PDFs...')
for source_pdf in sorted(all_source_pdfs.keys()):
    # Try to find mapping in DynamoDB by matching filename
    mapping = None

    # Extract filename from source PDF
    source_filename = source_pdf.split('/')[-1].replace('.pdf', '')
    source_filename_norm = source_filename.lower().replace(' ', '').replace('_', '').replace('-', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace("'", '')

    # Search through all mappings
    for map_data in mappings.values():
        # Try matching against local path
        if map_data['local']:
            local_filename = map_data['local'].split('/')[-1]
            local_filename_norm = local_filename.lower().replace(' ', '').replace('_', '').replace('-', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace("'", '')

            if source_filename_norm == local_filename_norm or source_filename_norm in local_filename_norm or local_filename_norm in source_filename_norm:
                mapping = map_data
                break

        # Try matching against s3 path
        if not mapping and map_data['s3']:
            s3_filename = map_data['s3'].split('/')[-1]
            s3_filename_norm = s3_filename.lower().replace(' ', '').replace('_', '').replace('-', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').replace("'", '')

            if source_filename_norm == s3_filename_norm or source_filename_norm in s3_filename_norm or s3_filename_norm in source_filename_norm:
                mapping = map_data
                break

    if mapping:
        rows.append({
            'source_pdf': source_pdf,
            'local_folder': mapping['local'] or 'UNIDENTIFIED',
            's3_folder': mapping['s3'] or 'UNIDENTIFIED',
            'book_id': mapping['book_id'],
            'status': 'MAPPED'
        })
    else:
        rows.append({
            'source_pdf': source_pdf,
            'local_folder': 'UNIDENTIFIED',
            's3_folder': 'UNIDENTIFIED',
            'book_id': 'NONE',
            'status': 'NO_MAPPING'
        })

# 2. Add local folders that weren't matched to source PDFs
print('Adding unmapped local folders...')
mapped_locals = {r['local_folder'] for r in rows if r['local_folder'] != 'UNIDENTIFIED'}

for local_folder in sorted(local_folders):
    if local_folder not in mapped_locals:
        # Try to find S3 mapping via reverse lookup in mappings
        s3_folder = 'UNIDENTIFIED'
        for map_data in mappings.values():
            if map_data['local'] == local_folder:
                s3_folder = map_data['s3'] or 'UNIDENTIFIED'
                break

        rows.append({
            'source_pdf': 'UNIDENTIFIED',
            'local_folder': local_folder,
            's3_folder': s3_folder,
            'book_id': 'NONE',
            'status': 'LOCAL_ONLY'
        })

# Save to CSV
csv_file = 'data/analysis/complete_songbook_mapping.csv'
print(f'\nSaving to {csv_file}...')

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)

    writer.writeheader()
    writer.writerows(rows)

print(f'\n{"="*80}')
print('COMPLETE SONGBOOK MAPPING CREATED')
print(f'{"="*80}')
print(f'Total rows: {len(rows)}')
print(f'Source PDFs: {len(all_source_pdfs)}')
print(f'Mapped: {sum(1 for r in rows if r["status"] == "MAPPED")}')
print(f'No mapping: {sum(1 for r in rows if r["status"] == "NO_MAPPING")}')
print(f'Local only: {sum(1 for r in rows if r["status"] == "LOCAL_ONLY")}')
print(f'\nSaved to: {csv_file}')
