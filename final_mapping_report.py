#!/usr/bin/env python3
"""
Final mapping report: identify truly unprocessed PDFs and case mismatches.
"""

from pathlib import Path
import csv

print("=" * 80)
print("FINAL MAPPING REPORT")
print("=" * 80)
print()

# Load normalization plan
normalization_plan = {}
with open('normalization_plan_fixed.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        old_path = row['Old_Path']
        normalization_plan[old_path] = {
            'type': row['Type'],
            'new_name': row['New_Name'],
            'status': row['Status']
        }

# Load reconciliation
reconciliation = []
with open('book_reconciliation_validated.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        reconciliation.append(row)

# Analyze
matched_pdfs = []
unmatched_pdfs = []
fake_books_count = 0
case_mismatches = []

for row in reconciliation:
    status = row['Status']
    pdf_path = row['PDF_Path']
    pdf_book = row['PDF_Book']
    folder_path = row['Folder_Path']
    
    if not pdf_path:
        continue
    
    # Count Fake Books
    if '_Fake Books' in pdf_path:
        fake_books_count += 1
        continue
    
    # Get normalized names
    if pdf_path in normalization_plan:
        normalized_pdf_name = normalization_plan[pdf_path]['new_name']
    else:
        normalized_pdf_name = pdf_book
    
    normalized_folder_name = None
    if folder_path and folder_path in normalization_plan:
        normalized_folder_name = normalization_plan[folder_path]['new_name']
    elif folder_path:
        normalized_folder_name = Path(folder_path).name
    
    # Categorize
    if status == 'MATCHED':
        matched_pdfs.append({
            'pdf_name': normalized_pdf_name,
            'folder_name': normalized_folder_name,
            'pdf_path': pdf_path,
            'folder_path': folder_path
        })
        
        # Check for case mismatch
        if normalized_pdf_name != normalized_folder_name:
            # Check if it's only a case difference
            if normalized_pdf_name.lower() == normalized_folder_name.lower():
                case_mismatches.append({
                    'pdf_name': normalized_pdf_name,
                    'folder_name': normalized_folder_name,
                    'pdf_path': pdf_path,
                    'folder_path': folder_path
                })
    else:
        unmatched_pdfs.append({
            'pdf_name': normalized_pdf_name,
            'pdf_path': pdf_path
        })

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total PDFs in SheetMusic:        {len(matched_pdfs) + len(unmatched_pdfs) + fake_books_count}")
print(f"  - Matched (have folders):      {len(matched_pdfs)}")
print(f"  - Unprocessed (no folders):    {len(unmatched_pdfs)}")
print(f"  - Fake Books (excluded):       {fake_books_count}")
print()
print(f"Case mismatches to fix:          {len(case_mismatches)}")
print()

# Display the 20 unprocessed PDFs
print("=" * 80)
print(f"UNPROCESSED PDFs - READY FOR AWS PIPELINE ({len(unmatched_pdfs)} total)")
print("=" * 80)
for i, pdf in enumerate(unmatched_pdfs, 1):
    pdf_path = Path(pdf['pdf_path'])
    parts = pdf_path.parts
    sheet_music_idx = parts.index('SheetMusic') if 'SheetMusic' in parts else -1
    if sheet_music_idx >= 0:
        rel_path = Path(*parts[sheet_music_idx + 1:])
    else:
        rel_path = pdf_path
    print(f"{i:2d}. {rel_path}")
print()

# Save unprocessed list for AWS processing
output_file = Path("ready_for_aws_processing.csv")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_Name', 'PDF_Path', 'Artist', 'Book_Name'])
    
    for pdf in unmatched_pdfs:
        pdf_path = Path(pdf['pdf_path'])
        parts = pdf_path.parts
        sheet_music_idx = parts.index('SheetMusic') if 'SheetMusic' in parts else -1
        if sheet_music_idx >= 0 and sheet_music_idx + 1 < len(parts):
            artist = parts[sheet_music_idx + 1]
        else:
            artist = ""
        
        writer.writerow([pdf['pdf_name'], pdf['pdf_path'], artist, pdf['pdf_name']])

print(f"✓ Saved AWS processing list to: {output_file}")
print()

# Report on case mismatches
if case_mismatches:
    print("=" * 80)
    print(f"CASE MISMATCHES ({len(case_mismatches)} total)")
    print("=" * 80)
    print("These PDFs and folders match except for letter casing.")
    print("This is cosmetic and doesn't affect functionality.")
    print()
    print("Sample mismatches (first 10):")
    for i, item in enumerate(case_mismatches[:10], 1):
        print(f"{i}. PDF:    {item['pdf_name']}")
        print(f"   Folder: {item['folder_name']}")
        print()
    
    # Save case mismatch report
    case_output = Path("case_mismatches.csv")
    with open(case_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['PDF_Name', 'Folder_Name', 'PDF_Path', 'Folder_Path'])
        
        for item in case_mismatches:
            writer.writerow([
                item['pdf_name'],
                item['folder_name'],
                item['pdf_path'],
                item['folder_path']
            ])
    
    print(f"✓ Saved case mismatch report to: {case_output}")
else:
    print("=" * 80)
    print("✓ NO CASE MISMATCHES - Perfect 1:1 mapping!")
    print("=" * 80)

print()
print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print(f"✓ {len(matched_pdfs)} PDFs have been successfully processed")
print(f"✓ {len(unmatched_pdfs)} PDFs are ready for AWS pipeline processing")
print(f"✓ {fake_books_count} Fake Books are excluded (as expected)")
print()
if case_mismatches:
    print(f"⚠ {len(case_mismatches)} case mismatches exist but don't affect functionality")
    print("  (Windows filesystem is case-insensitive)")
print()
