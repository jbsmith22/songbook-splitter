#!/usr/bin/env python3
"""
Fix case mismatches between PDF names and folder names.
Finds current folders and renames them to match PDF names exactly.
"""

from pathlib import Path
import csv

print("=" * 80)
print("FIXING CASE MISMATCHES")
print("=" * 80)
print()

# Load case mismatches to understand what needs to be fixed
case_mismatches = []
with open('case_mismatches.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        case_mismatches.append(row)

print(f"Found {len(case_mismatches)} case mismatches to fix")
print()

# Build a mapping of what folders need to be renamed
# Key: current folder name (lowercase for comparison)
# Value: target folder name (from PDF)
rename_map = {}

for item in case_mismatches:
    pdf_name = item['PDF_Name']
    folder_name = item['Folder_Name']
    
    # The folder currently has 'folder_name', needs to become 'pdf_name'
    rename_map[folder_name.lower()] = {
        'current_name': folder_name,
        'target_name': pdf_name
    }

print(f"Built rename map with {len(rename_map)} entries")
print()

# Now scan ProcessedSongs to find actual folders
processed_songs_path = Path("ProcessedSongs")
rename_operations = []

for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir():
        continue
    if artist_folder.name.startswith('.'):
        continue
    
    # Check each book folder
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir():
            continue
        if book_folder.name.startswith('.'):
            continue
        
        # Check if this folder needs to be renamed
        folder_name_lower = book_folder.name.lower()
        if folder_name_lower in rename_map:
            target_name = rename_map[folder_name_lower]['target_name']
            
            # Only rename if names actually differ
            if book_folder.name != target_name:
                rename_operations.append({
                    'old_path': book_folder,
                    'old_name': book_folder.name,
                    'new_name': target_name,
                    'parent': book_folder.parent
                })

print(f"Found {len(rename_operations)} folders to rename")
print()

if not rename_operations:
    print("No folders need renaming. All case mismatches may already be fixed!")
    exit(0)

# Display what will be renamed
print("=" * 80)
print("RENAME PLAN (first 10)")
print("=" * 80)
for i, op in enumerate(rename_operations[:10], 1):
    print(f"{i}. {op['old_name']}")
    print(f"   → {op['new_name']}")
    print()

if len(rename_operations) > 10:
    print(f"... and {len(rename_operations) - 10} more")
    print()

# Ask for confirmation
response = input(f"Proceed with {len(rename_operations)} renames? (yes/no): ").strip().lower()
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
        if i % 10 == 0 or i == len(rename_operations):
            print(f"  Progress: {i}/{len(rename_operations)}")
    
    except Exception as e:
        error_count += 1
        errors.append({
            'path': str(old_path),
            'old_name': op['old_name'],
            'new_name': new_name,
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
        print(f"  {err['old_name']} → {err['new_name']}")
        print(f"    {err['error']}")
    print()
    
    # Save error log
    error_file = Path("case_mismatch_errors.csv")
    with open(error_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Path', 'Old_Name', 'New_Name', 'Error'])
        for err in errors:
            writer.writerow([err['path'], err['old_name'], err['new_name'], err['error']])
    print(f"✓ Error log saved to: {error_file}")
else:
    print("✓ All case mismatches fixed successfully!")

print()
print("Case mismatch fix complete!")
