"""
Undo the folder renames from the execution log
"""
import json
from pathlib import Path

LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

# Load the execution log
log_file = 'data/analysis/folder_rename_log_20260201_225739.json'
print(f"Loading: {log_file}")
with open(log_file, 'r', encoding='utf-8') as f:
    log_data = json.load(f)

# Load the auto-standardized decisions to get the from/to paths
decisions_file = 'reconciliation_decisions_2026-02-02_auto_standardized.json'
print(f"Loading: {decisions_file}")
with open(decisions_file, 'r', encoding='utf-8') as f:
    decisions_data = json.load(f)

decisions = decisions_data['decisions']

# Get list of successfully renamed folders from log
renamed_folders = log_data['renamed_folders']
print(f"\nFound {len(renamed_folders)} folders in execution log")
print(f"Successfully renamed: {log_data['statistics']['rename_local_folder']}")

# Build undo list
undo_count = 0
errors = []

for folder_path in renamed_folders:
    folder_data = decisions.get(folder_path)

    if not folder_data:
        continue

    local_path = folder_data.get('local_path')
    s3_path = folder_data.get('s3_path')
    choice = folder_data.get('folderNameChoice')

    # Only undo if choice was 's3' (which means local was renamed to match S3)
    if choice == 's3' and local_path and s3_path and local_path != s3_path:
        # The rename was: local_path -> s3_path
        # To undo: s3_path -> local_path

        current_path = LOCAL_ROOT / s3_path
        original_path = LOCAL_ROOT / local_path

        if current_path.exists() and not original_path.exists():
            try:
                # Ensure parent directory exists
                original_path.parent.mkdir(parents=True, exist_ok=True)
                current_path.rename(original_path)
                print(f"  OK Undone: {s3_path} -> {local_path}")
                undo_count += 1
            except Exception as e:
                error_msg = f"Failed to undo {s3_path}: {str(e)}"
                print(f"  ERROR {error_msg}")
                errors.append(error_msg)
        elif not current_path.exists():
            print(f"  SKIP (not found): {s3_path}")
        elif original_path.exists():
            print(f"  SKIP (target exists): {original_path}")

print(f"\nUndone {undo_count} folder renames")
print(f"Errors: {len(errors)}")

if errors:
    print("\nErrors:")
    for error in errors[:20]:
        print(f"  - {error}")
