#!/usr/bin/env python3
"""
Execute the normalization plan to rename PDFs and folders.
"""

import csv
import sys
from pathlib import Path

input_file = Path("normalization_plan_fixed.csv")

def main():
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)
        print("Run with --execute flag to perform actual renames")
        print()
    else:
        print("=" * 80)
        print("EXECUTING NORMALIZATION PLAN")
        print("=" * 80)
        print()
    
    # Read all entries
    entries = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        entries = list(reader)
    
    print(f"Loaded {len(entries)} rename operations")
    print()
    
    # Separate PDFs and folders
    pdfs = [e for e in entries if e['Type'] == 'PDF']
    folders = [e for e in entries if e['Type'] == 'FOLDER']
    
    # Process PDFs first (they're files, easier to rename)
    print("=" * 80)
    print(f"PROCESSING {len(pdfs)} PDF RENAMES")
    print("=" * 80)
    print()
    
    pdf_success = 0
    pdf_errors = []
    
    for i, entry in enumerate(pdfs, 1):
        old_path = Path(entry['Old_Path'])
        new_path = Path(entry['New_Path'])
        
        if dry_run:
            # Just check if source exists
            if old_path.exists():
                print(f"[{i}/{len(pdfs)}] Would rename:")
                print(f"  From: {old_path.name}")
                print(f"  To:   {new_path.name}")
                pdf_success += 1
            else:
                print(f"[{i}/{len(pdfs)}] ERROR: Source not found: {old_path}")
                pdf_errors.append((old_path, "Source not found"))
        else:
            # Actually perform the rename
            try:
                if not old_path.exists():
                    print(f"[{i}/{len(pdfs)}] ERROR: Source not found: {old_path}")
                    pdf_errors.append((old_path, "Source not found"))
                    continue
                
                if new_path.exists():
                    print(f"[{i}/{len(pdfs)}] ERROR: Destination already exists: {new_path}")
                    pdf_errors.append((old_path, "Destination already exists"))
                    continue
                
                # Use .NET method to avoid issues with special characters
                import os
                os.rename(str(old_path), str(new_path))
                print(f"[{i}/{len(pdfs)}] ✓ Renamed: {old_path.name} → {new_path.name}")
                pdf_success += 1
            except Exception as e:
                print(f"[{i}/{len(pdfs)}] ERROR: {old_path.name} - {str(e)}")
                pdf_errors.append((old_path, str(e)))
    
    print()
    print(f"PDF Results: {pdf_success} successful, {len(pdf_errors)} errors")
    print()
    
    # Process folders
    print("=" * 80)
    print(f"PROCESSING {len(folders)} FOLDER RENAMES")
    print("=" * 80)
    print()
    
    folder_success = 0
    folder_errors = []
    
    for i, entry in enumerate(folders, 1):
        old_path = Path(entry['Old_Path'])
        new_path = Path(entry['New_Path'])
        
        if dry_run:
            # Just check if source exists
            if old_path.exists():
                print(f"[{i}/{len(folders)}] Would rename:")
                print(f"  From: {old_path.name}")
                print(f"  To:   {new_path.name}")
                folder_success += 1
            else:
                print(f"[{i}/{len(folders)}] ERROR: Source not found: {old_path}")
                folder_errors.append((old_path, "Source not found"))
        else:
            # Actually perform the rename
            try:
                if not old_path.exists():
                    print(f"[{i}/{len(folders)}] ERROR: Source not found: {old_path}")
                    folder_errors.append((old_path, "Source not found"))
                    continue
                
                if new_path.exists():
                    print(f"[{i}/{len(folders)}] ERROR: Destination already exists: {new_path}")
                    folder_errors.append((old_path, "Destination already exists"))
                    continue
                
                # Use .NET method to avoid issues with special characters
                import os
                os.rename(str(old_path), str(new_path))
                print(f"[{i}/{len(folders)}] ✓ Renamed: {old_path.name} → {new_path.name}")
                folder_success += 1
            except Exception as e:
                print(f"[{i}/{len(folders)}] ERROR: {old_path.name} - {str(e)}")
                folder_errors.append((old_path, str(e)))
    
    print()
    print(f"Folder Results: {folder_success} successful, {len(folder_errors)} errors")
    print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total operations: {len(entries)}")
    print(f"  PDFs: {pdf_success}/{len(pdfs)} successful")
    print(f"  Folders: {folder_success}/{len(folders)} successful")
    print(f"  Errors: {len(pdf_errors) + len(folder_errors)}")
    print()
    
    if pdf_errors or folder_errors:
        print("ERRORS:")
        for path, error in pdf_errors + folder_errors:
            print(f"  {path}: {error}")
        print()
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN COMPLETE - No changes were made")
        print("=" * 80)
        print("Run with --execute flag to perform actual renames:")
        print("  py execute_normalization.py --execute")
    else:
        print("=" * 80)
        print("NORMALIZATION COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    main()
