#!/usr/bin/env python3
"""
Fix the remaining 13 case mismatches.
"""

from pathlib import Path

# The 13 remaining case mismatches
mismatches = [
    ("ELO - Greatest Hits", "Elo - Greatest Hits"),
    ("Led Zeppelin - Led Zeppelin II", "Led Zeppelin - Led Zeppelin Ii"),
    ("Various Artists - Legally Blonde - score", "Various Artists - Legally Blonde - Score"),
    ("Various Artists - Les Miserables - Piano-Conductor", "Various Artists - Les Miserables - Piano-conductor"),
    ("Various Artists - Little Mermaid Workshop score", "Various Artists - Little Mermaid Workshop Score"),
    ("Various Artists - Seussical - TYA", "Various Artists - Seussical - Tya"),
    ("Various Artists - The Ultimate BROADWAY fakebook", "Various Artists - The Ultimate Broadway Fakebook"),
    ("Steven Sondheim - All Sondheim Volume 2 BOOK", "Steven Sondheim - All Sondheim Volume 2 Book"),
    ("Various Artists - Book Of Great TV Hits", "Various Artists - Book Of Great Tv Hits"),
    ("Various Artists - The TV Fakebook", "Various Artists - The Tv Fakebook"),
    ("Various Artists - TV Detective - Themes For Solo Piano", "Various Artists - Tv Detective - Themes For Solo Piano"),
    ("Various Artists - TV Fakebook 2nd Ed", "Various Artists - Tv Fakebook 2nd Ed"),
    ("Various Artists - Ultimate TV Showstoppers", "Various Artists - Ultimate Tv Showstoppers"),
]

print("=" * 80)
print("FIXING REMAINING 13 CASE MISMATCHES")
print("=" * 80)
print()

# Find the folders
processed_songs_path = Path("ProcessedSongs")
rename_operations = []

for pdf_name, folder_name in mismatches:
    # Find the folder
    for artist_folder in processed_songs_path.iterdir():
        if not artist_folder.is_dir() or artist_folder.name.startswith('.'):
            continue
        
        for book_folder in artist_folder.iterdir():
            if not book_folder.is_dir() or book_folder.name.startswith('.'):
                continue
            
            if book_folder.name == folder_name:
                rename_operations.append({
                    'old_path': book_folder,
                    'old_name': folder_name,
                    'new_name': pdf_name,
                    'parent': book_folder.parent
                })
                break

print(f"Found {len(rename_operations)} folders to rename")
print()

# Display what will be renamed
print("=" * 80)
print("RENAME PLAN")
print("=" * 80)
for i, op in enumerate(rename_operations, 1):
    print(f"{i}. {op['old_name']}")
    print(f"   → {op['new_name']}")
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
        print(f"  ✓ {i}/{len(rename_operations)}: {new_name}")
    
    except Exception as e:
        error_count += 1
        errors.append({
            'old_name': op['old_name'],
            'new_name': new_name,
            'error': str(e)
        })
        print(f"  ✗ Error: {op['old_name']}")
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
else:
    print("✓ All remaining case mismatches fixed!")

print()
print("Case mismatch fix complete!")
