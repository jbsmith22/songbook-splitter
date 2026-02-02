"""
Update validation data with new S3 paths after folder renames
"""
import json
import shutil
from datetime import datetime

# Create backup of validation data
validation_file = r'data\analysis\final_validation_data.json'
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f'{validation_file}.backup_{timestamp}'
shutil.copy2(validation_file, backup_file)
print(f"Created backup: {backup_file}\n")

# Load decisions to see what was renamed
with open('reconciliation_decisions_2026-02-01.json', 'r', encoding='utf-8') as f:
    decisions_root = json.load(f)

decisions = decisions_root['decisions']

# Build mapping of old S3 paths to new S3 paths
s3_path_updates = {}
for folder_path, folder_data in decisions.items():
    if folder_data.get('folderAction'):
        action = folder_data['folderAction']
        if action.get('action') == 'rename-s3-folder':
            old_path = action['from']
            new_path = action['to']
            s3_path_updates[old_path] = new_path
            print(f"Will update: {old_path} -> {new_path}")

print(f"\nFound {len(s3_path_updates)} S3 path updates")

# Load validation data
with open(r'data\analysis\final_validation_data.json', 'r', encoding='utf-8') as f:
    validation_data = json.load(f)

# Update s3_path for matched folders
updated_count = 0
for match in validation_data['matched']:
    old_s3_path = match['s3_path']
    if old_s3_path in s3_path_updates:
        new_s3_path = s3_path_updates[old_s3_path]
        match['s3_path'] = new_s3_path
        updated_count += 1
        print(f"Updated: {old_s3_path} -> {new_s3_path}")

print(f"\n{updated_count} validation entries updated")

# Save updated validation data
with open(r'data\analysis\final_validation_data.json', 'w', encoding='utf-8') as f:
    json.dump(validation_data, f, indent=2)

print(f"\nValidation data saved to data\\analysis\\final_validation_data.json")
