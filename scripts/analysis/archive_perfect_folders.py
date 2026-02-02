"""
Archive 292 PERFECT folders to keep them out of the way while working on remaining folders
"""
import json
import boto3
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bucket = 'jsmith-output'
table = dynamodb.Table('jsmith-processing-ledger')

# Paths
local_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')
archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

perfect_folders = match_data['quality_tiers']['perfect']
print(f"Found {len(perfect_folders)} PERFECT folders to archive\n")

stats = defaultdict(int)
errors = []
archived_records = []

# Create archive directory if it doesn't exist
archive_root.mkdir(exist_ok=True)

for i, folder in enumerate(perfect_folders, 1):
    book_id = folder.get('book_id', '')
    s3_path = folder.get('s3_path', '')
    local_path = folder.get('local_path', '')

    if not book_id or book_id in ['fuzzy', 'unknown', '']:
        stats['no_book_id'] += 1
        continue

    if i % 50 == 0:
        print(f"Archiving {i}/{len(perfect_folders)}...")

    try:
        # 1. Move S3 files to archive location
        s3_archive_path = f"archive/completed/{s3_path}"

        # List all files in the folder
        s3_files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{s3_path}/"):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.pdf'):
                        s3_files.append(obj['Key'])

        # Copy each file to archive location
        for s3_key in s3_files:
            filename = s3_key.split('/')[-1]
            new_key = f"{s3_archive_path}/{filename}"

            # Copy to archive
            s3_client.copy_object(
                Bucket=bucket,
                CopySource={'Bucket': bucket, 'Key': s3_key},
                Key=new_key
            )

            # Delete original
            s3_client.delete_object(Bucket=bucket, Key=s3_key)

        stats['s3_folders_archived'] += 1
        stats['s3_files_moved'] += len(s3_files)

        # 2. Move local files to archive location
        local_folder = local_root / local_path
        archive_folder = archive_root / local_path

        if local_folder.exists():
            # Create archive directory structure
            archive_folder.parent.mkdir(parents=True, exist_ok=True)

            # Move the folder
            shutil.move(str(local_folder), str(archive_folder))
            stats['local_folders_archived'] += 1

            # Count files
            local_file_count = len(list(archive_folder.glob('*.pdf')))
            stats['local_files_moved'] += local_file_count

        # 3. Update DynamoDB to reflect new location
        try:
            response = table.query(
                KeyConditionExpression='book_id = :bid',
                ExpressionAttributeValues={':bid': book_id},
                ScanIndexForward=False,
                Limit=1
            )

            if response['Items']:
                ddb_item = response['Items'][0]

                # Update with archive location
                table.put_item(Item={
                    **ddb_item,
                    's3_output_path': s3_archive_path,
                    'archived': True,
                    'archive_timestamp': datetime.now().isoformat(),
                    'original_s3_path': s3_path,
                    'original_local_path': local_path
                })
                stats['dynamodb_updated'] += 1

        except Exception as e:
            errors.append(f"DynamoDB update failed for {book_id}: {e}")

        # 4. Update manifest to reflect new location
        try:
            response = s3_client.get_object(Bucket=bucket, Key=f'output/{book_id}/manifest.json')
            manifest = json.loads(response['Body'].read().decode('utf-8'))

            # Update paths in manifest
            manifest['s3_path'] = s3_archive_path
            manifest['archived'] = True
            manifest['archive_timestamp'] = datetime.now().isoformat()
            manifest['original_s3_path'] = s3_path
            manifest['original_local_path'] = local_path

            # Update song paths
            for song in manifest.get('songs', []):
                song['output_path'] = f"{s3_archive_path}/{song['output_filename']}"

            # Save updated manifest
            s3_client.put_object(
                Bucket=bucket,
                Key=f'output/{book_id}/manifest.json',
                Body=json.dumps(manifest, indent=2),
                ContentType='application/json'
            )
            stats['manifests_updated'] += 1

        except Exception as e:
            errors.append(f"Manifest update failed for {book_id}: {e}")

        # Record the archive operation
        archived_records.append({
            'book_id': book_id,
            'original_s3_path': s3_path,
            'original_local_path': local_path,
            'archive_s3_path': s3_archive_path,
            'archive_local_path': str(archive_folder.relative_to(archive_root.parent)),
            'file_count': len(s3_files),
            'archived_at': datetime.now().isoformat()
        })

    except Exception as e:
        errors.append(f"Failed to archive {s3_path}: {e}")
        stats['errors'] += 1

# Save archive log
archive_log = {
    'archived_at': datetime.now().isoformat(),
    'folder_count': len(archived_records),
    'total_files_archived': stats['s3_files_moved'],
    'folders': archived_records
}

with open('data/analysis/archived_perfect_folders.json', 'w') as f:
    json.dump(archive_log, f, indent=2)

print(f"\n{'='*60}")
print("ARCHIVE PERFECT FOLDERS SUMMARY")
print(f"{'='*60}")
print(f"Folders to archive:        {len(perfect_folders)}")
print(f"S3 folders archived:       {stats['s3_folders_archived']}")
print(f"S3 files moved:            {stats['s3_files_moved']}")
print(f"Local folders archived:    {stats['local_folders_archived']}")
print(f"Local files moved:         {stats['local_files_moved']}")
print(f"DynamoDB updated:          {stats['dynamodb_updated']}")
print(f"Manifests updated:         {stats['manifests_updated']}")
print(f"No book_id:                {stats['no_book_id']}")
print(f"Errors:                    {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print(f"\n{'='*60}")
print("ARCHIVE LOCATIONS")
print(f"{'='*60}")
print(f"S3: {bucket}/archive/completed/")
print(f"Local: {archive_root}")
print(f"\nArchive log saved to: data/analysis/archived_perfect_folders.json")

print("\nOK PERFECT folders archived!")
print("Remaining folders in ProcessedSongs can now be worked on without clutter.")
