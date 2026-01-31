#!/usr/bin/env python3
"""
Fix case mismatches between PDF names and folder names.
Uses two-step rename process for Windows case-insensitive filesystem.
"""

from pathlib import Path
import csv
import os

print("=" * 80)
print("FIXING CASE MISMATCHES")
print("=" * 80)
print()

# Load case mismatches
case_mismatches = []
with open('case_mismatches.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        case_mismatches.append(row)

print(f"Found {len(case_mismatches)} case mismatches to fix")
print()

# We need to rename folders to match PDF names
# Strategy: Rename folder to match the PDF name (which is the correct normalized name)

rename_operations = []

for item in case_mismatches:
    pdf_name = item['PDF_Name']
    folder_name = item['Folder_Name']
    folder_path = Path(item['Folder_Path'])
    
    # The target name should match the PDF name
    target_name = pdf_name
    
    # Check if folder exists
    if folder_path.exists():
        rename_operations.append({
            'old_path': folder_path,
            'old_name': folder_name,
            'new_name': target_name,
            'parent': folder_path.parent
        })

print(f"Prepared {len(rename_operations)} rename operations")
print()

# Display what will be renamed
print("=" * 80)
print("RENAME PLAN")
print("=" * 80)
for i, op in enumerate(rename_operations[:10], 1):
    print(f"{i}. {op['old_name']}")
    print(f"   → {op['new_name']}")
    print()

if len(rename_operations) > 10:
    print(f"... and {len(rename_operations) - 10} more")
    print()

# Ask for confirmation
response = input("Proceed with renames? (yes/no): ").strip().lower()
if response != 'yes':
    print("Aborted.")
    exit(0)

print()
print("=" * 80)
print("EXECUTING RENAMES")
print("=" * 80)

success_count = 0
error_count = 0
errors = []

for i, op in enumerate(rename_operations, 1):
    old_path = op['old_path']
    new_name = op['new_name']
    parent = op['parent']
    
    # Two-step rename for case-only changes on Windows
    temp_name = f"_TEMP_RENAME_{i}_"
    temp_path = parent / temp_name
    final_path = parent / new_name
    
    try:
        # Step 1: Rename to temp name
        old_path.rename(temp_path)
        
        # Step 2: Rename to final name
        temp_path.rename(final_path)
        
        success_count += 1
        if i % 10 == 0:
            print(f"  Progress: {i}/{len(rename_operations)}")
    
    except Exception as e:
        error_count += 1
        errors.append({
            'path': str(old_path),
            'error': str(e)
        })
        print(f"  ✗ Error renaming: {old_path.name}")
        print(f"    {e}")

print()
print("=" * 80)
print("RESULTS")
print("=" * 80)
print(f"✓ Successfully renamed: {success_count}")
print(f"✗ Errors: {error_count}")
print()

if errors:
    print("Errors encountered:")
    for err in errors:
        print(f"  {err['path']}")
        print(f"    {err['error']}")
    print()

# Save error log if any
if errors:
    error_file = Path("case_mismatch_errors.csv")
    with open(error_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Path', 'Error'])
        for err in errors:
            writer.writerow([err['path'], err['error']])
    print(f"✓ Error log saved to: {error_file}")

print()
print("Case mismatch fix complete!")
