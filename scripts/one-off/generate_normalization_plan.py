#!/usr/bin/env python3
"""
Generate a normalization plan for renaming PDFs and folders.
Remove special characters, brackets, parentheses, and make names consistent.
"""

import csv
import re
from pathlib import Path

input_file = Path("book_reconciliation_validated.csv")
output_file = Path("normalization_plan.csv")

def normalize_name(name):
    """
    Normalize a name by removing special characters and standardizing capitalization.
    Rules:
    - Remove brackets [] and their contents
    - Keep parentheses with "page" information (e.g., "(page 01 - 40)")
    - Remove other parentheses () and their contents
    - Replace & with 'and'
    - Remove apostrophes, quotes
    - In page info: replace spaces with underscores, keep hyphens
    - Apply title case with special handling for acronyms
    - Replace multiple spaces with single space
    - Remove leading/trailing spaces and dashes
    - Keep: letters, numbers, spaces, hyphens, underscores
    """
    # Preserve page information in parentheses
    page_info = ''
    page_match = re.search(r'\(page[^)]+\)', name, re.IGNORECASE)
    if page_match:
        page_info = page_match.group(0)
        # Extract just the text without parentheses
        page_info_clean = page_info[1:-1]  # Remove ( and )
        # Replace spaces with underscores, keep alphanumeric and hyphens
        page_info_clean = re.sub(r'\s+', '_', page_info_clean)
        # Remove any remaining special characters except hyphens and underscores
        page_info_clean = re.sub(r'[^a-zA-Z0-9\-_]', '', page_info_clean)
        # Temporarily remove it with a safe placeholder
        name = name.replace(page_info, ' PAGEINFOPLACEHOLDER ')
    
    # Replace brackets and parentheses with underscores, keep their contents
    name = name.replace('[', '_').replace(']', '_')
    name = name.replace('(', '_').replace(')', '_')
    
    # Replace & with 'and'
    name = name.replace('&', 'and')
    
    # Remove apostrophes and quotes
    name = name.replace("'", '')
    name = name.replace('"', '')
    name = name.replace('`', '')
    
    # Remove other special characters but keep letters, numbers, spaces, hyphens, underscores
    name = re.sub(r'[^a-zA-Z0-9\s\-_]', '', name)
    
    # Restore page info if it existed
    if page_info:
        name = name.replace('PAGEINFOPLACEHOLDER', page_info_clean)
    
    # Replace multiple spaces with single space
    name = re.sub(r'\s+', ' ', name)
    
    # Remove leading/trailing spaces and dashes
    name = name.strip(' -')
    
    # Apply title case with special handling for acronyms
    name = apply_title_case(name)
    
    return name

def apply_title_case(name):
    """
    Apply title case with special handling for known acronyms and conventions.
    """
    # Known acronyms that should stay uppercase
    acronyms = ['PVG', 'SATB', 'MTI', 'PC', 'RSC', 'TYA', 'TV', 'DVD', 'CD', 'II', 'III', 'IV', 'V', 'VI']
    
    # Split into words
    words = name.split()
    result = []
    
    for word in words:
        # Check if it's an acronym (all caps, 2-4 letters)
        if word.upper() in acronyms:
            result.append(word.upper())
        # Check if it's a Roman numeral pattern
        elif re.match(r'^[IVX]+$', word.upper()) and len(word) <= 4:
            result.append(word.upper())
        # Check if it's a number
        elif word.isdigit():
            result.append(word)
        # Check if it contains underscores (page info)
        elif '_' in word:
            result.append(word)
        # Otherwise apply title case
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)

print("=" * 80)
print("GENERATING NORMALIZATION PLAN")
print("=" * 80)
print()

renames = []
pdf_renames = 0
folder_renames = 0

with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    
    for row in reader:
        rename_entry = {
            'Type': '',
            'Old_Path': '',
            'New_Path': '',
            'Old_Name': '',
            'New_Name': '',
            'Needs_Rename': 'NO',
            'Artist': '',
            'Status': row['Status']
        }
        
        # Process PDF
        if row['PDF_Path']:
            pdf_path = Path(row['PDF_Path'])
            old_name = pdf_path.stem
            new_name = normalize_name(old_name)
            
            if old_name != new_name:
                new_path = pdf_path.parent / f"{new_name}.pdf"
                rename_entry['Type'] = 'PDF'
                rename_entry['Old_Path'] = str(pdf_path)
                rename_entry['New_Path'] = str(new_path)
                rename_entry['Old_Name'] = old_name
                rename_entry['New_Name'] = new_name
                rename_entry['Needs_Rename'] = 'YES'
                rename_entry['Artist'] = row['PDF_Artist']
                renames.append(rename_entry.copy())
                pdf_renames += 1
        
        # Process Folder
        if row['Folder_Path']:
            folder_path = Path(row['Folder_Path'])
            old_name = folder_path.name
            new_name = normalize_name(old_name)
            
            if old_name != new_name:
                new_path = folder_path.parent / new_name
                rename_entry['Type'] = 'FOLDER'
                rename_entry['Old_Path'] = str(folder_path)
                rename_entry['New_Path'] = str(new_path)
                rename_entry['Old_Name'] = old_name
                rename_entry['New_Name'] = new_name
                rename_entry['Needs_Rename'] = 'YES'
                rename_entry['Artist'] = row['Folder_Artist']
                renames.append(rename_entry.copy())
                folder_renames += 1

# Write output
with open(output_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['Type', 'Needs_Rename', 'Artist', 'Old_Name', 'New_Name', 'Old_Path', 'New_Path', 'Status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for entry in renames:
        writer.writerow(entry)

print(f"✓ Generated {len(renames)} rename operations")
print(f"  - PDFs to rename: {pdf_renames}")
print(f"  - Folders to rename: {folder_renames}")
print()
print(f"✓ Output saved to: {output_file}")
print()
print("=" * 80)
print("SAMPLE RENAMES (first 10)")
print("=" * 80)

for i, entry in enumerate(renames[:10]):
    print(f"\n{i+1}. {entry['Type']} - {entry['Artist']}")
    print(f"   Old: {entry['Old_Name']}")
    print(f"   New: {entry['New_Name']}")

if len(renames) > 10:
    print(f"\n... and {len(renames) - 10} more")

print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Review normalization_plan.csv")
print("2. Make any manual adjustments if needed")
print("3. Run a script to execute the renames")
