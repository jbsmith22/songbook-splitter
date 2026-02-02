"""
Verify which files in reconciliation_decisions_2026-02-02.json actually exist
Shows source path, existence status, action, and target path
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Local base path
local_base = Path('SheetMusicIndividualSheets')

# Load 2026-02-02 decisions
print("Loading 2026-02-02 decisions...")
decisions_file = Path(__file__).parent.parent.parent / 'reconciliation_decisions_2026-02-02.json'
with open(decisions_file, 'r', encoding='utf-8') as f:
    decisions_02 = json.load(f)

print(f"Found {len(decisions_02['decisions'])} folders with decisions\n")

# Track results
results = []
stats = defaultdict(int)

def check_s3_file_exists(s3_key):
    """Check if file exists in S3"""
    try:
        s3_client.head_object(Bucket=bucket, Key=s3_key)
        return True
    except:
        return False

def check_local_file_exists(local_path):
    """Check if file exists locally"""
    full_path = local_base / local_path
    return full_path.exists()

print("Checking file existence for all operations...\n")

# Process first 10 folders for initial analysis
folder_count = 0
max_folders_to_check = 10

for folder_path, folder_data in decisions_02['decisions'].items():
    if folder_count >= max_folders_to_check:
        break

    file_decisions = folder_data.get('fileDecisions', {})
    if not file_decisions:
        continue

    folder_count += 1

    print(f"\n{'='*80}")
    print(f"Folder {folder_count}: {folder_path}")
    print(f"{'='*80}")

    for filename, file_dec in file_decisions.items():
        action = file_dec.get('action', '')
        stats['total_operations'] += 1

        # Get paths from file decision (has correct bracket notation for S3)
        local_path = file_dec.get('local_path', folder_path)
        s3_path = file_dec.get('s3_path', folder_path)

        source_exists = False
        source_location = ''
        source_path = ''
        target_path = ''

        if action == 'rename-s3':
            # Source is in S3
            source_path = f"{s3_path}/{filename}"
            source_location = 'S3'
            source_exists = check_s3_file_exists(source_path)

            # Target is also in S3 with new name
            normalized_name = file_dec.get('normalized_name', filename)
            target_path = f"{s3_path}/{normalized_name}"

        elif action == 'rename-local':
            # Source is local
            source_path = f"{local_path}/{filename}"
            source_location = 'Local'
            source_exists = check_local_file_exists(source_path)

            # Target is also local with new name
            normalized_name = file_dec.get('normalized_name', filename)
            target_path = f"{local_path}/{normalized_name}"

        elif action in ['copy-to-local', 'copy-s3-to-local']:
            # Source is in S3
            source_path = f"{s3_path}/{filename}"
            source_location = 'S3'
            source_exists = check_s3_file_exists(source_path)

            # Target is local
            target_path = f"{local_path}/{filename}"

        elif action in ['copy-to-s3', 'copy-local-to-s3']:
            # Source is local
            source_path = f"{local_path}/{filename}"
            source_location = 'Local'
            source_exists = check_local_file_exists(source_path)

            # Target is S3
            target_path = f"{s3_path}/{filename}"

        elif action == 'delete-local':
            # Source is local
            source_path = f"{local_path}/{filename}"
            source_location = 'Local'
            source_exists = check_local_file_exists(source_path)
            target_path = '[DELETE]'

        elif action == 'delete-s3':
            # Source is in S3
            source_path = f"{s3_path}/{filename}"
            source_location = 'S3'
            source_exists = check_s3_file_exists(source_path)
            target_path = '[DELETE]'

        elif action == 'delete-both':
            # Check both locations
            s3_path_full = f"{s3_path}/{filename}"
            local_path_full = f"{local_path}/{filename}"
            s3_exists = check_s3_file_exists(s3_path_full)
            local_exists = check_local_file_exists(local_path_full)

            source_location = 'Both'
            source_path = f"S3: {s3_path_full} / Local: {local_path_full}"
            source_exists = s3_exists and local_exists
            target_path = '[DELETE BOTH]'

        # Track stats
        if source_exists:
            stats['valid_operations'] += 1
        else:
            stats['invalid_operations'] += 1

        status = "EXISTS" if source_exists else "MISSING"

        print(f"\n  {action.upper()}: {filename}")
        print(f"    Source ({source_location}): {status}")
        print(f"    Source Path: {source_path}")
        print(f"    Target Path: {target_path}")

        results.append({
            'folder': folder_path,
            'filename': filename,
            'action': action,
            'source_location': source_location,
            'source_path': source_path,
            'source_exists': source_exists,
            'target_path': target_path
        })

print(f"\n\n{'='*80}")
print("SUMMARY (First 10 Folders)")
print(f"{'='*80}")
print(f"Total operations checked: {stats['total_operations']}")
print(f"Valid (source exists):    {stats['valid_operations']}")
print(f"Invalid (source missing): {stats['invalid_operations']}")
print(f"\nTotal folders in file:    {len(decisions_02['decisions'])}")
print(f"Folders checked:          {folder_count}")

# Save detailed results to JSON
output_file = 'decision_file_verification_sample.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump({
        'stats': dict(stats),
        'results': results[:100],  # First 100 results
        'folders_checked': folder_count,
        'total_folders': len(decisions_02['decisions'])
    }, f, indent=2)

print(f"\nDetailed results saved to: {output_file}")
