#!/usr/bin/env python3
"""
Fix duplicate normalized names by adding numeric suffixes.
"""

import csv
from pathlib import Path
from collections import defaultdict

input_file = Path("normalization_plan.csv")
output_file = Path("normalization_plan_fixed.csv")

print("=" * 80)
print("FIXING DUPLICATE NORMALIZED NAMES")
print("=" * 80)
print()

# Read all entries
entries = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    entries = list(reader)

print(f"Loaded {len(entries)} rename operations")

# Group by Type, Artist, and New_Name to find duplicates
name_groups = defaultdict(list)
for i, entry in enumerate(entries):
    key = (entry['Type'], entry['Artist'], entry['New_Name'])
    name_groups[key].append(i)

# Find duplicates
duplicates_found = 0
for key, indices in name_groups.items():
    if len(indices) > 1:
        duplicates_found += 1
        type_name, artist, new_name = key
        print(f"\nDuplicate: {type_name} - {artist} - {new_name}")
        print(f"  {len(indices)} items will normalize to same name:")
        
        # Add numeric suffix to duplicates
        for seq_num, idx in enumerate(indices, start=1):
            entry = entries[idx]
            print(f"    {seq_num}. {entry['Old_Name']}")
            
            # Add suffix to all but the first one
            if seq_num > 1:
                # Add suffix before file extension for PDFs
                if entry['Type'] == 'PDF':
                    entry['New_Name'] = f"{new_name} - {seq_num}"
                    old_path = Path(entry['New_Path'])
                    entry['New_Path'] = str(old_path.parent / f"{entry['New_Name']}.pdf")
                else:
                    entry['New_Name'] = f"{new_name} - {seq_num}"
                    old_path = Path(entry['New_Path'])
                    entry['New_Path'] = str(old_path.parent / entry['New_Name'])
                
                print(f"       → Renamed to: {entry['New_Name']}")

print()
print(f"✓ Fixed {duplicates_found} duplicate name groups")

# Write fixed output
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['Type', 'Needs_Rename', 'Artist', 'Old_Name', 'New_Name', 'Old_Path', 'New_Path', 'Status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(entries)

print(f"✓ Output saved to: {output_file}")
print()

# Verify no duplicates remain
final_check = defaultdict(list)
for entry in entries:
    key = (entry['Type'], entry['Artist'], entry['New_Name'])
    final_check[key].append(entry['Old_Name'])

remaining_dupes = sum(1 for v in final_check.values() if len(v) > 1)

if remaining_dupes == 0:
    print("✓ NO DUPLICATE NAMES REMAINING")
else:
    print(f"⚠ WARNING: {remaining_dupes} duplicate names still exist")
    for key, names in final_check.items():
        if len(names) > 1:
            print(f"  {key}: {names}")
