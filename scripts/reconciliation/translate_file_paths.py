"""
Translate file paths in reconciliation_decisions_2026-02-02.json
to account for file renames from reconciliation_decisions_2026-02-01.json
"""
import json
from collections import defaultdict

# Load 2026-02-01 decisions to get file rename mappings
print("Loading 2026-02-01 file operations...")
with open('reconciliation_decisions_2026-02-01.json', 'r', encoding='utf-8') as f:
    decisions_2026_01 = json.load(f)

# Build file rename mapping: (folder_path, old_filename) -> new_filename
file_rename_map = {}
folder_rename_map = {}

for folder_path, decisions in decisions_2026_01['decisions'].items():
    # Check for folder renames
    folder_decision = decisions.get('folderDecision', {})
    if folder_decision:
        new_s3 = folder_decision.get('new_s3_path')
        new_local = folder_decision.get('new_local_path')
        if new_s3 and new_s3 != decisions.get('s3_path', folder_path):
            folder_rename_map[decisions.get('s3_path', folder_path)] = new_s3
        if new_local and new_local != decisions.get('local_path', folder_path):
            folder_rename_map[decisions.get('local_path', folder_path)] = new_local

    # Check for file renames
    file_decisions = decisions.get('fileDecisions', {})
    for filename, file_dec in file_decisions.items():
        action = file_dec.get('action', '')
        if action in ['rename-s3', 'rename-local']:
            normalized = file_dec.get('normalized_name')
            if normalized and normalized != filename:
                key = (folder_path, filename)
                file_rename_map[key] = normalized
                print(f"  File rename: {folder_path}/{filename} -> {normalized}")

print(f"\nFound {len(file_rename_map)} file renames from 2026-02-01")
print(f"Found {len(folder_rename_map)} folder renames from 2026-02-01")

# Load 2026-02-02 decisions
print("\nLoading 2026-02-02 file decisions...")
with open('reconciliation_decisions_2026-02-02.json', 'r', encoding='utf-8') as f:
    decisions_2026_02 = json.load(f)

# Translate paths and remove duplicate operations
updated_decisions = {}
translations = 0
duplicates_removed = 0
operations_kept = 0

for folder_path, decisions in decisions_2026_02['decisions'].items():
    # Translate folder path if it was renamed
    new_folder_path = folder_rename_map.get(folder_path, folder_path)

    updated_decision = decisions.copy()
    updated_decision['fileDecisions'] = {}

    # Process file decisions
    file_decisions = decisions.get('fileDecisions', {})
    for old_filename, file_dec in file_decisions.items():
        action = file_dec.get('action', '')

        # Check if this file was already renamed in 2026-02-01
        key = (folder_path, old_filename)
        if key in file_rename_map:
            # File was renamed - update the filename
            new_filename = file_rename_map[key]

            # Check if this decision is trying to rename to the same name (duplicate)
            if action in ['rename-s3', 'rename-local']:
                proposed_name = file_dec.get('normalized_name')
                if proposed_name == new_filename:
                    # Duplicate rename - skip it
                    duplicates_removed += 1
                    continue

            # Update the file decision to use the new filename
            updated_file_dec = file_dec.copy()
            updated_decision['fileDecisions'][new_filename] = updated_file_dec
            translations += 1
        else:
            # File wasn't renamed - keep as is
            updated_decision['fileDecisions'][old_filename] = file_dec.copy()
            operations_kept += 1

    # Only include folder if it has file decisions
    if updated_decision['fileDecisions']:
        # Update folder paths
        if 'local_path' in updated_decision:
            updated_decision['local_path'] = folder_rename_map.get(updated_decision['local_path'], updated_decision['local_path'])
        if 's3_path' in updated_decision:
            updated_decision['s3_path'] = folder_rename_map.get(updated_decision['s3_path'], updated_decision['s3_path'])

        updated_decisions[new_folder_path] = updated_decision

# Create updated decisions file
updated_file = {
    'decisions': updated_decisions,
    'metadata': decisions_2026_02.get('metadata', {}),
    'translation_info': {
        'source_file': 'reconciliation_decisions_2026-02-02.json',
        'renames_from': 'reconciliation_decisions_2026-02-01.json',
        'file_translations': translations,
        'duplicate_operations_removed': duplicates_removed,
        'operations_kept': operations_kept
    }
}

# Save to new file
output_file = 'reconciliation_decisions_2026-02-02_translated.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updated_file, f, indent=2)

print(f"\n{'='*60}")
print("TRANSLATION SUMMARY")
print('='*60)
print(f"File translations:           {translations}")
print(f"Duplicate operations removed: {duplicates_removed}")
print(f"Operations kept as-is:       {operations_kept}")
print(f"Total folders with decisions: {len(updated_decisions)}")
print(f"\nUpdated decisions saved to: {output_file}")
print("\nYou can now execute the translated decisions file.")
