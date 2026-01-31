#!/usr/bin/env python3
"""
Fix case-only renames on Windows by using a two-step process:
1. Rename to a temporary name
2. Rename to the final name
"""

import re
import sys
import os
from pathlib import Path

def normalize_name(name):
    """Apply title case normalization."""
    acronyms = ['PVG', 'SATB', 'MTI', 'PC', 'RSC', 'TYA', 'TV', 'DVD', 'CD', 'II', 'III', 'IV', 'V', 'VI']
    words = name.split()
    result = []
    
    for word in words:
        if word.upper() in acronyms:
            result.append(word.upper())
        elif re.match(r'^[IVX]+$', word.upper()) and len(word) <= 4:
            result.append(word.upper())
        elif word.isdigit():
            result.append(word)
        elif '_' in word:
            result.append(word)
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

def has_lowercase_words(name):
    """Check if name has lowercase words that should be capitalized."""
    lowercase_words = [' and ', ' of ', ' the ', ' in ', ' for ', ' from ', ' with ', ' to ', ' at ', ' by ']
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
        print("FIXING CASE-ONLY RENAMES (Two-Step Process)")
        print("=" * 80)
        print()
    
    # Find PDFs with lowercase words
    sheet_music_path = Path("SheetMusic")
    pdfs_to_fix = []
    
    for pdf_file in sheet_music_path.rglob("*.pdf"):
        if pdf_file.name.startswith('.'):
            continue
        
        old_name = pdf_file.stem
        
        if not has_lowercase_words(old_name):
            continue
        
        new_name = normalize_name(old_name)
        
        if old_name == new_name:
            continue
        
        pdfs_to_fix.append((pdf_file, old_name, new_name))
    
    print(f"Found {len(pdfs_to_fix)} PDFs to fix with two-step rename")
    print()
    
    success = 0
    errors = []
    
    for i, (pdf_file, old_name, new_name) in enumerate(pdfs_to_fix, 1):
        if dry_run:
            print(f"[{i}/{len(pdfs_to_fix)}] Would rename (two-step):")
            print(f"  From: {old_name}.pdf")
            print(f"  To:   {new_name}.pdf")
            success += 1
        else:
            try:
                # Step 1: Rename to temporary name
                temp_name = f"_TEMP_{i}_"
                temp_path = pdf_file.parent / f"{temp_name}.pdf"
                os.rename(str(pdf_file), str(temp_path))
                
                # Step 2: Rename to final name
                final_path = pdf_file.parent / f"{new_name}.pdf"
                os.rename(str(temp_path), str(final_path))
                
                print(f"[{i}/{len(pdfs_to_fix)}] ✓ Renamed: {old_name}.pdf → {new_name}.pdf")
                success += 1
            except Exception as e:
                print(f"[{i}/{len(pdfs_to_fix)}] ERROR: {old_name}.pdf - {str(e)}")
                errors.append((pdf_file, str(e)))
                # Try to clean up temp file if it exists
                try:
                    if temp_path.exists():
                        os.rename(str(temp_path), str(pdf_file))
                except:
                    pass
    
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
        print("  py fix_case_only_renames.py --execute")
    else:
        print("=" * 80)
        print("FIX COMPLETE")
        print("=" * 80)

if __name__ == "__main__":
    main()
