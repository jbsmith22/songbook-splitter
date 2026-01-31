#!/usr/bin/env python3
"""
Verify that all PDF_Paths and Folder_Paths in the CSV actually exist.
"""

import csv
from pathlib import Path

input_file = Path("book_reconciliation_fixed.csv")
output_file = Path("book_reconciliation_verified.csv")

print("=" * 80)
print("VERIFYING PATHS IN CSV")
print("=" * 80)
print()

pdf_exists_count = 0
pdf_missing_count = 0
folder_exists_count = 0
folder_missing_count = 0
rows_total = 0

missing_pdfs = []
missing_folders = []

with open(input_file, 'r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    
    # Add new columns for verification
    fieldnames = list(reader.fieldnames) + ['PDF_Exists', 'Folder_Exists']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            rows_total += 1
            
            # Check PDF path
            pdf_exists = ''
            if row['PDF_Path']:
                pdf_path = Path(row['PDF_Path'])
                if pdf_path.exists() and pdf_path.is_file():
                    pdf_exists = 'YES'
                    pdf_exists_count += 1
                else:
                    pdf_exists = 'NO'
                    pdf_missing_count += 1
                    missing_pdfs.append({
                        'status': row['Status'],
                        'artist': row['PDF_Artist'],
                        'book': row['PDF_Book'],
                        'path': row['PDF_Path']
                    })
            
            # Check Folder path
            folder_exists = ''
            if row['Folder_Path']:
                folder_path = Path(row['Folder_Path'])
                if folder_path.exists() and folder_path.is_dir():
                    folder_exists = 'YES'
                    folder_exists_count += 1
                else:
                    folder_exists = 'NO'
                    folder_missing_count += 1
                    missing_folders.append({
                        'status': row['Status'],
                        'artist': row['Folder_Artist'],
                        'book': row['Folder_Book'],
                        'path': row['Folder_Path']
                    })
            
            row['PDF_Exists'] = pdf_exists
            row['Folder_Exists'] = folder_exists
            
            writer.writerow(row)

print(f"Processed {rows_total} rows")
print()
print("PDF Paths:")
print(f"  ✓ Exist: {pdf_exists_count}")
print(f"  ✗ Missing: {pdf_missing_count}")
print()
print("Folder Paths:")
print(f"  ✓ Exist: {folder_exists_count}")
print(f"  ✗ Missing: {folder_missing_count}")
print()

if missing_pdfs:
    print("=" * 80)
    print(f"MISSING PDF FILES ({len(missing_pdfs)})")
    print("=" * 80)
    for item in missing_pdfs:
        print(f"\nStatus: {item['status']}")
        print(f"  Artist: {item['artist']}")
        print(f"  Book: {item['book']}")
        print(f"  Path: {item['path']}")

if missing_folders:
    print()
    print("=" * 80)
    print(f"MISSING FOLDERS ({len(missing_folders)})")
    print("=" * 80)
    for item in missing_folders:
        print(f"\nStatus: {item['status']}")
        print(f"  Artist: {item['artist']}")
        print(f"  Book: {item['book']}")
        print(f"  Path: {item['path']}")

print()
print("=" * 80)
print(f"✓ Output saved to: {output_file}")
print("=" * 80)
