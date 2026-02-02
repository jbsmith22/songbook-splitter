"""
Execute file-level reconciliation decisions from reconciliation_decisions_2026-02-02.json
Handles renames, copies, and deletes with conflict resolution
"""
import json
import boto3
import shutil
from pathlib import Path
from collections import defaultdict
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.backup_helper import create_backup

# Load decisions
with open('reconciliation_decisions_2026-02-02.json', 'r', encoding='utf-8') as f:
    decisions_root = json.load(f)

decisions = decisions_root['decisions']

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Track operations
stats = defaultdict(int)
errors = []

def get_available_s3_path(s3_path):
    """Find available S3 path by adding -2, -3, etc if needed"""
    base_path = s3_path
    suffix = 2

    while True:
        try:
            s3_client.head_object(Bucket=bucket, Key=s3_path)
            # File exists, try next suffix
            path_parts = base_path.rsplit('.', 1)
            if len(path_parts) == 2:
                s3_path = f"{path_parts[0]}-{suffix}.{path_parts[1]}"
            else:
                s3_path = f"{base_path}-{suffix}"
            suffix += 1
        except:
            # File doesn't exist, path is available
            return s3_path

def get_available_local_path(local_path):
    """Find available local path by adding -2, -3, etc if needed"""
    path = Path(local_path)
    if not path.exists():
        return local_path

    suffix = 2
    while True:
        new_path = path.parent / f"{path.stem}-{suffix}{path.suffix}"
        if not new_path.exists():
            return str(new_path)
        suffix += 1

def rename_s3_file(from_path, to_path, book_id):
    """Rename file in S3"""
    try:
        from_key = from_path.strip('/')
        to_key = to_path.strip('/')

        # Check if target exists
        to_key = get_available_s3_path(to_key)

        # Copy to new location
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': from_key},
            Key=to_key
        )

        # Delete old object
        s3_client.delete_object(Bucket=bucket, Key=from_key)

        stats['s3_renames'] += 1
        return to_key
    except Exception as e:
        errors.append(f"S3 rename {from_key} -> {to_key}: {e}")
        return None

def rename_local_file(from_path, to_path):
    """Rename local file"""
    try:
        from_file = Path(from_path)
        to_file = Path(to_path)

        if not from_file.exists():
            errors.append(f"Local file not found: {from_path}")
            return None

        # Check if target exists
        final_path = get_available_local_path(to_path)
        to_file = Path(final_path)

        # Ensure parent directory exists
        to_file.parent.mkdir(parents=True, exist_ok=True)

        # Rename file
        shutil.move(str(from_file), str(to_file))

        stats['local_renames'] += 1
        return str(to_file)
    except Exception as e:
        errors.append(f"Local rename {from_path} -> {to_path}: {e}")
        return None

def copy_s3_to_local(s3_path, local_path, book_id):
    """Copy file from S3 to local"""
    try:
        s3_key = s3_path.strip('/')
        local_file = Path(local_path)

        # Check if target exists
        final_path = get_available_local_path(local_path)
        local_file = Path(final_path)

        # Ensure parent directory exists
        local_file.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        s3_client.download_file(bucket, s3_key, str(local_file))

        stats['s3_to_local_copies'] += 1
        return str(local_file)
    except Exception as e:
        errors.append(f"S3->Local copy {s3_key} -> {local_path}: {e}")
        return None

def copy_local_to_s3(local_path, s3_path, book_id):
    """Copy file from local to S3"""
    try:
        local_file = Path(local_path)
        s3_key = s3_path.strip('/')

        if not local_file.exists():
            errors.append(f"Local file not found: {local_path}")
            return None

        # Check if target exists
        s3_key = get_available_s3_path(s3_key)

        # Upload file
        s3_client.upload_file(str(local_file), bucket, s3_key)

        stats['local_to_s3_copies'] += 1
        return s3_key
    except Exception as e:
        errors.append(f"Local->S3 copy {local_path} -> {s3_key}: {e}")
        return None

def delete_local_file(local_path):
    """Delete local file"""
    try:
        local_file = Path(local_path)

        if not local_file.exists():
            errors.append(f"Local file not found for deletion: {local_path}")
            return False

        local_file.unlink()
        stats['local_deletes'] += 1
        return True
    except Exception as e:
        errors.append(f"Local delete {local_path}: {e}")
        return False

def delete_s3_file(s3_path):
    """Delete S3 file"""
    try:
        s3_key = s3_path.strip('/')

        s3_client.delete_object(Bucket=bucket, Key=s3_key)

        stats['s3_deletes'] += 1
        return True
    except Exception as e:
        errors.append(f"S3 delete {s3_key}: {e}")
        return False

# Process all file decisions
print(f"Processing file decisions from reconciliation_decisions_2026-02-02.json...\n")

for folder_path, folder_decisions in decisions.items():
    file_decisions = folder_decisions.get('fileDecisions', {})

    if not file_decisions:
        continue

    book_id = folder_decisions.get('book_id', '')
    local_base = folder_decisions.get('local_path', folder_path)
    s3_base = folder_decisions.get('s3_path', folder_path)

    print(f"\nProcessing {len(file_decisions)} files in: {folder_path}")

    for filename, file_decision in file_decisions.items():
        action = file_decision.get('action')

        if action == 'rename-s3':
            # Rename file in S3
            normalized_name = file_decision.get('normalized_name')
            if normalized_name:
                from_path = f"{s3_base}/{filename}"
                to_path = f"{s3_base}/{normalized_name}"
                rename_s3_file(from_path, to_path, book_id)

        elif action == 'rename-local':
            # Rename local file
            normalized_name = file_decision.get('normalized_name')
            if normalized_name:
                from_path = f"SheetMusicIndividualSheets/{local_base}/{filename}"
                to_path = f"SheetMusicIndividualSheets/{local_base}/{normalized_name}"
                rename_local_file(from_path, to_path)

        elif action in ['copy-to-local', 'copy-s3-to-local']:
            # Copy from S3 to local
            s3_path = f"{s3_base}/{filename}"
            local_path = f"SheetMusicIndividualSheets/{local_base}/{filename}"
            copy_s3_to_local(s3_path, local_path, book_id)

        elif action in ['copy-to-s3', 'copy-local-to-s3']:
            # Copy from local to S3
            local_path = f"SheetMusicIndividualSheets/{local_base}/{filename}"
            s3_path = f"{s3_base}/{filename}"
            copy_local_to_s3(local_path, s3_path, book_id)

        elif action == 'delete-local':
            # Delete local file
            local_path = f"SheetMusicIndividualSheets/{local_base}/{filename}"
            delete_local_file(local_path)

        elif action == 'delete-s3':
            # Delete S3 file
            s3_path = f"{s3_base}/{filename}"
            delete_s3_file(s3_path)

        elif action == 'delete-both':
            # Delete both local and S3
            local_path = f"SheetMusicIndividualSheets/{local_base}/{filename}"
            s3_path = f"{s3_base}/{filename}"
            delete_local_file(local_path)
            delete_s3_file(s3_path)

# Print summary
print("\n" + "="*60)
print("EXECUTION SUMMARY")
print("="*60)
print(f"S3 renames:        {stats['s3_renames']}")
print(f"Local renames:     {stats['local_renames']}")
print(f"S3->Local copies:  {stats['s3_to_local_copies']}")
print(f"Local->S3 copies:  {stats['local_to_s3_copies']}")
print(f"Local deletes:     {stats['local_deletes']}")
print(f"S3 deletes:        {stats['s3_deletes']}")
print(f"\nTotal operations:  {sum(stats.values())}")
print(f"Errors:            {len(errors)}")

if errors:
    print("\n" + "="*60)
    print("ERRORS")
    print("="*60)
    for error in errors[:20]:  # Show first 20 errors
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK File reconciliation execution complete!")
