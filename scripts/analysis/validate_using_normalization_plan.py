"""
Validate inventory using the normalization plan as source of truth.
The normalization plan shows what the names SHOULD be after normalization.
"""
import csv
from pathlib import Path

def main():
    # Read normalization plan
    plan_file = "normalization_plan_fixed.csv"
    
    print("=" * 70)
    print("VALIDATING INVENTORY USING NORMALIZATION PLAN")
    print("=" * 70)
    print()
    
    with open(plan_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        plan_entries = list(reader)
    
    print(f"Loaded {len(plan_entries)} entries from normalization plan")
    print()
    
    # Group by book (PDF + FOLDER pairs)
    books = {}
    for entry in plan_entries:
        if entry['Type'] == 'PDF':
            artist = entry['Artist']
            new_name = entry['New_Name']
            if new_name.endswith('.pdf'):
                new_name = new_name[:-4]  # Remove .pdf extension
            
            key = f"{artist}|{new_name}"
            if key not in books:
                books[key] = {'artist': artist, 'book_name': new_name, 'pdf': None, 'folder': None}
            books[key]['pdf'] = entry
    
    for entry in plan_entries:
        if entry['Type'] == 'FOLDER':
            artist = entry['Artist']
            new_name = entry['New_Name']
            
            key = f"{artist}|{new_name}"
            if key not in books:
                books[key] = {'artist': artist, 'book_name': new_name, 'pdf': None, 'folder': None}
            books[key]['folder'] = entry
    
    print(f"Found {len(books)} unique books in normalization plan")
    print()
    
    # Now validate actual filesystem
    print("Validating filesystem...")
    results = []
    
    pdf_exists_count = 0
    folder_exists_count = 0
    both_exist_count = 0
    neither_exist_count = 0
    
    for key, book in books.items():
        artist = book['artist']
        book_name = book['book_name']
        
        # Check if PDF exists (use New_Path from plan)
        pdf_exists = False
        pdf_path = ""
        if book['pdf']:
            pdf_path = book['pdf']['New_Path']
            pdf_exists = Path(pdf_path).exists()
            if pdf_exists:
                pdf_exists_count += 1
        
        # Check if folder exists (use New_Path from plan)
        folder_exists = False
        folder_path = ""
        folder_file_count = 0
        if book['folder']:
            folder_path = book['folder']['New_Path']
            folder_exists = Path(folder_path).exists()
            if folder_exists:
                folder_exists_count += 1
                # Count PDFs in folder
                folder_file_count = len(list(Path(folder_path).glob("*.pdf")))
        
        # Determine status
        if pdf_exists and folder_exists:
            status = "COMPLETE"
            both_exist_count += 1
        elif pdf_exists and not folder_exists:
            status = "MISSING_FOLDER"
        elif not pdf_exists and folder_exists:
            status = "MISSING_PDF"
        else:
            status = "BOTH_MISSING"
            neither_exist_count += 1
        
        results.append({
            'Artist': artist,
            'BookName': book_name,
            'PDFPath': pdf_path,
            'PDFExists': 'YES' if pdf_exists else 'NO',
            'FolderPath': folder_path,
            'FolderExists': 'YES' if folder_exists else 'NO',
            'FileCount': folder_file_count,
            'Status': status
        })
    
    # Sort by artist, then book name
    results.sort(key=lambda x: (x['Artist'], x['BookName']))
    
    # Write to CSV
    output_file = "book_reconciliation_validated.csv"
    fieldnames = ['Artist', 'BookName', 'PDFPath', 'PDFExists', 
                  'FolderPath', 'FolderExists', 'FileCount', 'Status']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total books in plan:      {len(books)}")
    print(f"PDFs exist:               {pdf_exists_count}")
    print(f"Folders exist:            {folder_exists_count}")
    print(f"Both exist (COMPLETE):    {both_exist_count}")
    print(f"Neither exist:            {neither_exist_count}")
    print()
    
    # Calculate total files
    total_files = sum(r['FileCount'] for r in results if r['Status'] == 'COMPLETE')
    print(f"Total output PDF files:   {total_files}")
    print()
    print(f"Results written to: {output_file}")
    print()
    
    # Show missing folders
    missing_folders = [r for r in results if r['Status'] == 'MISSING_FOLDER']
    if missing_folders:
        print("=" * 70)
        print(f"BOOKS WITH MISSING FOLDERS ({len(missing_folders)})")
        print("=" * 70)
        for r in missing_folders:
            print(f"  {r['Artist']} / {r['BookName']}")
        print()

if __name__ == "__main__":
    main()
