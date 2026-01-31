"""
Execute the exact match rename plan.
Renames folders to exactly match PDF filenames.
"""
import csv
import sys
from pathlib import Path

def main():
    plan_file = "exact_match_rename_plan.csv"
    
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("=" * 70)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 70)
        print("Run with --execute flag to perform actual renames:")
        print("  py execute_exact_match_renames.py --execute")
        print()
    else:
        print("=" * 70)
        print("EXECUTING EXACT MATCH RENAMES")
        print("=" * 70)
        print()
    
    # Read rename plan
    with open(plan_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        operations = list(reader)
    
    print(f"Loaded {len(operations)} rename operations")
    print()
    
    success_count = 0
    error_count = 0
    errors = []
    
    for i, op in enumerate(operations, 1):
        old_path = Path(op['OldPath'])
        new_path = Path(op['NewPath'])
        
        if i % 50 == 0:
            print(f"  Processing {i}/{len(operations)}...")
        
        # Check if source exists
        if not old_path.exists():
            error_msg = f"Source not found: {old_path}"
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Check if target already exists
        if new_path.exists() and old_path != new_path:
            error_msg = f"Target already exists: {new_path}"
            errors.append(error_msg)
            error_count += 1
            continue
        
        # Perform rename
        if not dry_run:
            try:
                old_path.rename(new_path)
                success_count += 1
            except Exception as e:
                error_msg = f"Failed to rename {old_path}: {e}"
                errors.append(error_msg)
                error_count += 1
        else:
            success_count += 1
    
    print(f"  Processing {len(operations)}/{len(operations)}... Done!")
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
        print("Run with --execute flag to perform actual renames:")
        print("  py execute_exact_match_renames.py --execute")
        print("=" * 70)
    else:
        if error_count == 0:
            print("=" * 70)
            print("✅ ALL RENAMES COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print()
            print("Next step: Run validation to confirm exact matches:")
            print("  py validate_current_state.py")
            print()

if __name__ == "__main__":
    main()
