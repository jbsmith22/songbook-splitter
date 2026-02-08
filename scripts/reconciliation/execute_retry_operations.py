"""
Execute retry operations from the retry file
"""
import json
import boto3
from pathlib import Path
from datetime import datetime

# Load retry operations
retry_file = 'reconciliation_retry_2026-02-02.json'
print(f"Loading retry operations from {retry_file}...")
with open(retry_file, 'r', encoding='utf-8') as f:
    retry_data = json.load(f)

operations = retry_data['operations']
print(f"Found {len(operations)} retry operations")

# Initialize AWS
s3 = boto3.client('s3')
BUCKET = 'jsmith-output'
LOCAL_ROOT = Path('d:/Work/songbook-splitter/ProcessedSongs')

# Statistics
stats = {
    'rename_s3': 0,
    'rename_local': 0,
    'errors': []
}

print(f"\n{'='*80}")
print("EXECUTING RETRY OPERATIONS")
print(f"{'='*80}\n")

for i, op in enumerate(operations, 1):
    op_type = op['type']
    source = op['source']
    target = op['target']
    reason = op.get('reason', '')

    if op_type == 'rename-s3':
        try:
            # Copy to new name
            copy_source = {'Bucket': BUCKET, 'Key': source}
            s3.copy_object(CopySource=copy_source, Bucket=BUCKET, Key=target)

            # Delete old file
            s3.delete_object(Bucket=BUCKET, Key=source)

            stats['rename_s3'] += 1
            source_name = source.split('/')[-1]
            target_name = target.split('/')[-1]
            print(f"[{i}/{len(operations)}] S3 RENAME: {source_name} -> {target_name}")

        except Exception as e:
            error_msg = f"Error renaming S3 {source}: {e}"
            stats['errors'].append(error_msg)
            print(f"[{i}/{len(operations)}] ERROR: {error_msg}")

    elif op_type == 'rename-local':
        try:
            source_path = Path(source)
            target_path = Path(target)

            # Rename file
            source_path.rename(target_path)

            stats['rename_local'] += 1
            print(f"[{i}/{len(operations)}] LOCAL RENAME: {source_path.name} -> {target_path.name}")

        except Exception as e:
            error_msg = f"Error renaming local {source}: {e}"
            stats['errors'].append(error_msg)
            print(f"[{i}/{len(operations)}] ERROR: {error_msg}")

print(f"\n{'='*80}")
print("EXECUTION SUMMARY")
print(f"{'='*80}")
print(f"S3 renames:    {stats['rename_s3']}")
print(f"Local renames: {stats['rename_local']}")
print(f"Errors:        {len(stats['errors'])}")

if stats['errors']:
    print(f"\nErrors encountered:")
    for error in stats['errors'][:10]:
        print(f"  - {error}")
    if len(stats['errors']) > 10:
        print(f"  ... and {len(stats['errors']) - 10} more")

# Save execution log
log_file = f"data/analysis/retry_execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
log_data = {
    'timestamp': datetime.now().isoformat(),
    'retry_file': retry_file,
    'statistics': stats
}

with open(log_file, 'w', encoding='utf-8') as f:
    json.dump(log_data, f, indent=2)

print(f"\nExecution log saved to: {log_file}")
