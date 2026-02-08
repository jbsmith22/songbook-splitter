"""
Merge fresh recommendations with hints from previous decisions
"""
import json
from collections import defaultdict

print("Loading fresh recommendations...")
with open('reconciliation_decisions_2026-02-02_fresh_generated.json', 'r') as f:
    fresh_data = json.load(f)
fresh_decisions = fresh_data.get('decisions', {})

print("Loading previous decisions for hints...")
with open('reconciliation_decisions_2026-02-02_translated.json', 'r') as f:
    old_data = json.load(f)
old_decisions = old_data.get('decisions', {})

print(f"Fresh: {len(fresh_decisions)} folders")
print(f"Old: {len(old_decisions)} folders\n")

stats = defaultdict(int)
merged_decisions = {}

# Process each folder in fresh decisions
for folder_key, fresh_folder in fresh_decisions.items():
    stats['total_folders'] += 1

    # Check if we have old decisions for this folder
    old_folder = old_decisions.get(folder_key)

    if not old_folder:
        # No old decisions, use fresh as-is
        merged_decisions[folder_key] = fresh_folder
        stats['folders_no_hints'] += 1
        continue

    # Merge folder-level data
    merged_folder = {**fresh_folder}
    merged_file_decisions = {}

    fresh_files = fresh_folder.get('fileDecisions', {})
    old_files = old_folder.get('fileDecisions', {})

    for filename, fresh_decision in fresh_files.items():
        stats['total_files'] += 1
        old_decision = old_files.get(filename)

        if not old_decision:
            # No hint, use fresh decision
            merged_file_decisions[filename] = fresh_decision
            stats['files_no_hints'] += 1
            continue

        # We have a hint from old decisions
        old_action = old_decision.get('action', '')
        fresh_action = fresh_decision.get('action', '')

        # Prioritize certain manual decisions from old file
        if old_action in ['delete-from-local', 'delete-from-s3', 'delete-s3', 'delete-local']:
            # User wanted to delete this, preserve that
            merged_file_decisions[filename] = {
                **fresh_decision,
                'action': 'delete-from-local' if 'local' in old_action else 'delete-from-s3',
                'reason': f"Manual decision: {old_decision.get('reason', 'User chose to delete')}",
                'hint_source': 'previous_decision'
            }
            stats['hints_delete'] += 1

        elif old_action in ['rename-s3', 'rename-local']:
            # User wanted to rename, preserve that intent
            merged_file_decisions[filename] = {
                **fresh_decision,
                'action': old_action,
                'reason': f"Manual decision: {old_decision.get('reason', 'User chose to rename')}",
                'rename_target': old_decision.get('rename_target', ''),
                'hint_source': 'previous_decision'
            }
            stats['hints_rename'] += 1

        elif old_action == 'copy-local-to-s3' and fresh_action in ['copy-local-to-s3', 'copy-local-to-s3-overwrite']:
            # Old decision aligns with fresh, use it
            merged_file_decisions[filename] = {
                **fresh_decision,
                'action': 'copy-local-to-s3-overwrite',
                'reason': fresh_decision.get('reason', ''),
                'hint_source': 'aligned'
            }
            stats['hints_aligned'] += 1

        elif old_action == 'copy-s3-to-local' and fresh_action in ['copy-s3-to-local', 'copy-s3-to-local-overwrite']:
            # Old decision aligns with fresh, use it
            merged_file_decisions[filename] = {
                **fresh_decision,
                'action': 'copy-s3-to-local-overwrite',
                'reason': fresh_decision.get('reason', ''),
                'hint_source': 'aligned'
            }
            stats['hints_aligned'] += 1

        elif old_action == 'copy-to-local' and fresh_action in ['copy-s3-to-local', 'copy-s3-to-local-overwrite']:
            # Old decision aligns with fresh, normalize it
            merged_file_decisions[filename] = {
                **fresh_decision,
                'action': 'copy-s3-to-local-overwrite',
                'reason': fresh_decision.get('reason', ''),
                'hint_source': 'aligned_normalized'
            }
            stats['hints_aligned'] += 1

        elif old_action == 'no-action' and fresh_action == 'no-action':
            # Both agree no action needed
            merged_file_decisions[filename] = fresh_decision
            stats['hints_no_action'] += 1

        elif old_action and fresh_action and old_action != fresh_action:
            # Conflict - old says one thing, fresh says another
            # Use fresh but note the conflict for manual review
            merged_file_decisions[filename] = {
                **fresh_decision,
                'conflict_with_previous': old_action,
                'previous_reason': old_decision.get('reason', ''),
                'hint_source': 'conflict'
            }
            stats['hints_conflict'] += 1

        else:
            # Default: use fresh decision
            merged_file_decisions[filename] = fresh_decision
            stats['hints_other'] += 1

    merged_folder['fileDecisions'] = merged_file_decisions
    merged_decisions[folder_key] = merged_folder

# Save merged decisions
output_data = {
    'generated_at': '2026-02-02',
    'merged_with_hints': True,
    'folder_count': len(merged_decisions),
    'decisions': merged_decisions
}

output_file = 'reconciliation_decisions_2026-02-02_merged.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"{'='*70}")
print("MERGE SUMMARY")
print(f"{'='*70}")
print(f"Total folders:              {stats['total_folders']}")
print(f"Folders with no hints:      {stats['folders_no_hints']}")
print()
print(f"Total file decisions:       {stats['total_files']}")
print(f"Files with no hints:        {stats['files_no_hints']}")
print(f"Hints - delete preserved:   {stats['hints_delete']}")
print(f"Hints - rename preserved:   {stats['hints_rename']}")
print(f"Hints - aligned with fresh: {stats['hints_aligned']}")
print(f"Hints - no action needed:   {stats['hints_no_action']}")
print(f"Hints - conflicts found:    {stats['hints_conflict']}")
print(f"Hints - other:              {stats['hints_other']}")

print(f"\n{'='*70}")
print("OUTPUT")
print(f"{'='*70}")
print(f"Merged decisions saved to: {output_file}")
print(f"\nThis file contains:")
print(f"  - Fresh analysis of current file state")
print(f"  - Manual decisions preserved from previous work")
print(f"  - Conflicts flagged for review")

if stats['hints_conflict'] > 0:
    print(f"\nWARNING: {stats['hints_conflict']} conflicts found!")
    print("These are files where previous manual decisions differ from")
    print("current recommendations. Review these carefully.")

print("\nMerge complete!")
