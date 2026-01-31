#!/usr/bin/env python3
"""
Validate all paths and columns in the complete CSV against actual folder structure.
"""

import csv
from pathlib import Path

input_file = Path("book_reconciliation_complete.csv")
output_file = Path("book_reconciliation_validated.csv")

print("=" * 80)
print("VALIDATING COMPLETE CSV")
print("=" * 80)
print()

errors = []
warnings = []
rows_processed = 0

with open(input_file, 'r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    fieldnames = list(reader.fieldnames)
    
    # Add validation columns if not present
    if 'PDF_Exists' not in fieldnames:
        fieldnames.append('PDF_Exists')
    if 'Folder_Exists' not in fieldnames:
        fieldnames.append('Folder_Exists')
    if 'Validation_Notes' not in fieldnames:
        fieldnames.append('Validation_Notes')
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is 1)
            rows_processed += 1
            notes = []
            
            # Validate PDF path
            if row['PDF_Path']:
                pdf_path = Path(row['PDF_Path'])
                if pdf_path.exists() and pdf_path.is_file():
                    row['PDF_Exists'] = 'YES'
                    
                    # Extract artist and book from path
                    # Path structure: SheetMusic\{Artist}\Books\{BookName}.pdf
                    # or: SheetMusic\{Artist}\{BookName}.pdf
                    parts = pdf_path.parts
                    actual_book = pdf_path.stem  # Filename without extension
                    
                    # Find artist - skip "Books" folder if present
                    actual_artist = None
                    for i in range(len(parts) - 1, -1, -1):
                        if parts[i] == 'SheetMusic':
                            if i + 1 < len(parts):
                                actual_artist = parts[i + 1]
                            break
                    
                    if actual_artist:
                        # Check if CSV columns match
                        if row['PDF_Artist'] != actual_artist:
                            notes.append(f"PDF_Artist mismatch: CSV='{row['PDF_Artist']}' vs Actual='{actual_artist}'")
                            errors.append(f"Row {row_num}: PDF_Artist mismatch")
                        
                        if row['PDF_Book'] != actual_book:
                            notes.append(f"PDF_Book mismatch: CSV='{row['PDF_Book']}' vs Actual='{actual_book}'")
                            errors.append(f"Row {row_num}: PDF_Book mismatch")
                else:
                    row['PDF_Exists'] = 'NO'
                    notes.append(f"PDF file not found: {row['PDF_Path']}")
                    errors.append(f"Row {row_num}: PDF file missing")
            else:
                row['PDF_Exists'] = ''
            
            # Validate Folder path
            if row['Folder_Path']:
                folder_path = Path(row['Folder_Path'])
                if folder_path.exists() and folder_path.is_dir():
                    row['Folder_Exists'] = 'YES'
                    
                    # Extract artist and book from path
                    parts = folder_path.parts
                    if len(parts) >= 2:
                        actual_artist = parts[-2]  # Parent folder
                        actual_book = parts[-1]    # Folder name
                        
                        # Check if CSV columns match
                        if row['Folder_Artist'] != actual_artist:
                            notes.append(f"Folder_Artist mismatch: CSV='{row['Folder_Artist']}' vs Actual='{actual_artist}'")
                            errors.append(f"Row {row_num}: Folder_Artist mismatch")
                        
                        if row['Folder_Book'] != actual_book:
                            notes.append(f"Folder_Book mismatch: CSV='{row['Folder_Book']}' vs Actual='{actual_book}'")
                            errors.append(f"Row {row_num}: Folder_Book mismatch")
                    
                    # Check if folder has PDFs
                    pdf_files = list(folder_path.glob("*.pdf"))
                    if not pdf_files:
                        notes.append(f"Folder has no PDF files")
                        warnings.append(f"Row {row_num}: Folder is empty")
                else:
                    row['Folder_Exists'] = 'NO'
                    notes.append(f"Folder not found: {row['Folder_Path']}")
                    errors.append(f"Row {row_num}: Folder missing")
            else:
                row['Folder_Exists'] = ''
            
            # Validate Status
            if row['Status'] == 'MATCHED':
                if not row['PDF_Path'] or not row['Folder_Path']:
                    notes.append("Status is MATCHED but missing PDF or Folder path")
                    errors.append(f"Row {row_num}: MATCHED status incomplete")
            elif row['Status'] == 'UNMATCHED_PDF':
                if row['Folder_Path']:
                    notes.append("Status is UNMATCHED_PDF but has Folder path")
                    warnings.append(f"Row {row_num}: UNMATCHED_PDF has folder")
            elif row['Status'] == 'UNMATCHED_FOLDER':
                if row['PDF_Path']:
                    notes.append("Status is UNMATCHED_FOLDER but has PDF path")
                    warnings.append(f"Row {row_num}: UNMATCHED_FOLDER has PDF")
            
            row['Validation_Notes'] = '; '.join(notes) if notes else ''
            writer.writerow(row)

print(f"Processed {rows_processed} rows")
print()
print("=" * 80)
print("VALIDATION RESULTS")
print("=" * 80)
print(f"Errors: {len(errors)}")
print(f"Warnings: {len(warnings)}")
print()

if errors:
    print("ERRORS:")
    for error in errors[:20]:  # Show first 20
        print(f"  - {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more")
    print()

if warnings:
    print("WARNINGS:")
    for warning in warnings[:20]:  # Show first 20
        print(f"  - {warning}")
    if len(warnings) > 20:
        print(f"  ... and {len(warnings) - 20} more")
    print()

print(f"✓ Output saved to: {output_file}")
print()

if len(errors) == 0 and len(warnings) == 0:
    print("✓ ALL VALIDATIONS PASSED!")
else:
    print(f"⚠ Found {len(errors)} errors and {len(warnings)} warnings")
    print("  Check the Validation_Notes column in the output CSV for details")
