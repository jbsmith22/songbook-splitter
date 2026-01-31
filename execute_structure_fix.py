"""
Execute the structure fix plan.
Moves PDFs from Books subfolders and fixes artist casing.
"""
import csv
import sys
from pathlib import Path
import shutil

def main():
    plan_file = "structure_fix_plan.csv"
    
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("=" * 70)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 70)
        print("Run with --execute flag to perform actual moves:")
        print("  py execute_structure_fix.py --execute")
        print()
    else:
        print("=" * 70)
        print("EXECUTING STRUCTURE FIX")
        print("=" * 70)
        print()
    
    # Read plan
    with open(plan_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        operations = list(reader)
    
    print(f"Loaded {len(operations)} operations")
    print()
    
    success_count = 0
    error_count = 0
    errors = []
    
    # Group operations by target artist folder to create folders first
    target_artists = set()
    for op in operations:
        target_path = Path(op['TargetPath'])
        target_artist_folder = target_path.parent
        target_artists.add(target_artist_folder)
    
    # Create target artist folders if they don't exist
    if not dry_run:
        print("Creating target artist folders...")
        for artist_folder in target_artists:
            if not artist_folder.exists():
                try:
                    artist_folder.mkdir(parents=True, exist_ok=True)
                    print(f"  Created: {artist_folder}")
                except Exception as e:
                    error_msg = f"Failed to create folder {artist_folder}: {e}"
                    errors.append(error_msg)
                    error_count += 1
        print()
    
    # Execute moves
    print("Moving PDFs...")
    for i, op in enumerate(operations, 1):
        if i % 50 == 0:
            print(f"  Processing {i}/{len(operations)}...")
        
        current_path = Path(op['CurrentPath'])
        target_path = Path(op['TargetPath'])
        
        # Check if source exists
        if not current_path.exists():
            error_msg = f"Source not found: {current_path}"
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Check if target already exists
        if target_path.exists() and current_path != target_path:
            error_msg = f"Target already exists: {target_path}"
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Perform move
        if not dry_run:
            try:
                # Ensure parent directory exists
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Move the file
                shutil.move(str(current_path), str(target_path))
                success_count += 1
            except Exception as e:
                error_msg = f"Failed to move {current_path}: {e}"
                errors.append(error_msg)
                error_count += 1
        else:
            success_count += 1
    
    print(f"  Processing {len(operations)}/{len(operations)}... Done!")
    print()
    
    # Clean up empty Books folders
    if not dry_run:
        print("Cleaning up empty Books folders...")
        sheetmusic_base = Path("SheetMusic")
        for books_folder in sheetmusic_base.rglob("Books"):
            if books_folder.is_dir():
                try:
                    # Check if empty
                    if not any(books_folder.iterdir()):
                        books_folder.rmdir()
                        print(f"  Removed empty: {books_folder}")
                except Exception as e:
                    print(f"  Could not remove {books_folder}: {e}")
        print()
    
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total operations:  {len(operations)}")
    print(f"Successful:        {success_count}")
    print(f"Errors:            {error_count}")
    print()
    
    if errors:
        print("=" * 70)
        print("ERRORS")
        print("=" * 70)
        for error in errors[:10]:
            print(f"  {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")
        print()
    
    if dry_run:
        print("=" * 70)
        print("This was a DRY RUN - no changes were made")
        print("Run with --execute flag to perform actual moves:")
        print("  py execute_structure_fix.py --execute")
        print("=" * 70)
    else:
        if error_count == 0:
            print("=" * 70)
            print("✅ ALL OPERATIONS COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print()
            print("Next step: Validate the new structure:")
            print("  py validate_current_state.py")
            print()

if __name__ == "__main__":
    main()
