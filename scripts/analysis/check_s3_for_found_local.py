"""
Check S3 for folders matching the 15 FOUND_LOCAL entries
"""
import csv
import boto3
from collections import defaultdict

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

print('Checking S3 for FOUND_LOCAL folders...\n')

# Read the complete mapping
rows = []
with open('data/analysis/provenance_complete_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Get FOUND_LOCAL entries
found_local = [r for r in rows if r['status'] == 'FOUND_LOCAL']
print(f'Found {len(found_local)} FOUND_LOCAL entries\n')

# Query S3 for all folders
print('Scanning S3 bucket...')
paginator = s3.get_paginator('list_objects_v2')

# Get all unique folder paths in S3
s3_folders = defaultdict(list)
pages = paginator.paginate(Bucket=BUCKET)

for page in pages:
    if 'Contents' not in page:
        continue
    for obj in page['Contents']:
        key = obj['Key']
        # Skip output/ and artifacts/ folders
        if key.startswith('output/') or key.startswith('artifacts/'):
            continue

        # Extract folder path (first 2 levels: artist/songbook)
        parts = key.split('/')
        if len(parts) >= 3:  # artist/songbook/file.pdf
            folder = f"{parts[0]}/{parts[1]}"
            s3_folders[folder].append(key)

print(f'Found {len(s3_folders)} unique S3 folders\n')

# Check each FOUND_LOCAL for S3 match
matches = []
for local_row in found_local:
    local_folder = local_row['local_folder']
    source_pdf = local_row['source_pdf']

    # Check if this folder exists in S3
    if local_folder in s3_folders:
        files = s3_folders[local_folder]
        matches.append({
            'source_pdf': source_pdf,
            'local_folder': local_folder,
            's3_folder': local_folder,
            'file_count': len(files),
            'sample_files': files[:3]
        })
        print(f'S3 MATCH: {local_folder}')
        print(f'  Files: {len(files)}')
        print(f'  Sample: {files[0] if files else "none"}')
        print()
    else:
        # Check in archive
        archive_path = f"archive/completed/{local_folder}"
        if archive_path.replace('archive/completed/', '') in [k.replace('archive/completed/', '') for k in s3_folders.keys() if k.startswith('archive/completed/')]:
            print(f'S3 MATCH (archived): {local_folder}')
            print()
        else:
            print(f'NO S3 MATCH: {local_folder}')
            print()

print(f'\n{"="*80}')
print(f'S3 MATCHING SUMMARY')
print(f'{"="*80}')
print(f'Total FOUND_LOCAL folders checked: {len(found_local)}')
print(f'Found in S3 (active): {len(matches)}')
print(f'Not found in S3: {len(found_local) - len(matches)}')

# Save matches
import json
with open('data/analysis/found_local_s3_matches.json', 'w', encoding='utf-8') as f:
    json.dump({
        'matches': matches,
        'total_checked': len(found_local),
        'found_in_s3': len(matches)
    }, f, indent=2)

print(f'\nResults saved to: data/analysis/found_local_s3_matches.json')
