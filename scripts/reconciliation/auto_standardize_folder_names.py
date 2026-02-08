"""
Auto-generate folder name choices for all folders with different local/S3 paths
Defaults to S3 naming for consistency (brackets instead of underscores)
"""
import json
from pathlib import Path

# Load the decisions file
decisions_file = 'reconciliation_decisions_2026-02-02 (1).json'

print(f"Loading: {decisions_file}")
with open(decisions_file, 'r') as f:
    data = json.load(f)

decisions = data['decisions']
print(f"Total folders: {len(decisions)}")

# Find folders with different paths but no choice
updated_count = 0
for folder_key, folder_data in decisions.items():
    local_path = folder_data.get('local_path')
    s3_path = folder_data.get('s3_path')

    # Skip if paths match or if choice already made
    if not local_path or not s3_path or local_path == s3_path:
        continue

    if folder_data.get('folderNameChoice'):
        continue  # Already has a choice

    # Auto-choose S3 naming (more consistent with brackets)
    folder_data['folderNameChoice'] = 's3'
    folder_data['chosenFolderPath'] = s3_path
    updated_count += 1

print(f"\nAdded folderNameChoice to {updated_count} folders")
print(f"All choices default to 's3' (standardize on S3 naming)")

# Save updated file
output_file = 'reconciliation_decisions_2026-02-02_auto_standardized.json'
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"\nSaved to: {output_file}")
print(f"\nNext step:")
print(f"  py scripts/reconciliation/execute_folder_renames.py {output_file} --yes")
