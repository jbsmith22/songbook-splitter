"""
Execute reconciliation decisions for completed folders with conflict resolution and manifest updates
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
    'conflicts_resolved': 0,
    'manifests_updated': 0,
    'errors': []
}

def find_available_filename(file_path):
    """Find an available filename by adding -2, -3, etc."""
    path = Path(file_path)
    base = path.stem
    ext = path.suffix
    parent = path.parent

    counter = 2
    while True:
        new_name = f"{base}-{counter}{ext}"
        new_path = parent / new_name
        if not new_path.exists():
            return str(new_path), new_name
        counter += 1

def rename_local_file(local_path, old_filename, new_filename):
    """Rename a file in local filesystem with conflict resolution"""
    folder_path = LOCAL_ROOT / local_path
    old_file = folder_path / old_filename
    new_file = folder_path / new_filename

    if not old_file.exists():
        raise FileNotFoundError(f"Local file not found: {old_file}")

    # Handle conflict
    if new_file.exists():
        new_file_path, actual_new_name = find_available_filename(new_file)
        print(f"  ⚠ Conflict: {new_filename} exists, using {actual_new_name}")
        old_file.rename(new_file_path)
        stats['conflicts_resolved'] += 1
        return actual_new_name
    else:
        old_file.rename(new_file)
        print(f"  OK Renamed local: {old_filename} -> {new_filename}")

    stats['rename_local'] += 1
    return new_filename

def rename_s3_file(s3_path, old_filename, new_filename):
    """Rename a file in S3 with conflict resolution"""
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    # Find old file
    old_key = None
    for prefix in prefixes:
        try:
            key = f"{prefix}{old_filename}"
            s3.head_object(Bucket=S3_BUCKET, Key=key)
            old_key = key
            break
        except:
            continue

    if not old_key:
        raise FileNotFoundError(f"S3 file not found: {s3_path}/{old_filename}")

    # Determine new key location
    old_prefix = old_key.rsplit('/', 1)[0]
    new_key = f"{old_prefix}/{new_filename}"

    # Handle conflict
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=new_key)
        # File exists, find alternative name
        base, ext = new_filename.rsplit('.', 1) if '.' in new_filename else (new_filename, '')
        counter = 2
        while True:
            alt_name = f"{base}-{counter}.{ext}" if ext else f"{base}-{counter}"
            alt_key = f"{old_prefix}/{alt_name}"
            try:
                s3.head_object(Bucket=S3_BUCKET, Key=alt_key)
                counter += 1
            except:
                new_key = alt_key
                new_filename = alt_name
                print(f"  ⚠ Conflict: original name exists, using {new_filename}")
                stats['conflicts_resolved'] += 1
                break
    except:
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
    return new_filename

def update_manifest_for_rename(book_id, old_filename, new_filename):
    """Update manifest.json to reflect the renamed file"""
    try:
        manifest_key = f'output/{book_id}/manifest.json'
        response = s3.get_object(Bucket=S3_BUCKET, Key=manifest_key)
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Update output section if it contains the old filename
        if 'output' in manifest and 'songs' in manifest['output']:
            updated = False
            for song in manifest['output']['songs']:
                if song.get('filename') == old_filename:
                    song['filename'] = new_filename
                    updated = True

            if updated:
                # Write back to S3
                s3.put_object(
                    Bucket=S3_BUCKET,
                    Key=manifest_key,
                    Body=json.dumps(manifest, indent=2),
                    ContentType='application/json'
                )
                print(f"    ✓ Updated manifest for {book_id}")
                stats['manifests_updated'] += 1
    except Exception as e:
        print(f"    ⚠ Could not update manifest for {book_id}: {e}")

def execute_file_decision(folder_path, filename, decision, book_id):
    """Execute a single file decision"""
    action = decision['action']

    try:
        if action.startswith('rename-local'):
            normalized_name = decision.get('normalized_name', filename)
            actual_name = rename_local_file(folder_path, filename, normalized_name)
            if book_id not in ['fuzzy', 'unknown', '']:
                update_manifest_for_rename(book_id, filename, actual_name)

        elif action.startswith('rename-s3'):
            normalized_name = decision.get('normalized_name', filename)
            actual_name = rename_s3_file(decision['s3_path'], filename, normalized_name)
            if book_id not in ['fuzzy', 'unknown', '']:
                update_manifest_for_rename(book_id, filename, actual_name)

        # Other actions (copy, delete) would go here...
        # For now, focusing on renames which are the most common

    except Exception as e:
        error_msg = f"Error processing {folder_path}/{filename}: {str(e)}"
        print(f"  ERROR {error_msg}")
        stats['errors'].append(error_msg)

def main():
    import sys

    print("=== Executing Completed Reconciliation Decisions ===\n")

    # Check for --yes flag
    auto_confirm = '--yes' in sys.argv or '-y' in sys.argv

    # Load decisions file
    decision_file = 'reconciliation_decisions_2026-02-01.json'
    print(f"Loading {decision_file}...")
    with open(decision_file, 'r', encoding='utf-8') as f:
        root = json.load(f)

    all_decisions = root['decisions']

    # Filter for completed folders with file decisions
    completed_decisions = {
        path: data for path, data in all_decisions.items()
        if data.get('completed') and data.get('fileDecisions')
    }

    print(f"Found {len(completed_decisions)} completed folders with file decisions")

    # Count operations
    total_ops = sum(len(data['fileDecisions']) for data in completed_decisions.values())
    print(f"Total file operations: {total_ops}\n")

    if not auto_confirm:
        response = input("Proceed with execution? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
    else:
        print("Auto-confirmed with --yes flag")

    print("\nExecuting decisions...\n")

    # Execute each folder's decisions
    for folder_path, folder_data in completed_decisions.items():
        file_decisions = folder_data.get('fileDecisions', {})
        book_id = folder_data.get('book_id', 'unknown')

        if not file_decisions:
            continue

        print(f"\n{folder_path}:")
        for filename, decision in file_decisions.items():
            execute_file_decision(folder_path, filename, decision, book_id)

    # Print statistics
    print("\n" + "=" * 80)
    print("EXECUTION SUMMARY")
    print("=" * 80)
    print(f"\nLocal renames:      {stats['rename_local']}")
    print(f"S3 renames:         {stats['rename_s3']}")
    print(f"Conflicts resolved: {stats['conflicts_resolved']}")
    print(f"Manifests updated:  {stats['manifests_updated']}")
    print(f"\nTotal operations:   {sum([v for k, v in stats.items() if isinstance(v, int)])}")
    print(f"Errors:             {len(stats['errors'])}")

    if stats['errors']:
        print("\nErrors encountered:")
        for error in stats['errors'][:20]:
            print(f"  - {error}")
        if len(stats['errors']) > 20:
            print(f"  ... and {len(stats['errors']) - 20} more")

    # Save execution log
    log_file = f"execution_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(f"data/analysis/{log_file}", 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'decision_file': decision_file,
            'statistics': stats,
            'completed_folders': list(completed_decisions.keys())
        }, f, indent=2)

    print(f"\n✓ Execution log saved to data/analysis/{log_file}")

if __name__ == '__main__':
    main()
