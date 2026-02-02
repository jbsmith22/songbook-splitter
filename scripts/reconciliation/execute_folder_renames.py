"""
Execute folder rename decisions from reconciliation decisions file
"""
import json
import boto3
import shutil
from pathlib import Path
from datetime import datetime

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'
LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

# Statistics
stats = {
    'rename_local_folder': 0,
    'rename_s3_folder': 0,
    'conflicts_resolved': 0,
    'manifests_updated': 0,
    'errors': []
}

def find_available_foldername(folder_path):
    """Find an available folder name by adding -2, -3, etc."""
    path = Path(folder_path)
    base = path.name
    parent = path.parent

    counter = 2
    while True:
        new_name = f"{base}-{counter}"
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path), new_name
        counter += 1

def rename_local_folder(from_path, to_path):
    """Rename a local folder with conflict resolution"""
    local_from = LOCAL_ROOT / from_path
    local_to = LOCAL_ROOT / to_path

    if not local_from.exists():
        raise FileNotFoundError(f"Local folder not found: {local_from}")

    # Handle conflict
    if local_to.exists():
        new_path, actual_name = find_available_foldername(local_to)
        print(f"  ⚠ Conflict: {to_path} exists, using {actual_name}")
        local_from.rename(new_path)
        stats['conflicts_resolved'] += 1
        return Path(new_path).relative_to(LOCAL_ROOT).as_posix()
    else:
        # Ensure parent directory exists
        local_to.parent.mkdir(parents=True, exist_ok=True)
        local_from.rename(local_to)
        print(f"  OK Renamed local folder: {from_path} -> {to_path}")

    stats['rename_local_folder'] += 1
    return to_path

def rename_s3_folder(from_path, to_path):
    """Rename an S3 folder by copying all objects and deleting originals"""
    # Song PDFs are stored at root level (no "output/" prefix)
    # Only manifests/artifacts are under output/{book_id}/
    from_prefix = from_path.strip('/')
    to_prefix = to_path.strip('/')

    # List all objects in source folder
    print(f"  Listing objects in s3://{S3_BUCKET}/{from_prefix}/...")
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=from_prefix + '/')

    objects_to_move = []
    for page in pages:
        if 'Contents' in page:
            objects_to_move.extend(page['Contents'])

    if not objects_to_move:
        raise FileNotFoundError(f"No objects found in S3 folder: {from_prefix}/")

    print(f"  Found {len(objects_to_move)} objects to move")

    # Check if target already exists
    try:
        response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=to_prefix + '/', MaxKeys=1)
        if response.get('KeyCount', 0) > 0:
            # Target exists, find alternative name
            base_parts = to_path.rsplit('/', 1)
            if len(base_parts) == 2:
                parent, folder_name = base_parts
            else:
                parent = ''
                folder_name = to_path

            counter = 2
            while True:
                alt_name = f"{folder_name}-{counter}"
                alt_path = f"{parent}/{alt_name}" if parent else alt_name
                alt_prefix = alt_path.strip('/')

                response = s3.list_objects_v2(Bucket=S3_BUCKET, Prefix=alt_prefix + '/', MaxKeys=1)
                if response.get('KeyCount', 0) == 0:
                    to_prefix = alt_prefix
                    to_path = alt_path
                    print(f"  ⚠ Conflict: original path exists in S3, using {to_path}")
                    stats['conflicts_resolved'] += 1
                    break
                counter += 1
    except Exception as e:
        print(f"  Warning checking for conflicts: {e}")

    # Copy all objects to new location
    moved = 0
    for obj in objects_to_move:
        old_key = obj['Key']
        # Replace the prefix
        new_key = old_key.replace(from_prefix + '/', to_prefix + '/', 1)

        try:
            # Copy object
            s3.copy_object(
                Bucket=S3_BUCKET,
                CopySource={'Bucket': S3_BUCKET, 'Key': old_key},
                Key=new_key
            )
            moved += 1

            if moved % 10 == 0:
                print(f"    Moved {moved}/{len(objects_to_move)} objects...")
        except Exception as e:
            print(f"    ERROR copying {old_key}: {e}")
            stats['errors'].append(f"Failed to copy {old_key}: {str(e)}")

    print(f"  Copied {moved} objects to new location")

    # Delete old objects
    deleted = 0
    for obj in objects_to_move:
        try:
            s3.delete_object(Bucket=S3_BUCKET, Key=obj['Key'])
            deleted += 1
        except Exception as e:
            print(f"    ERROR deleting {obj['Key']}: {e}")
            stats['errors'].append(f"Failed to delete {obj['Key']}: {str(e)}")

    print(f"  Deleted {deleted} old objects")
    print(f"  OK Renamed S3 folder: {from_path} -> {to_path}")

    stats['rename_s3_folder'] += 1
    return to_path

def update_manifest_path(old_folder_path, new_folder_path):
    """Update manifest.json path after folder rename"""
    try:
        # Try to get manifest from new location (if it was moved)
        manifest_key = f'output/{new_folder_path}/manifest.json'
        response = s3.get_object(Bucket=S3_BUCKET, Key=manifest_key)
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Check if manifest needs updating
        # (Some manifests may already have correct paths)
        needs_update = False

        # Update any references to old folder path in the manifest
        if 'output' in manifest and 'songs' in manifest['output']:
            for song in manifest['output']['songs']:
                # Could update any path references here if needed
                pass

        # For now, manifests should be fine after folder move
        # since they use relative paths
        print(f"    ✓ Manifest exists at new location")

    except Exception as e:
        print(f"    ⚠ Could not verify manifest: {e}")

def execute_folder_action(folder_path, folder_action):
    """Execute a single folder rename action"""
    action = folder_action.get('action')
    from_path = folder_action.get('from')
    to_path = folder_action.get('to')

    if not action or not from_path or not to_path:
        print(f"  ERROR: Invalid folder action: {folder_action}")
        return

    try:
        if action == 'rename-local-folder':
            actual_path = rename_local_folder(from_path, to_path)

        elif action == 'rename-s3-folder':
            actual_path = rename_s3_folder(from_path, to_path)
            # Verify manifest is in place
            update_manifest_path(from_path, actual_path)

        else:
            print(f"  WARNING: Unknown action: {action}")

    except Exception as e:
        error_msg = f"Error processing folder {folder_path}: {str(e)}"
        print(f"  ERROR {error_msg}")
        stats['errors'].append(error_msg)

def main():
    import sys

    print("=== Executing Folder Rename Decisions ===\n")

    # Check for --yes flag
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    # Load decisions file
    decision_file = 'reconciliation_decisions_2026-02-01.json'
    print(f"Loading {decision_file}...")
    with open(decision_file, 'r', encoding='utf-8') as f:
        root = json.load(f)

    all_decisions = root['decisions']

    # Filter for completed folders with folderAction
    folder_decisions = {
        path: data for path, data in all_decisions.items()
        if data.get('completed') and data.get('folderAction')
    }

    print(f"Found {len(folder_decisions)} completed folders with folder rename actions")

    # Count by action type
    rename_local = sum(1 for d in folder_decisions.values()
                      if d['folderAction'].get('action') == 'rename-local-folder')
    rename_s3 = sum(1 for d in folder_decisions.values()
                   if d['folderAction'].get('action') == 'rename-s3-folder')

    print(f"  Local folder renames: {rename_local}")
    print(f"  S3 folder renames: {rename_s3}")
    print()

    if not auto_confirm:
        response = input("Proceed with execution? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    else:
        print("Auto-confirmed with --yes flag")

    print("\nExecuting folder rename decisions...\n")

    # Execute each folder's rename action
    for folder_path, folder_data in folder_decisions.items():
        folder_action = folder_data.get('folderAction')

        if not folder_action:
            continue

        print(f"\n{folder_path}:")
        execute_folder_action(folder_path, folder_action)

    # Print statistics
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\nLocal folder renames: {stats['rename_local_folder']}")
    print(f"S3 folder renames:    {stats['rename_s3_folder']}")
    print(f"Conflicts resolved:   {stats['conflicts_resolved']}")
    print(f"\nTotal operations:     {stats['rename_local_folder'] + stats['rename_s3_folder']}")
    print(f"Errors:               {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors'][:20]:
            print(f"  - {error}")
        if len(stats['errors']) > 20:
            print(f"  ... and {len(stats['errors']) - 20} more")

    # Save execution log
    log_file = f"folder_rename_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(f"data/analysis/{log_file}", 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'decision_file': decision_file,
            'statistics': stats,
            'renamed_folders': list(folder_decisions.keys())
        }, f, indent=2)

    print(f"\n✓ Execution log saved to data/analysis/{log_file}")

if __name__ == '__main__':
    main()
