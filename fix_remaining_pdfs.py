#!/usr/bin/env python3
"""
Fix the remaining 37 PDFs that have capitalization issues.
These are files where the destination already existed during the first run.
"""

import re
import sys
from pathlib import Path

def normalize_name(name):
    """Apply title case normalization."""
    # Known acronyms that should stay uppercase
    acronyms = ['PVG', 'SATB', 'MTI', 'PC', 'RSC', 'TYA', 'TV', 'DVD', 'CD', 'II', 'III', 'IV', 'V', 'VI']
    
    # Split into words
    words = name.split()
    result = []
    
    for word in words:
        # Check if it's an acronym
        if word.upper() in acronyms:
            result.append(word.upper())
        # Check if it's a Roman numeral pattern
        elif re.match(r'^[IVX]+$', word.upper()) and len(word) <= 4:
            result.append(word.upper())
        # Check if it's a number
        elif word.isdigit():
            result.append(word)
        # Check if it contains underscores (already normalized)
        elif '_' in word:
            result.append(word)
        # Otherwise apply title case
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

def has_lowercase_words(name):
    """Check if name has lowercase words that should be capitalized."""
    lowercase_words = [' and ', ' of ', ' the ', ' in ', ' for ', ' from ', ' with ', ' to ', ' at ']
    return any(word in name for word in lowercase_words)

def main():
    dry_run = "--execute" not in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No changes will be made")
        print("=" * 80)
        print("Run with --execute flag to perform actual renames")
        print()
    else:
        print("=" * 80)
        print("FIXING REMAINING UNNORMALIZED PDFs")
        print("=" * 80)
        print()
    
    # Find PDFs with lowercase words
    sheet_music_path = Path("SheetMusic")
    pdfs_to_fix = []
    
    for pdf_file in sheet_music_path.rglob("*.pdf"):
        if pdf_file.name.startswith('.'):
            continue
        if has_lowercase_words(pdf_file.stem):
            pdfs_to_fix.append(pdf_file)
    
    print(f"Found {len(pdfs_to_fix)} PDFs to fix")
    print()
    
    success = 0
    errors = []
    
    for i, pdf_file in enumerate(pdfs_to_fix, 1):
        old_name = pdf_file.stem
        new_name = normalize_name(old_name)
        
        if old_name == new_name:
            continue
        
        new_path = pdf_file.parent / f"{new_name}.pdf"
        
        if dry_run:
            print(f"[{i}/{len(pdfs_to_fix)}] Would rename:")
            print(f"  From: {old_name}.pdf")
            print(f"  To:   {new_name}.pdf")
            success += 1
        else:
            try:
                import os
                
                # For case-only changes on Windows, use two-step rename
                if new_path.exists() and pdf_file.resolve() == new_path.resolve():
                    # Same file, just case difference - use temp name
                    temp_path = pdf_file.parent / f"_temp_{new_name}.pdf"
                    os.rename(str(pdf_file), str(temp_path))
                    os.rename(str(temp_path), str(new_path))
                    print(f"[{i}/{len(pdfs_to_fix)}] ✓ Renamed (case-only): {old_name}.pdf → {new_name}.pdf")
                elif new_path.exists():
                    print(f"[{i}/{len(pdfs_to_fix)}] SKIP: Different file exists: {new_name}.pdf")
                    continue
                else:
                    os.rename(str(pdf_file), str(new_path))
                    print(f"[{i}/{len(pdfs_to_fix)}] ✓ Renamed: {old_name}.pdf → {new_name}.pdf")
                
                success += 1
            except Exception as e:
                print(f"[{i}/{len(pdfs_to_fix)}] ERROR: {old_name}.pdf - {str(e)}")
                errors.append((pdf_file, str(e)))
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total PDFs processed: {len(pdfs_to_fix)}")
    print(f"Successful: {success}")
    print(f"Errors: {len(errors)}")
    print()
    
    if errors:
        print("ERRORS:")
        for path, error in errors:
            print(f"  {path}: {error}")
        print()
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN COMPLETE - No changes were made")
        print("=" * 80)
        print("Run with --execute flag to perform actual renames:")
        print("  py fix_remaining_pdfs.py --execute")
    else:
        print("=" * 80)
        print("FIX COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    main()
