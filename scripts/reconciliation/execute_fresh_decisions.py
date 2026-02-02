"""
Execute fresh reconciliation decisions
"""
import json
import boto3
import shutil
from pathlib import Path
from collections import defaultdict

# Load decisions
print("Loading reconciliation_decisions_2026-02-02_fresh.json...")
decisions_file = Path(__file__).parent.parent.parent / 'reconciliation_decisions_2026-02-02_fresh.json'
with open(decisions_file, 'r', encoding='utf-8') as f:
    decisions_root = json.load(f)

decisions = decisions_root['decisions']
print(f"Loaded {len(decisions)} folders with decisions")
print(f"Total operations: {sum(len(d['fileDecisions']) for d in decisions.values())}\n")

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Local base
local_base = Path(__file__).parent.parent.parent / 'SheetMusicIndividualSheets'

# Track operations
stats = defaultdict(int)
errors = []

def copy_s3_to_local(s3_path, local_path):
    """Copy file from S3 to local"""
    try:
        s3_key = s3_path
        local_file = local_base / local_path

        # Ensure parent directory exists
        local_file.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        s3_client.download_file(bucket, s3_key, str(local_file))
        stats['s3_to_local_copies'] += 1
        return True
    except Exception as e:
        errors.append(f"S3->Local copy {s3_key} -> {local_path}: {e}")
        return False

def copy_local_to_s3(local_path, s3_path, overwrite=False):
    """Copy file from local to S3"""
    try:
        local_file = local_base / local_path
        s3_key = s3_path

        if not local_file.exists():
            errors.append(f"Local file not found: {local_path}")
            return False

        # Upload file
        s3_client.upload_file(str(local_file), bucket, s3_key)

        if overwrite:
            stats['size_mismatch_fixes'] += 1
        else:
            stats['local_to_s3_copies'] += 1
        return True
    except Exception as e:
        errors.append(f"Local->S3 copy {local_path} -> {s3_key}: {e}")
        return False

# Execute decisions
print("Executing fresh file decisions...\n")

for folder_path, folder_data in decisions.items():
    file_decisions = folder_data.get('fileDecisions', {})
    if not file_decisions:
        continue

    local_path = folder_data.get('local_path', '')
    s3_path = folder_data.get('s3_path', '')

    print(f"Processing {len(file_decisions)} files in: {folder_path}")

    for filename, file_decision in file_decisions.items():
        action = file_decision.get('action')

        if action == 'copy-s3-to-local':
            # Copy from S3 to local
            s3_file_path = f"{s3_path}/{filename}"
            local_file_path = f"{local_path}/{filename}"
            copy_s3_to_local(s3_file_path, local_file_path)

        elif action == 'copy-local-to-s3':
            # Copy from local to S3
            local_file_path = f"{local_path}/{filename}"
            s3_file_path = f"{s3_path}/{filename}"
            copy_local_to_s3(local_file_path, s3_file_path, overwrite=False)

        elif action == 'copy-local-to-s3-overwrite':
            # Copy from local to S3 (overwriting size mismatch)
            local_file_path = f"{local_path}/{filename}"
            s3_file_path = f"{s3_path}/{filename}"
            copy_local_to_s3(local_file_path, s3_file_path, overwrite=True)

# Print summary
print(f"\n{'='*60}")
print("EXECUTION SUMMARY")
print(f"{'='*60}")
print(f"S3->Local copies:    {stats['s3_to_local_copies']}")
print(f"Local->S3 copies:    {stats['local_to_s3_copies']}")
print(f"Size mismatch fixes: {stats['size_mismatch_fixes']}")
print(f"\nTotal operations:    {sum(stats.values())}")
print(f"Errors:              {len(errors)}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK Fresh reconciliation execution complete!")
