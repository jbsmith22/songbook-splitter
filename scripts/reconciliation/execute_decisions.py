"""
Execute reconciliation decisions from the exported JSON file
Handles: rename-local, rename-s3, copy-to-local, copy-to-s3, delete operations
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
    'rename_local': 0,
    'rename_s3': 0,
    'copy_to_local': 0,
    'copy_to_s3': 0,
    'delete_local': 0,
    'delete_s3': 0,
    'errors': []
}

def rename_local_file(local_path, old_filename, new_filename):
    """Rename a file in the local filesystem"""
    folder_path = LOCAL_ROOT / local_path
    old_file = folder_path / old_filename
    new_file = folder_path / new_filename

    if not old_file.exists():
        raise FileNotFoundError(f"Local file not found: {old_file}")

    if new_file.exists():
        raise FileExistsError(f"Target file already exists: {new_file}")

    old_file.rename(new_file)
    print(f"  OK Renamed local: {old_filename} -> {new_filename}")
    stats['rename_local'] += 1

def rename_s3_file(s3_path, old_filename, new_filename):
    """Rename a file in S3 (copy to new key, delete old key)"""
    # Try multiple possible prefixes (with/without /Songs/ subfolder)
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    old_key = None
    for prefix in prefixes:
        test_key = f"{prefix}{old_filename}"
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=test_key)
            old_key = test_key
            break
        except:
            continue

    if not old_key:
        raise FileNotFoundError(f"S3 file not found: {s3_path}/{old_filename}")

    # Determine new key (same prefix structure)
    prefix = old_key.rsplit('/', 1)[0] + '/'
    new_key = f"{prefix}{new_filename}"

    # Check if new key already exists
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=new_key)
        raise FileExistsError(f"Target S3 file already exists: {new_key}")
    except s3.exceptions.ClientError:
        pass  # Good, doesn't exist

    # Copy to new key
    s3.copy_object(
        Bucket=S3_BUCKET,
        CopySource={'Bucket': S3_BUCKET, 'Key': old_key},
        Key=new_key
    )

    # Delete old key
    s3.delete_object(Bucket=S3_BUCKET, Key=old_key)

    print(f"  OK Renamed S3: {old_filename} -> {new_filename}")
    stats['rename_s3'] += 1

def copy_s3_to_local(s3_path, filename, local_path, allow_overwrite=False):
    """Copy a file from S3 to local"""
    # Find the file in S3
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    s3_key = None
    for prefix in prefixes:
        test_key = f"{prefix}{filename}"
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=test_key)
            s3_key = test_key
            break
        except:
            continue

    if not s3_key:
        raise FileNotFoundError(f"S3 file not found: {s3_path}/{filename}")

    # Create local folder if it doesn't exist
    folder_path = LOCAL_ROOT / local_path
    folder_path.mkdir(parents=True, exist_ok=True)

    local_file = folder_path / filename

    if local_file.exists() and not allow_overwrite:
        raise FileExistsError(f"Local file already exists: {local_file}")

    # Download from S3
    s3.download_file(S3_BUCKET, s3_key, str(local_file))

    action_word = "Overwrote" if local_file.exists() else "Copied"
    print(f"  OK {action_word} S3 to local: {filename}")
    stats['copy_to_local'] += 1

def copy_local_to_s3(local_path, filename, s3_path, allow_overwrite=False):
    """Copy a file from local to S3"""
    folder_path = LOCAL_ROOT / local_path
    local_file = folder_path / filename

    if not local_file.exists():
        raise FileNotFoundError(f"Local file not found: {local_file}")

    # Determine S3 key structure by checking what exists
    # First check if there's a Songs subfolder structure
    base_key = f"{s3_path}/"
    songs_key = f"{s3_path}/Songs/"

    # Check which structure is being used
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=songs_key,
            MaxKeys=1
        )
        if response.get('Contents'):
            # Songs subfolder exists
            s3_key = f"{songs_key}{filename}"
        else:
            # No Songs subfolder
            s3_key = f"{base_key}{filename}"
    except:
        # Default to base structure
        s3_key = f"{base_key}{filename}"

    # Check if file already exists
    file_exists = False
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=s3_key)
        file_exists = True
        if not allow_overwrite:
            raise FileExistsError(f"S3 file already exists: {s3_key}")
    except s3.exceptions.ClientError:
        pass  # Good, doesn't exist

    # Upload to S3
    s3.upload_file(str(local_file), S3_BUCKET, s3_key)

    action_word = "Overwrote" if file_exists else "Copied"
    print(f"  OK {action_word} local to S3: {filename}")
    stats['copy_to_s3'] += 1

def delete_local_file(local_path, filename):
    """Delete a file from local filesystem"""
    folder_path = LOCAL_ROOT / local_path
    local_file = folder_path / filename

    if not local_file.exists():
        raise FileNotFoundError(f"Local file not found: {local_file}")

    local_file.unlink()

    print(f"  OK Deleted local: {filename}")
    stats['delete_local'] += 1

def delete_s3_file(s3_path, filename):
    """Delete a file from S3"""
    # Try multiple possible prefixes
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    s3_key = None
    for prefix in prefixes:
        test_key = f"{prefix}{filename}"
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=test_key)
            s3_key = test_key
            break
        except:
            continue

    if not s3_key:
        raise FileNotFoundError(f"S3 file not found: {s3_path}/{filename}")

    s3.delete_object(Bucket=S3_BUCKET, Key=s3_key)

    print(f"  OK Deleted S3: {filename}")
    stats['delete_s3'] += 1

def execute_decision(folder_path, filename, decision):
    """Execute a single file decision"""
    action = decision['action']
    local_path = decision['local_path']
    s3_path = decision['s3_path']

    try:
        if action == 'no-action':
            # No action needed, skip
            return

        elif action == 'rename-local':
            new_name = decision.get('rename_target') or decision.get('normalized_name')
            if not new_name:
                raise ValueError(f"Rename action missing target name")
            rename_local_file(local_path, filename, new_name)

        elif action == 'rename-s3':
            new_name = decision.get('rename_target') or decision.get('normalized_name')
            if not new_name:
                raise ValueError(f"Rename action missing target name")
            rename_s3_file(s3_path, filename, new_name)

        elif action == 'copy-to-local':
            copy_s3_to_local(s3_path, filename, local_path, allow_overwrite=False)

        elif action == 'copy-to-s3':
            copy_local_to_s3(local_path, filename, s3_path, allow_overwrite=False)

        elif action == 'copy-local-to-s3':
            copy_local_to_s3(local_path, filename, s3_path, allow_overwrite=False)

        elif action == 'copy-local-to-s3-overwrite':
            # For size mismatches, overwrite S3 with local version
            copy_local_to_s3(local_path, filename, s3_path, allow_overwrite=True)

        elif action == 'copy-s3-to-local':
            copy_s3_to_local(s3_path, filename, local_path, allow_overwrite=False)

        elif action == 'copy-s3-to-local-overwrite':
            # For size mismatches, overwrite local with S3 version
            copy_s3_to_local(s3_path, filename, local_path, allow_overwrite=True)

        elif action in ['delete-local', 'delete-from-local']:
            delete_local_file(local_path, filename)

        elif action in ['delete-s3', 'delete-from-s3']:
            delete_s3_file(s3_path, filename)

        elif action == 'delete-both':
            delete_local_file(local_path, filename)
            delete_s3_file(s3_path, filename)

        else:
            print(f"  ⚠ Unknown action: {action}")

    except Exception as e:
        error_msg = f"Error processing {folder_path}/{filename}: {str(e)}"
        print(f"  ERROR {error_msg}")
        stats['errors'].append(error_msg)

def main():
    import sys

    print("=== Executing Reconciliation Decisions ===\n")

    # Check for --yes flag
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    # Check if a specific decisions file was provided as argument
    import glob
    if len(sys.argv) > 1 and sys.argv[1].endswith('.json'):
        decisions_file = sys.argv[1]
    else:
        # Look for the merged decisions file first
        if Path('reconciliation_decisions_2026-02-02_merged.json').exists():
            decisions_file = 'reconciliation_decisions_2026-02-02_merged.json'
        else:
            # Find the most recent decisions file
            decision_files = glob.glob('reconciliation_decisions_*.json')
            if not decision_files:
                print("ERROR: No reconciliation_decisions_*.json file found")
                return

            # Use the most recent one
            decision_files.sort(key=lambda f: Path(f).stat().st_mtime, reverse=True)
            decisions_file = decision_files[0]

    print(f"Loading decisions from: {decisions_file}")
    with open(decisions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    decisions = data['decisions']
    print(f"Found {len(decisions)} folders with decisions\n")

    # Ask for confirmation
    print("This will execute the following operations:")
    print("- Rename files (local and S3)")
    print("- Copy files between local and S3")
    print("- Delete files (local and S3)")
    print()

    if not auto_confirm:
        response = input("Are you sure you want to proceed? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    else:
        print("Auto-confirmed with --yes flag")

    print("\nExecuting decisions...\n")

    # Process each folder
    for folder_path, folder_data in decisions.items():
        file_decisions = folder_data.get('fileDecisions', {})

        if not file_decisions:
            continue

        print(f"\n{folder_path}:")

        for filename, decision in file_decisions.items():
            execute_decision(folder_path, filename, decision)

    # Print statistics
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\nLocal renames:  {stats['rename_local']}")
    print(f"S3 renames:     {stats['rename_s3']}")
    print(f"S3 -> Local:    {stats['copy_to_local']}")
    print(f"Local -> S3:    {stats['copy_to_s3']}")
    print(f"Local deletes:  {stats['delete_local']}")
    print(f"S3 deletes:     {stats['delete_s3']}")
    print(f"\nTotal operations: {sum([v for k, v in stats.items() if k != 'errors'])}")
    print(f"Errors: {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors'][:10]:
            print(f"  - {error}")
        if len(stats['errors']) > 10:
            print(f"  ... and {len(stats['errors']) - 10} more")

    # Save execution log
    log_file = f"data/analysis/execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'decisions_file': decisions_file,
            'statistics': stats
        }, f, indent=2)

    print(f"\nExecution log saved to: {log_file}")

if __name__ == '__main__':
    main()
