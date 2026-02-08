"""
Analyze the new decisions file
"""
import json
from collections import defaultdict

decisions_file = 'reconciliation_decisions_2026-02-03.json'
print(f"Loading {decisions_file}...")

with open(decisions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

decisions = data['decisions']
print(f"\nTotal folders: {len(decisions)}")

# Analyze decisions
stats = {
    'marked_exact': 0,
    'with_file_decisions': 0,
    'with_folder_choices': 0,
    'file_decision_types': defaultdict(int),
    'folder_choices': defaultdict(int),
    'total_file_decisions': 0
}

for folder_path, folder_data in decisions.items():
    if folder_data.get('markedExact'):
        stats['marked_exact'] += 1

    file_decisions = folder_data.get('fileDecisions', {})
    if file_decisions:
        stats['with_file_decisions'] += 1
        stats['total_file_decisions'] += len(file_decisions)
        for filename, decision in file_decisions.items():
            action = decision.get('action', 'unknown')
            stats['file_decision_types'][action] += 1

    folder_choice = folder_data.get('folderNameChoice')
    if folder_choice:
        stats['with_folder_choices'] += 1
        stats['folder_choices'][folder_choice] += 1

print(f"\n{'='*70}")
print("DECISIONS SUMMARY")
print(f"{'='*70}")
print(f"Folders marked as exact:           {stats['marked_exact']}")
print(f"Folders with file decisions:       {stats['with_file_decisions']}")
print(f"Folders with folder name choices:  {stats['with_folder_choices']}")
print(f"Total file decisions:              {stats['total_file_decisions']}")

if stats['folder_choices']:
    print(f"\nFolder name choices:")
    for choice, count in sorted(stats['folder_choices'].items()):
        print(f"  {choice}: {count}")

if stats['file_decision_types']:
    print(f"\nFile decision types:")
    for action, count in sorted(stats['file_decision_types'].items(), key=lambda x: -x[1]):
        print(f"  {action}: {count}")

# Ready to execute?
ready_to_execute = stats['with_file_decisions'] > 0 or stats['with_folder_choices'] > 0

print(f"\n{'='*70}")
if ready_to_execute:
    print("STATUS: Ready to execute decisions")
    print(f"{'='*70}")
    print(f"\nThis file contains {stats['total_file_decisions']} file decisions")
    print(f"and {stats['with_folder_choices']} folder naming decisions.")
    print(f"\nTo execute:")
    print(f"  File decisions: py scripts/reconciliation/execute_decisions.py {decisions_file} --yes")
    if stats['with_folder_choices']:
        print(f"  Folder renames: py scripts/reconciliation/execute_folder_renames.py {decisions_file} --yes")
else:
    print("STATUS: No decisions to execute")
    print(f"{'='*70}")
    print(f"\nThis file has {stats['marked_exact']} folders marked as exact,")
    print(f"but no file or folder name decisions to execute.")
