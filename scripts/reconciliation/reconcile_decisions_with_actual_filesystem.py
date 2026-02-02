"""
Reconcile 2026-02-02 decisions with actual filesystem state
Queries S3 and local filesystem directly to verify file existence
Creates a new decision file with only valid operations
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict
import os

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Local base path (relative to repo root)
local_base = Path(__file__).parent.parent.parent / 'SheetMusicIndividualSheets'

print("Building actual file inventory...")
print("This may take a few minutes as we query S3 and local filesystem...")

# Build set of all S3 files
print("\n1. Scanning S3 bucket...")
current_s3_files = set()
paginator = s3_client.get_paginator('list_objects_v2')
page_iterator = paginator.paginate(Bucket=bucket)

s3_count = 0
for page in page_iterator:
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            # Skip manifest files and other non-PDF files
            if not key.startswith('output/') and key.endswith('.pdf'):
                current_s3_files.add(key)
                s3_count += 1
                if s3_count % 1000 == 0:
                    print(f"   Found {s3_count} S3 files so far...")

print(f"   Total S3 files: {len(current_s3_files)}")

# Build set of all local files
print("\n2. Scanning local filesystem...")
current_local_files = set()
local_count = 0

if local_base.exists():
    for file_path in local_base.rglob('*.pdf'):
        # Get relative path from SheetMusicIndividualSheets
        rel_path = file_path.relative_to(local_base)
        current_local_files.add(str(rel_path).replace('\\', '/'))
        local_count += 1
        if local_count % 1000 == 0:
            print(f"   Found {local_count} local files so far...")

print(f"   Total local files: {len(current_local_files)}")

# Load 2026-02-02 decisions
print("\n3. Loading 2026-02-02 decisions...")
decisions_file = Path(__file__).parent.parent.parent / 'reconciliation_decisions_2026-02-02.json'
with open(decisions_file, 'r', encoding='utf-8') as f:
    decisions_02 = json.load(f)

print(f"   Found {len(decisions_02['decisions'])} folders with decisions")

# Analyze decisions and keep only valid ones
valid_decisions = {}
stats = defaultdict(int)

print("\n4. Validating operations against actual filesystem...")

for folder_path, folder_data in decisions_02['decisions'].items():
    file_decisions = folder_data.get('fileDecisions', {})
    if not file_decisions:
        continue

    valid_file_decisions = {}

    for filename, file_dec in file_decisions.items():
        action = file_dec.get('action', '')
        local_path = file_dec.get('local_path', folder_path)
        s3_path = file_dec.get('s3_path', folder_path)

        is_valid = False
        reason = ''

        # Check validity based on action type
        if action == 'rename-s3':
            # Check if source file exists in S3
            source_s3_key = f"{s3_path}/{filename}"
            if source_s3_key in current_s3_files:
                is_valid = True
                stats['valid_s3_renames'] += 1
            else:
                stats['invalid_s3_renames_missing_source'] += 1
                reason = 'source not in S3'

        elif action == 'rename-local':
            # Check if source file exists locally
            source_local_path = f"{local_path}/{filename}"
            if source_local_path in current_local_files:
                is_valid = True
                stats['valid_local_renames'] += 1
            else:
                stats['invalid_local_renames_missing_source'] += 1
                reason = 'source not local'

        elif action in ['copy-to-local', 'copy-s3-to-local']:
            # Check if source exists in S3
            source_s3_key = f"{s3_path}/{filename}"
            if source_s3_key in current_s3_files:
                # Check if target doesn't already exist locally
                target_local_path = f"{local_path}/{filename}"
                if target_local_path not in current_local_files:
                    is_valid = True
                    stats['valid_s3_to_local_copies'] += 1
                else:
                    stats['skipped_s3_to_local_already_exists'] += 1
                    reason = 'already exists locally'
            else:
                stats['invalid_s3_to_local_missing_source'] += 1
                reason = 'source not in S3'

        elif action in ['copy-to-s3', 'copy-local-to-s3']:
            # Check if source exists locally
            source_local_path = f"{local_path}/{filename}"
            if source_local_path in current_local_files:
                # Check if target doesn't already exist in S3
                target_s3_key = f"{s3_path}/{filename}"
                if target_s3_key not in current_s3_files:
                    is_valid = True
                    stats['valid_local_to_s3_copies'] += 1
                else:
                    stats['skipped_local_to_s3_already_exists'] += 1
                    reason = 'already exists in S3'
            else:
                stats['invalid_local_to_s3_missing_source'] += 1
                reason = 'source not local'

        elif action == 'delete-local':
            # Check if file exists locally
            source_local_path = f"{local_path}/{filename}"
            if source_local_path in current_local_files:
                is_valid = True
                stats['valid_local_deletes'] += 1
            else:
                stats['skipped_local_delete_not_found'] += 1
                reason = 'not found locally'

        elif action == 'delete-s3':
            # Check if file exists in S3
            source_s3_key = f"{s3_path}/{filename}"
            if source_s3_key in current_s3_files:
                is_valid = True
                stats['valid_s3_deletes'] += 1
            else:
                stats['skipped_s3_delete_not_found'] += 1
                reason = 'not found in S3'

        elif action == 'delete-both':
            # Check both exist
            local_path_full = f"{local_path}/{filename}"
            s3_path_full = f"{s3_path}/{filename}"
            if local_path_full in current_local_files and s3_path_full in current_s3_files:
                is_valid = True
                stats['valid_both_deletes'] += 1
            else:
                stats['skipped_both_delete_partial'] += 1
                reason = 'not found in both locations'

        if is_valid:
            valid_file_decisions[filename] = file_dec
        elif reason:
            stats[f'skipped_{reason.replace(" ", "_")}'] += 1

    # Only include folder if it has valid file decisions
    if valid_file_decisions:
        valid_folder_data = folder_data.copy()
        valid_folder_data['fileDecisions'] = valid_file_decisions
        valid_decisions[folder_path] = valid_folder_data

# Create new reconciled decisions file
reconciled_file = {
    'decisions': valid_decisions,
    'metadata': {
        'source_file': 'reconciliation_decisions_2026-02-02.json',
        'reconciled_with': 'actual filesystem state (S3 + local)',
        'total_original_operations': sum(len(fd.get('fileDecisions', {})) for fd in decisions_02['decisions'].values()),
        'total_valid_operations': sum(len(fd.get('fileDecisions', {})) for fd in valid_decisions.values()),
        'timestamp': '2026-02-02',
        's3_files_scanned': len(current_s3_files),
        'local_files_scanned': len(current_local_files)
    }
}

output_file = 'reconciliation_decisions_2026-02-02_reconciled_v2.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(reconciled_file, f, indent=2)

# Print summary
print("\n" + "="*80)
print("RECONCILIATION SUMMARY")
print("="*80)
print(f"\nS3 files scanned:     {len(current_s3_files)}")
print(f"Local files scanned:  {len(current_local_files)}")
print(f"\nOriginal decisions: {reconciled_file['metadata']['total_original_operations']} operations")
print(f"Valid operations:   {reconciled_file['metadata']['total_valid_operations']} operations")
print(f"Folders with valid operations: {len(valid_decisions)}")

print("\n--- VALID OPERATIONS ---")
if stats.get('valid_s3_renames'): print(f"  S3 renames:          {stats['valid_s3_renames']}")
if stats.get('valid_local_renames'): print(f"  Local renames:       {stats['valid_local_renames']}")
if stats.get('valid_s3_to_local_copies'): print(f"  S3->Local copies:    {stats['valid_s3_to_local_copies']}")
if stats.get('valid_local_to_s3_copies'): print(f"  Local->S3 copies:    {stats['valid_local_to_s3_copies']}")
if stats.get('valid_local_deletes'): print(f"  Local deletes:       {stats['valid_local_deletes']}")
if stats.get('valid_s3_deletes'): print(f"  S3 deletes:          {stats['valid_s3_deletes']}")
if stats.get('valid_both_deletes'): print(f"  Both deletes:        {stats['valid_both_deletes']}")

print("\n--- SKIPPED OPERATIONS ---")
for key, value in sorted(stats.items()):
    if key.startswith('invalid_') or key.startswith('skipped_'):
        print(f"  {key}: {value}")

print(f"\nReconciled decisions saved to: {output_file}")
print("\nYou can now execute these reconciled decisions.")
