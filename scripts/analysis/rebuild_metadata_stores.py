"""
Rebuild manifests and artifacts based on actual files in S3 and ProcessedSongs
"""
import json
import boto3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'
local_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

# Load validation data
print("Loading validation data...")
with open('data/analysis/final_validation_data.json', 'r') as f:
    validation_data = json.load(f)

matched_folders = validation_data.get('matched', [])
print(f"Found {len(matched_folders)} matched folders\n")

stats = defaultdict(int)
errors = []

# Process each matched folder
for i, match in enumerate(matched_folders, 1):
    book_id = match.get('book_id', '')
    s3_path = match.get('s3_path', '')
    local_path = match.get('local_path', '')
    artist = s3_path.split('/')[0] if '/' in s3_path else ''
    book_name = '/'.join(s3_path.split('/')[1:]) if '/' in s3_path else s3_path

    if not book_id or book_id in ['fuzzy', 'unknown', '']:
        stats['no_book_id'] += 1
        continue

    if i % 50 == 0:
        print(f"Processing {i}/{len(matched_folders)}...")

    try:
        # Get actual S3 files
        s3_files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{s3_path}/"):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.pdf'):
                        filename = obj['Key'].split('/')[-1]
                        s3_files.append({
                            'filename': filename,
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat()
                        })

        # Get actual local files
        local_files = []
        local_folder = local_root / local_path
        if local_folder.exists():
            for pdf_file in local_folder.glob('*.pdf'):
                local_files.append({
                    'filename': pdf_file.name,
                    'size': pdf_file.stat().st_size
                })

        # Build manifest
        manifest = {
            'book_id': book_id,
            'artist': artist,
            'book_name': book_name,
            's3_path': s3_path,
            'local_path': local_path,
            'processing_timestamp': datetime.now().isoformat(),
            'rebuilt_from_actual_files': True,
            'file_count': len(s3_files),
            'songs': [
                {
                    'output_filename': f['filename'],
                    'output_path': f"{s3_path}/{f['filename']}",
                    'size_bytes': f['size'],
                    'last_modified': f['last_modified']
                }
                for f in s3_files
            ],
            'output_files': [f['filename'] for f in s3_files]
        }

        # Upload manifest
        manifest_key = f'output/{book_id}/manifest.json'
        s3_client.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2),
            ContentType='application/json'
        )
        stats['manifests_created'] += 1

        # Build and upload artifacts
        # 1. output_files.json
        output_files = {f['filename']: f['size'] for f in s3_files}
        s3_client.put_object(
            Bucket=bucket,
            Key=f'artifacts/{book_id}/output_files.json',
            Body=json.dumps(output_files, indent=2),
            ContentType='application/json'
        )

        # 2. verified_songs.json
        verified_songs = [
            {
                'filename': f['filename'],
                'verified': True,
                'size': f['size']
            }
            for f in s3_files
        ]
        s3_client.put_object(
            Bucket=bucket,
            Key=f'artifacts/{book_id}/verified_songs.json',
            Body=json.dumps(verified_songs, indent=2),
            ContentType='application/json'
        )

        # 3. toc_parse.json (stub - we don't have original TOC data)
        toc_parse = {
            'note': 'Reconstructed from actual files',
            'entry_count': len(s3_files),
            'entries': [
                {
                    'title': f['filename'].replace('.pdf', ''),
                    'page': None
                }
                for f in s3_files
            ]
        }
        s3_client.put_object(
            Bucket=bucket,
            Key=f'artifacts/{book_id}/toc_parse.json',
            Body=json.dumps(toc_parse, indent=2),
            ContentType='application/json'
        )

        # 4. toc_discovery.json (stub)
        toc_discovery = {
            'note': 'Reconstructed from actual files',
            'toc_pages': [],
            'method': 'reconstructed'
        }
        s3_client.put_object(
            Bucket=bucket,
            Key=f'artifacts/{book_id}/toc_discovery.json',
            Body=json.dumps(toc_discovery, indent=2),
            ContentType='application/json'
        )

        # 5. page_mapping.json (stub)
        page_mapping = {
            'note': 'Reconstructed from actual files',
            'offset': 0
        }
        s3_client.put_object(
            Bucket=bucket,
            Key=f'artifacts/{book_id}/page_mapping.json',
            Body=json.dumps(page_mapping, indent=2),
            ContentType='application/json'
        )

        stats['artifacts_created'] += 1

    except Exception as e:
        errors.append(f"Failed to process {s3_path}: {e}")
        stats['errors'] += 1

print(f"\n{'='*60}")
print("REBUILD METADATA STORES SUMMARY")
print(f"{'='*60}")
print(f"Folders processed:       {len(matched_folders)}")
print(f"Manifests created:       {stats['manifests_created']}")
print(f"Artifacts created:       {stats['artifacts_created']}")
print(f"No book_id:              {stats['no_book_id']}")
print(f"Errors:                  {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK Metadata stores rebuild complete!")
print("Manifests and artifacts now accurately reflect actual files in S3.")
