#!/usr/bin/env python3
"""
Fix Folder_Artist and Folder_Book columns based on Folder_Path.
"""

import csv
from pathlib import Path

input_file = Path("book_reconciliation.csv")
output_file = Path("book_reconciliation_fixed.csv")

print("Reading CSV and fixing folder columns...")

rows_fixed = 0
rows_total = 0

with open(input_file, 'r', encoding='utf-8') as f_in:
    reader = csv.DictReader(f_in)
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f_out:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in reader:
            rows_total += 1
            
            # If there's a Folder_Path, extract artist and book from it
            if row['Folder_Path']:
                folder_path = Path(row['Folder_Path'])
                
                # Path structure: c:\Work\AWSMusic\ProcessedSongs\{Artist}\{Book}
                if folder_path.exists() and folder_path.is_dir():
                    # Get the last two parts: Artist and Book
                    parts = folder_path.parts
                    if len(parts) >= 2:
                        book_name = parts[-1]  # Last part is book folder name
                        artist_name = parts[-2]  # Second to last is artist folder name
                        
                        # Update the row if values changed
                        if row['Folder_Artist'] != artist_name or row['Folder_Book'] != book_name:
                            row['Folder_Artist'] = artist_name
                            row['Folder_Book'] = book_name
                            rows_fixed += 1
            
            writer.writerow(row)

print(f"✓ Fixed {rows_fixed} rows out of {rows_total} total rows")
print(f"✓ Output saved to: {output_file}")
