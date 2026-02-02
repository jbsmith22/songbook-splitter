"""
Create comprehensive backup of manifests, artifacts, and DynamoDB entries
for archived PERFECT folders
"""
import json
import boto3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bucket = 'jsmith-output'
table = dynamodb.Table('jsmith-processing-ledger')

# Load archive log
print("Loading archive log...")
with open('data/analysis/archived_perfect_folders.json', 'r') as f:
    archive_log = json.load(f)

archived_folders = archive_log['folders']
print(f"Found {len(archived_folders)} archived folders\n")

# Create backup directory
backup_root = Path('data/backups/archived_metadata_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
backup_root.mkdir(parents=True, exist_ok=True)

stats = defaultdict(int)
errors = []

backup_data = {
    'backup_timestamp': datetime.now().isoformat(),
    'folder_count': len(archived_folders),
    'manifests': {},
    'artifacts': {},
    'dynamodb_entries': {}
}

for i, folder in enumerate(archived_folders, 1):
    book_id = folder['book_id']

    if i % 50 == 0:
        print(f"Backing up metadata for {i}/{len(archived_folders)}...")

    try:
        # 1. Backup manifest
        try:
            response = s3_client.get_object(Bucket=bucket, Key=f'output/{book_id}/manifest.json')
            manifest = json.loads(response['Body'].read().decode('utf-8'))
            backup_data['manifests'][book_id] = manifest
            stats['manifests_backed_up'] += 1
        except Exception as e:
            errors.append(f"Failed to backup manifest for {book_id}: {e}")

        # 2. Backup artifacts (all 5 files)
        artifact_files = [
            'toc_discovery.json',
            'toc_parse.json',
            'page_mapping.json',
            'verified_songs.json',
            'output_files.json'
        ]

        backup_data['artifacts'][book_id] = {}
        for artifact_file in artifact_files:
            try:
                response = s3_client.get_object(Bucket=bucket, Key=f'artifacts/{book_id}/{artifact_file}')
                artifact_data = json.loads(response['Body'].read().decode('utf-8'))
                backup_data['artifacts'][book_id][artifact_file] = artifact_data
                stats['artifacts_backed_up'] += 1
            except Exception as e:
                # Some artifacts might not exist
                pass

        # 3. Backup DynamoDB entry
        try:
            response = table.query(
                KeyConditionExpression='book_id = :bid',
                ExpressionAttributeValues={':bid': book_id},
                ScanIndexForward=False,
                Limit=1
            )

            if response['Items']:
                # Convert Decimal to float for JSON serialization
                ddb_item = response['Items'][0]
                # DynamoDB returns Decimals which aren't JSON serializable
                backup_data['dynamodb_entries'][book_id] = json.loads(
                    json.dumps(ddb_item, default=str)
                )
                stats['dynamodb_entries_backed_up'] += 1
        except Exception as e:
            errors.append(f"Failed to backup DynamoDB for {book_id}: {e}")

    except Exception as e:
        errors.append(f"Failed to backup metadata for {book_id}: {e}")
        stats['errors'] += 1

# Save comprehensive backup
backup_file = backup_root / 'complete_metadata_backup.json'
with open(backup_file, 'w') as f:
    json.dump(backup_data, f, indent=2)

# Save summary
summary_file = backup_root / 'backup_summary.txt'
with open(summary_file, 'w') as f:
    f.write(f"Metadata Backup Summary\n")
    f.write(f"{'='*60}\n")
    f.write(f"Backup created: {datetime.now().isoformat()}\n")
    f.write(f"Folders backed up: {len(archived_folders)}\n")
    f.write(f"Manifests backed up: {stats['manifests_backed_up']}\n")
    f.write(f"Artifacts backed up: {stats['artifacts_backed_up']}\n")
    f.write(f"DynamoDB entries backed up: {stats['dynamodb_entries_backed_up']}\n")
    f.write(f"Errors: {stats['errors']}\n")
    f.write(f"\nBackup location: {backup_root}\n")

print(f"\n{'='*60}")
print("BACKUP ARCHIVED METADATA SUMMARY")
print(f"{'='*60}")
print(f"Folders backed up:            {len(archived_folders)}")
print(f"Manifests backed up:          {stats['manifests_backed_up']}")
print(f"Artifacts backed up:          {stats['artifacts_backed_up']}")
print(f"DynamoDB entries backed up:   {stats['dynamodb_entries_backed_up']}")
print(f"Errors:                       {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print(f"\n{'='*60}")
print("BACKUP LOCATION")
print(f"{'='*60}")
print(f"Complete backup: {backup_file}")
print(f"Summary: {summary_file}")

print("\nOK Metadata backup complete!")
print("All manifests, artifacts, and DynamoDB entries have been backed up.")
