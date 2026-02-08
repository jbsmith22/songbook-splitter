"""Analyze a decisions file"""
import json
import sys

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = 'reconciliation_decisions_2026-02-02 (1).json'

print(f"Analyzing: {filename}\n")

with open(filename, 'r') as f:
    data = json.load(f)

decisions = data['decisions']
print(f"Total folders in file: {len(decisions)}")

# Count folders with folderNameChoice
with_choice = {k: v for k, v in decisions.items() if v.get('folderNameChoice')}
print(f"Folders with folderNameChoice: {len(with_choice)}")

# Count folders with different paths
diff_paths = {k: v for k, v in decisions.items()
              if v.get('local_path') and v.get('s3_path')
              and v['local_path'] != v['s3_path']}
print(f"Folders with different local/S3 paths: {len(diff_paths)}")

# Show sample of folders with different paths but no choice
no_choice_diff = {k: v for k, v in diff_paths.items() if not v.get('folderNameChoice')}
print(f"Folders with different paths but NO choice: {len(no_choice_diff)}")

if no_choice_diff:
    print("\nFirst 5 examples of folders with different paths but no choice:")
    for i, (key, val) in enumerate(list(no_choice_diff.items())[:5], 1):
        print(f"{i}. {key}")
        print(f"   Local: {val.get('local_path')}")
        print(f"   S3:    {val.get('s3_path')}")
