"""
Translate file paths in reconciliation_decisions_2026-02-02.json
to account for folder renames from reconciliation_decisions_2026-02-01.json
"""
import json
from pathlib import Path

# Load 2026-02-01 decisions to get folder rename mappings
print("Loading 2026-02-01 folder renames...")
with open('reconciliation_decisions_2026-02-01.json', 'r', encoding='utf-8') as f:
    decisions_2026_01 = json.load(f)

# Build folder path mapping (old -> new)
folder_path_map = {}
for folder_path, decisions in decisions_2026_01['decisions'].items():
    folder_decision = decisions.get('folderDecision', {})
    if folder_decision:
        old_local = decisions.get('local_path', folder_path)
        old_s3 = decisions.get('s3_path', folder_path)
        new_local = folder_decision.get('new_local_path', old_local)
        new_s3 = folder_decision.get('new_s3_path', old_s3)

        # Store mappings
        if old_local != new_local:
            folder_path_map[old_local] = new_local
        if old_s3 != new_s3:
            folder_path_map[old_s3] = new_s3

print(f"Found {len(folder_path_map)} folder path changes from 2026-02-01")

# Load 2026-02-02 decisions
print("\nLoading 2026-02-02 file decisions...")
with open('reconciliation_decisions_2026-02-02.json', 'r', encoding='utf-8') as f:
    decisions_2026_02 = json.load(f)

# Translate paths in 2026-02-02 decisions
updated_decisions = {}
translations = 0
no_translation_needed = 0

for old_folder_path, decisions in decisions_2026_02['decisions'].items():
    # Check if this folder was renamed
    new_folder_path = folder_path_map.get(old_folder_path, old_folder_path)

    if new_folder_path != old_folder_path:
        translations += 1
        print(f"  Translating: {old_folder_path} -> {new_folder_path}")
    else:
        no_translation_needed += 1

    # Update folder paths in the decision
    updated_decision = decisions.copy()

    # Update local_path if it exists and needs translation
    if 'local_path' in updated_decision:
        old_local = updated_decision['local_path']
        updated_decision['local_path'] = folder_path_map.get(old_local, old_local)

    # Update s3_path if it exists and needs translation
    if 's3_path' in updated_decision:
        old_s3 = updated_decision['s3_path']
        updated_decision['s3_path'] = folder_path_map.get(old_s3, old_s3)

    # Update file decision paths
    if 'fileDecisions' in updated_decision:
        for filename, file_dec in updated_decision['fileDecisions'].items():
            # Update local_path in file decision
            if 'local_path' in file_dec:
                old_local = file_dec['local_path']
                file_dec['local_path'] = folder_path_map.get(old_local, old_local)

            # Update s3_path in file decision
            if 's3_path' in file_dec:
                old_s3 = file_dec['s3_path']
                file_dec['s3_path'] = folder_path_map.get(old_s3, old_s3)

    # Store with new folder path as key
    updated_decisions[new_folder_path] = updated_decision

# Create updated decisions file
updated_file = {
    'decisions': updated_decisions,
    'metadata': decisions_2026_02.get('metadata', {}),
    'translation_info': {
        'source_file': 'reconciliation_decisions_2026-02-02.json',
        'folder_renames_from': 'reconciliation_decisions_2026-02-01.json',
        'folders_translated': translations,
        'folders_unchanged': no_translation_needed
    }
}

# Save to new file
output_file = 'reconciliation_decisions_2026-02-02_translated.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(updated_file, f, indent=2)

print(f"\n{'='*60}")
print("TRANSLATION SUMMARY")
print('='*60)
print(f"Folders translated:     {translations}")
print(f"Folders unchanged:      {no_translation_needed}")
print(f"Total folders:          {len(updated_decisions)}")
print(f"\nUpdated decisions saved to: {output_file}")
print("\nYou can now execute the translated decisions file.")
