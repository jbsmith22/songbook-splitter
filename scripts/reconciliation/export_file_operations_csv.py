"""
Export file operations from reconciliation decision files to CSV
"""
import json
import csv
from pathlib import Path

# Output CSV file
output_file = 'reconciliation_file_operations_comparison.csv'

# Prepare CSV data
operations = []

# Process 2026-02-01 decisions
print("Processing 2026-02-01 decisions...")
try:
    with open('reconciliation_decisions_2026-02-01.json', 'r', encoding='utf-8') as f:
        decisions_01 = json.load(f)

    for folder_path, folder_data in decisions_01['decisions'].items():
        file_decisions = folder_data.get('fileDecisions', {})
        for filename, file_dec in file_decisions.items():
            action = file_dec.get('action', '')
            normalized = file_dec.get('normalized_name', '')

            operations.append({
                'batch': '2026-02-01',
                'folder': folder_path,
                'action': action,
                'original_filename': filename,
                'new_filename': normalized if normalized else filename,
                'local_path': file_dec.get('local_path', ''),
                's3_path': file_dec.get('s3_path', ''),
                'status': file_dec.get('status', ''),
                'timestamp': file_dec.get('timestamp', '')
            })

    print(f"  Found {len([o for o in operations if o['batch'] == '2026-02-01'])} file operations")
except FileNotFoundError:
    print("  File not found")

# Process 2026-02-02 decisions
print("Processing 2026-02-02 decisions...")
try:
    with open('reconciliation_decisions_2026-02-02.json', 'r', encoding='utf-8') as f:
        decisions_02 = json.load(f)

    for folder_path, folder_data in decisions_02['decisions'].items():
        file_decisions = folder_data.get('fileDecisions', {})
        for filename, file_dec in file_decisions.items():
            action = file_dec.get('action', '')
            normalized = file_dec.get('normalized_name', '')

            operations.append({
                'batch': '2026-02-02',
                'folder': folder_path,
                'action': action,
                'original_filename': filename,
                'new_filename': normalized if normalized else filename,
                'local_path': file_dec.get('local_path', ''),
                's3_path': file_dec.get('s3_path', ''),
                'status': file_dec.get('status', ''),
                'timestamp': file_dec.get('timestamp', '')
            })

    print(f"  Found {len([o for o in operations if o['batch'] == '2026-02-02'])} file operations")
except FileNotFoundError:
    print("  File not found")

# Write to CSV
print(f"\nWriting to {output_file}...")
with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['batch', 'folder', 'action', 'original_filename', 'new_filename',
                  'local_path', 's3_path', 'status', 'timestamp']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for op in operations:
        writer.writerow(op)

# Print summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

# Group by batch and action
from collections import defaultdict
batch_action_counts = defaultdict(lambda: defaultdict(int))
for op in operations:
    batch_action_counts[op['batch']][op['action']] += 1

for batch in ['2026-02-01', '2026-02-02']:
    if batch in batch_action_counts:
        print(f"\n{batch}:")
        for action, count in sorted(batch_action_counts[batch].items()):
            print(f"  {action}: {count}")

print(f"\nTotal operations: {len(operations)}")
print(f"\nCSV exported to: {output_file}")
