"""
Fix failed rename operations by using -# suffixes to avoid conflicts
"""
import json
import boto3
from pathlib import Path

# Load the execution log with errors
print("Loading execution log...")
with open('data/analysis/execution_log_20260202_204438.json', 'r', encoding='utf-8') as f:
    log = json.load(f)

# Load the original decisions file to get the operation types
print("Loading original decisions...")
with open('reconciliation_decisions_2026-02-03.json', 'r', encoding='utf-8') as f:
    original_decisions = json.load(f)

# Initialize S3 client
s3 = boto3.client('s3')
BUCKET = 'jsmith-output'
LOCAL_ROOT = Path('d:/Work/songbook-splitter/ProcessedSongs')

errors = log['statistics']['errors']
print(f"\nProcessing {len(errors)} errors...")

retry_operations = []
skipped_missing = []

for error_msg in errors:
    # Parse the error message
    if "Local file not found:" in error_msg:
        # Skip - file doesn't exist, nothing we can do
        file_path = error_msg.split("Local file not found: ")[1]
        skipped_missing.append(file_path)
        continue

    if "Target S3 file already exists:" in error_msg:
        # Extract source and target from error message
        # Format: "Error processing {folder}/{source}: Target S3 file already exists: {folder}/{target}"
        parts = error_msg.split(": Target S3 file already exists: ")
        source_path = parts[0].replace("Error processing ", "")
        target_path = parts[1]

        # Check if both files exist on S3
        try:
            # Check source exists
            s3.head_object(Bucket=BUCKET, Key=source_path)
            # Check target exists
            s3.head_object(Bucket=BUCKET, Key=target_path)

            # Both exist - need to rename source with suffix
            # Find next available suffix
            target_dir = target_path.rsplit('/', 1)[0]
            target_filename = target_path.rsplit('/', 1)[1]
            base_name = target_filename.rsplit('.', 1)[0]
            extension = target_filename.rsplit('.', 1)[1]

            suffix = 2
            while True:
                new_name = f"{base_name}-{suffix}.{extension}"
                new_path = f"{target_dir}/{new_name}"
                try:
                    s3.head_object(Bucket=BUCKET, Key=new_path)
                    suffix += 1
                except:
                    # This name is available
                    break

            retry_operations.append({
                'type': 'rename-s3',
                'source': source_path,
                'target': new_path,
                'reason': f'Renamed with -{suffix} suffix to avoid conflict with {target_path}'
            })
            print(f"  S3: {source_path} -> {new_name}")

        except Exception as e:
            print(f"  ERROR checking S3 files: {e}")
            continue

    elif "Target file already exists:" in error_msg:
        # Local file conflict
        parts = error_msg.split(": Target file already exists: ")
        source_path_rel = parts[0].replace("Error processing ", "")
        target_path_abs = parts[1]

        source_path_abs = LOCAL_ROOT / source_path_rel
        target_path_abs = Path(target_path_abs)

        # Check if both files exist locally
        if source_path_abs.exists() and target_path_abs.exists():
            # Both exist - need to rename source with suffix
            base_name = target_path_abs.stem
            extension = target_path_abs.suffix
            target_dir = target_path_abs.parent

            suffix = 2
            while True:
                new_path = target_dir / f"{base_name}-{suffix}{extension}"
                if not new_path.exists():
                    break
                suffix += 1

            retry_operations.append({
                'type': 'rename-local',
                'source': str(source_path_abs),
                'target': str(new_path),
                'reason': f'Renamed with -{suffix} suffix to avoid conflict with {target_path_abs.name}'
            })
            print(f"  LOCAL: {source_path_abs.name} -> {new_path.name}")

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Skipped (file not found): {len(skipped_missing)}")
print(f"Retry operations created: {len(retry_operations)}")

# Save retry operations to a new file
output = {
    'timestamp': log['timestamp'],
    'original_file': 'reconciliation_decisions_2026-02-03.json',
    'retry_count': len(retry_operations),
    'operations': retry_operations
}

output_file = 'reconciliation_retry_2026-02-02.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"\nRetry operations saved to: {output_file}")

# Print breakdown by type
rename_s3 = sum(1 for op in retry_operations if op['type'] == 'rename-s3')
rename_local = sum(1 for op in retry_operations if op['type'] == 'rename-local')
print(f"\nBreakdown:")
print(f"  rename-s3: {rename_s3}")
print(f"  rename-local: {rename_local}")
