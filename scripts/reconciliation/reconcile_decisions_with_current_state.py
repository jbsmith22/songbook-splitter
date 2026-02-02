"""
Reconcile 2026-02-02 decisions with current filesystem state
Creates a new decision file with only valid operations
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Load match quality data which has file-level information
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

# Build sets of files that currently exist and folders they belong to
print("Building current file inventory from all quality tiers...")
current_s3_files = set()
current_local_files = set()
folder_file_data = {}  # Store file info per folder for reference

for tier_name, folders in match_data['quality_tiers'].items():
    for folder in folders:
        local_path = folder.get('local_path', '')
        s3_path = folder.get('s3_path', '')
        fc = folder.get('file_comparison', {})

        # Track folder data
        folder_file_data[local_path] = {
            's3_path': s3_path,
            'file_comparison': fc
        }

        # Get all local files (matching + local-only)
        local_only = fc.get('local_only_files', [])
        for f in local_only:
            filename = f['filename'] if isinstance(f, dict) else f
            current_local_files.add(f"{local_path}/{filename}")

        # Get all S3 files (matching + s3-only)
        s3_only = fc.get('s3_only_files', [])
        for f in s3_only:
            filename = f['filename'] if isinstance(f, dict) else f
            current_s3_files.add(f"{s3_path}/{filename}")

        # Add size mismatches to both sets (they exist in both but different sizes)
        size_mismatches = fc.get('size_mismatches', [])
        for mismatch in size_mismatches:
            filename = mismatch['filename'] if isinstance(mismatch, dict) else mismatch
            current_local_files.add(f"{local_path}/{filename}")
            current_s3_files.add(f"{s3_path}/{filename}")

        # Infer matching files from counts
        total_local = fc.get('total_local', 0)
        total_s3 = fc.get('total_s3', 0)
        local_only_count = len(local_only)
        s3_only_count = len(s3_only)

        # Files that match should exist in both
        matching_count = min(total_local - local_only_count, total_s3 - s3_only_count)
        # We don't have the exact list, but we know they exist based on the counts

print(f"Current inventory: {len(current_s3_files)} S3 file references, {len(current_local_files)} local file references")
print(f"Tracked {len(folder_file_data)} folders")

# Load 2026-02-02 decisions
print("\nLoading 2026-02-02 decisions...")
with open('reconciliation_decisions_2026-02-02.json', 'r', encoding='utf-8') as f:
    decisions_02 = json.load(f)

# Analyze decisions and keep only valid ones
valid_decisions = {}
stats = defaultdict(int)

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
            source_path = f"{s3_path}/{filename}"
            if source_path in current_s3_files:
                is_valid = True
                stats['valid_s3_renames'] += 1
            else:
                stats['invalid_s3_renames_missing_source'] += 1
                reason = 'source not in S3'

        elif action == 'rename-local':
            # Check if source file exists locally
            source_path = f"{local_path}/{filename}"
            if source_path in current_local_files:
                is_valid = True
                stats['valid_local_renames'] += 1
            else:
                stats['invalid_local_renames_missing_source'] += 1
                reason = 'source not local'

        elif action in ['copy-to-local', 'copy-s3-to-local']:
            # Check if source exists in S3
            source_path = f"{s3_path}/{filename}"
            if source_path in current_s3_files:
                # Check if target doesn't already exist locally
                target_path = f"{local_path}/{filename}"
                if target_path not in current_local_files:
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
            source_path = f"{local_path}/{filename}"
            if source_path in current_local_files:
                # Check if target doesn't already exist in S3
                target_path = f"{s3_path}/{filename}"
                if target_path not in current_s3_files:
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
            source_path = f"{local_path}/{filename}"
            if source_path in current_local_files:
                is_valid = True
                stats['valid_local_deletes'] += 1
            else:
                stats['skipped_local_delete_not_found'] += 1
                reason = 'not found locally'

        elif action == 'delete-s3':
            # Check if file exists in S3
            source_path = f"{s3_path}/{filename}"
            if source_path in current_s3_files:
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
        'reconciled_with': 'current filesystem state',
        'total_original_operations': sum(len(fd.get('fileDecisions', {})) for fd in decisions_02['decisions'].values()),
        'total_valid_operations': sum(len(fd.get('fileDecisions', {})) for fd in valid_decisions.values()),
        'timestamp': '2026-02-02'
    }
}

output_file = 'reconciliation_decisions_2026-02-02_reconciled.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(reconciled_file, f, indent=2)

# Print summary
print("\n" + "="*80)
print("RECONCILIATION SUMMARY")
print("="*80)
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
