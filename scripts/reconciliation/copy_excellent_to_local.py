"""
Copy all S3 files to local for EXCELLENT folders to make them PERFECT
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'
local_base = Path('SheetMusicIndividualSheets')

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

excellent_folders = match_data['quality_tiers']['excellent']
print(f"Found {len(excellent_folders)} EXCELLENT folders\n")

stats = defaultdict(int)
errors = []

for i, folder in enumerate(excellent_folders, 1):
    local_path = folder.get('local_path', '')
    s3_path = folder.get('s3_path', '')

    print(f"\n[{i}/{len(excellent_folders)}] Processing: {local_path}")

    # List all S3 files for this folder
    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        prefix = f"{s3_path}/"

        file_count = 0
        for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                s3_key = obj['Key']

                # Skip if not a PDF
                if not s3_key.endswith('.pdf'):
                    continue

                # Extract filename (handle /Songs/ subfolder if present)
                if '/Songs/' in s3_key:
                    filename = s3_key.split('/Songs/')[-1]
                else:
                    filename = s3_key.split('/')[-1]

                # Local destination
                local_file = local_base / local_path / filename
                local_file.parent.mkdir(parents=True, exist_ok=True)

                # Download
                try:
                    s3_client.download_file(bucket, s3_key, str(local_file))
                    file_count += 1
                    stats['files_copied'] += 1

                    if file_count % 10 == 0:
                        print(f"  Copied {file_count} files...")

                except Exception as e:
                    errors.append(f"Failed to copy {s3_key}: {e}")
                    stats['errors'] += 1

        print(f"  Total copied: {file_count} files")

    except Exception as e:
        errors.append(f"Failed to list S3 for {s3_path}: {e}")
        stats['folder_errors'] += 1

print(f"\n{'='*60}")
print("COPY SUMMARY")
print(f"{'='*60}")
print(f"Folders processed:  {len(excellent_folders)}")
print(f"Files copied:       {stats['files_copied']}")
print(f"Errors:             {stats['errors']}")
print(f"Folder errors:      {stats['folder_errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK S3 to local copy complete!")
