"""
Validate complete inventory with exact 1:1 matching.
Source PDF name (without .pdf) should exactly match ProcessedSongs folder name.
"""
import os
import csv
from pathlib import Path

def get_all_source_pdfs(base_path):
    """Get all PDF files from SheetMusic directory."""
    pdfs = []
    base = Path(base_path)
    
    if not base.exists():
        print(f"ERROR: SheetMusic directory not found at {base_path}")
        return pdfs
    
    for artist_dir in base.iterdir():
        if not artist_dir.is_dir():
            continue
            
        artist_name = artist_dir.name
        
        # Check for Books subfolder
        books_dir = artist_dir / "Books"
        if books_dir.exists() and books_dir.is_dir():
            for pdf_file in books_dir.glob("*.pdf"):
                # Use the exact filename without .pdf extension
                book_name = pdf_file.stem
                
                pdfs.append({
                    'Artist': artist_name,
                    'BookName': book_name,
                    'SourcePath': str(pdf_file.relative_to(base)),
                    'SourceExists': True
                })
    
    return pdfs

def check_processed_folder_exact(artist, book_name, processed_base):
    """Check if processed folder exists with exact name match."""
    # Exact match: ProcessedSongs/Artist/BookName
    processed_path = Path(processed_base) / artist / book_name
    
    if processed_path.exists() and processed_path.is_dir():
        # Count PDF files in the folder
        pdf_files = list(processed_path.glob("*.pdf"))
        return {
            'ProcessedExists': True,
            'ProcessedPath': str(processed_path.relative_to(processed_base)),
            'FileCount': len(pdf_files)
        }
    else:
        return {
            'ProcessedExists': False,
            'ProcessedPath': '',
            'FileCount': 0
        }

def main():
    sheetmusic_base = "SheetMusic"
    processed_base = "ProcessedSongs"
    
    print("=" * 70)
    print("VALIDATING COMPLETE BOOK INVENTORY (EXACT MATCHING)")
    print("=" * 70)
    print()
    
    # Get all source PDFs
    print(f"Scanning source PDFs in {sheetmusic_base}...")
    source_pdfs = get_all_source_pdfs(sheetmusic_base)
    print(f"Found {len(source_pdfs)} source PDF files")
    print()
    
    # Check processed folders for each source PDF
    print(f"Checking processed folders in {processed_base} (exact name matching)...")
    results = []
    
    processed_count = 0
    missing_count = 0
    total_files = 0
    
    for pdf in source_pdfs:
        artist = pdf['Artist']
        book_name = pdf['BookName']
        
        # Check if exact matching folder exists
        processed_info = check_processed_folder_exact(artist, book_name, processed_base)
        
        # Combine information
        result = {
            'Artist': artist,
            'BookName': book_name,
            'SourcePath': pdf['SourcePath'],
            'SourceExists': 'YES',
            'ProcessedPath': processed_info['ProcessedPath'],
            'ProcessedExists': 'YES' if processed_info['ProcessedExists'] else 'NO',
            'FileCount': processed_info['FileCount'],
            'Status': 'COMPLETE' if processed_info['ProcessedExists'] else 'MISSING'
        }
        
        results.append(result)
        
        if processed_info['ProcessedExists']:
            processed_count += 1
            total_files += processed_info['FileCount']
        else:
            missing_count += 1
    
    # Sort by Artist, then BookName
    results.sort(key=lambda x: (x['Artist'], x['BookName']))
    
    # Write to CSV
    output_file = "book_reconciliation_validated.csv"
    fieldnames = ['Artist', 'BookName', 'SourcePath', 'SourceExists', 
                  'ProcessedPath', 'ProcessedExists', 'FileCount', 'Status']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"Validation complete!")
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total source PDFs:        {len(source_pdfs)}")
    print(f"Processed (complete):     {processed_count}")
    print(f"Missing (not processed):  {missing_count}")
    print(f"Total output PDF files:   {total_files}")
    print()
    print(f"Completion rate: {processed_count}/{len(source_pdfs)} ({100*processed_count/len(source_pdfs):.1f}%)")
    print()
    print(f"Results written to: {output_file}")
    print()
    
    # Show missing books
    if missing_count > 0:
        print("=" * 70)
        print(f"MISSING BOOKS ({missing_count})")
        print("=" * 70)
        for result in results:
            if result['Status'] == 'MISSING':
                print(f"  {result['Artist']} / {result['BookName']}")
        print()

if __name__ == "__main__":
    main()
