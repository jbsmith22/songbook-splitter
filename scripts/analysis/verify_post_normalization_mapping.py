#!/usr/bin/env python3
"""
Verify PDF-to-Folder mapping after normalization.
Uses normalization_plan_fixed.csv to understand current names.
"""

from pathlib import Path
import csv

print("=" * 80)
print("POST-NORMALIZATION MAPPING VERIFICATION")
print("=" * 80)
print()

# Step 1: Load the normalization plan to understand current names
print("Loading normalization plan...")
normalization_plan = {}

with open('normalization_plan_fixed.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        item_type = row['Type']
        old_path = row['Old_Path']
        new_name = row['New_Name']
        status = row['Status']
        
        # Store the mapping: old_path -> new_name
        normalization_plan[old_path] = {
            'type': item_type,
            'new_name': new_name,
            'status': status
        }

print(f"✓ Loaded {len(normalization_plan)} normalization entries")
print()

# Step 2: Load the original reconciliation to understand PDF-to-Folder relationships
print("Loading original reconciliation...")
reconciliation = []

with open('book_reconciliation_validated.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        reconciliation.append(row)

print(f"✓ Loaded {len(reconciliation)} reconciliation entries")
print()

# Step 3: Analyze the data
print("Analyzing mappings...")
print()

matched_pdfs = []
unmatched_pdfs = []
fake_books = []

for row in reconciliation:
    status = row['Status']
    pdf_path = row['PDF_Path']
    pdf_book = row['PDF_Book']
    folder_path = row['Folder_Path']
    
    # Skip if no PDF
    if not pdf_path:
        continue
    
    # Check if it's a Fake Book
    if '_Fake Books' in pdf_path:
        fake_books.append({
            'pdf_path': pdf_path,
            'pdf_book': pdf_book
        })
        continue
    
    # Get the normalized PDF name
    if pdf_path in normalization_plan:
        normalized_pdf_name = normalization_plan[pdf_path]['new_name']
    else:
        # PDF wasn't renamed, use original name
        normalized_pdf_name = pdf_book
    
    # Get the normalized folder name (if folder exists)
    normalized_folder_name = None
    if folder_path and folder_path in normalization_plan:
        normalized_folder_name = normalization_plan[folder_path]['new_name']
    elif folder_path:
        # Folder wasn't renamed, use original name
        folder_name = Path(folder_path).name
        normalized_folder_name = folder_name
    
    # Check if PDF has a matching folder
    if status == 'MATCHED':
        matched_pdfs.append({
            'pdf_name': normalized_pdf_name,
            'folder_name': normalized_folder_name,
            'pdf_path': pdf_path
        })
    else:  # UNMATCHED_PDF
        unmatched_pdfs.append({
            'pdf_name': normalized_pdf_name,
            'pdf_path': pdf_path,
            'original_status': status
        })

print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Matched PDFs (have folders):     {len(matched_pdfs)}")
print(f"Unmatched PDFs (no folders):     {len(unmatched_pdfs)}")
print(f"Fake Books (excluded):           {len(fake_books)}")
print(f"Total PDFs:                      {len(matched_pdfs) + len(unmatched_pdfs) + len(fake_books)}")
print()

# Verify the math
expected_unprocessed = len(unmatched_pdfs)
print(f"Expected unprocessed PDFs: {expected_unprocessed}")
print()

# Display unmatched PDFs
if unmatched_pdfs:
    print("=" * 80)
    print(f"UNPROCESSED PDFs ({len(unmatched_pdfs)} total)")
    print("=" * 80)
    for i, pdf in enumerate(unmatched_pdfs, 1):
        pdf_path = Path(pdf['pdf_path'])
        # Get relative path from SheetMusic folder
        try:
            rel_path = pdf_path.relative_to(Path.cwd() / 'SheetMusic')
        except ValueError:
            # If that fails, just show the path parts after SheetMusic
            parts = pdf_path.parts
            sheet_music_idx = parts.index('SheetMusic') if 'SheetMusic' in parts else -1
            if sheet_music_idx >= 0:
                rel_path = Path(*parts[sheet_music_idx + 1:])
            else:
                rel_path = pdf_path
        print(f"{i}. {rel_path}")
        print(f"   Normalized name: {pdf['pdf_name']}")
    print()

# Save unprocessed list
output_file = Path("unprocessed_pdfs_verified.csv")
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['PDF_Name_Normalized', 'PDF_Path', 'Artist'])
    
    for pdf in unmatched_pdfs:
        pdf_path = Path(pdf['pdf_path'])
        parts = pdf_path.parts
        # Find SheetMusic in the path
        sheet_music_idx = parts.index('SheetMusic') if 'SheetMusic' in parts else -1
        if sheet_music_idx >= 0 and sheet_music_idx + 1 < len(parts):
            artist = parts[sheet_music_idx + 1]
        else:
            artist = ""
        
        writer.writerow([pdf['pdf_name'], pdf['pdf_path'], artist])

print(f"✓ Saved unprocessed list to: {output_file}")
print()

# Verify that normalized names match
print("=" * 80)
print("VERIFICATION: Do normalized PDF names match folder names?")
print("=" * 80)
mismatches = []
for item in matched_pdfs:
    if item['pdf_name'] != item['folder_name']:
        mismatches.append(item)

if mismatches:
    print(f"⚠ Found {len(mismatches)} mismatches where PDF name != Folder name:")
    for item in mismatches[:10]:  # Show first 10
        print(f"  PDF:    {item['pdf_name']}")
        print(f"  Folder: {item['folder_name']}")
        print()
else:
    print(f"✓ All {len(matched_pdfs)} matched PDFs have identical folder names!")
    print("  Normalization was successful!")

