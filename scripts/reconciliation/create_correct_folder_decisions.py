"""
Create correct folder naming decisions:
- Use the 10 explicit choices from browser localStorage
- Default to 'local' for all other folders with different paths
- This will rename S3 to match local (keeping underscore format)
"""
import json
from pathlib import Path

print("Loading decisions files...")

# Load the original decisions file (has all folder data)
original_file = 'reconciliation_decisions_2026-02-02 (1).json'
if not Path(original_file).exists():
    original_file = 'reconciliation_decisions_2026-02-02-newer.json'

print(f"Using: {original_file}")
with open(original_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

decisions = data['decisions']
print(f"Total folders: {len(decisions)}")

# Find folders with different local/S3 paths
different_paths = []
explicit_choices = []

for folder_key, folder_data in decisions.items():
    local_path = folder_data.get('local_path')
    s3_path = folder_data.get('s3_path')

    if not local_path or not s3_path:
        continue

    if local_path != s3_path:
        existing_choice = folder_data.get('folderNameChoice')

        if existing_choice:
            # Keep existing choice
            explicit_choices.append(folder_key)
            print(f"  Explicit choice '{existing_choice}': {folder_key}")
        else:
            # Default to 'local' (rename S3 to match local)
            folder_data['folderNameChoice'] = 'local'
            folder_data['chosenFolderPath'] = local_path
            different_paths.append(folder_key)

print(f"\nExplicit choices preserved: {len(explicit_choices)}")
print(f"Defaulted to 'local': {len(different_paths)}")

# Save updated file
output_file = 'reconciliation_decisions_2026-02-02_correct.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print(f"\nSaved to: {output_file}")
print(f"\nThis will:")
print(f"  - Rename {len(different_paths)} S3 folders to match local (keep underscores)")
print(f"  - Honor {len(explicit_choices)} explicit choices")
print(f"\nTo execute:")
print(f"  py scripts/reconciliation/execute_folder_renames.py {output_file} --yes")
