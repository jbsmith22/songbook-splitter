"""
Validate complete inventory of source PDFs and processed output folders.
Creates book_reconciliation_validated.csv with actual current state.
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
                book_name = pdf_file.stem  # filename without .pdf extension
                # Remove artist prefix if present (e.g., "ACDC - Anthology" -> "Anthology")
                if book_name.startswith(f"{artist_name} - "):
                    book_name = book_name[len(artist_name) + 3:]
                
                pdfs.append({
                    'Artist': artist_name,
                    'BookName': book_name,
                    'SourcePath': str(pdf_file.relative_to(base)),
                    'SourceExists': True
                })
    
    return pdfs

def normalize_book_name(name):
    """Normalize book name for comparison - convert underscores to brackets."""
    # Replace _text_ with [text]
    import re
    normalized = re.sub(r'_([^_]+)_', r'[\1]', name)
    return normalized

def check_processed_folder(artist, book_name, processed_base):
    """Check if processed folder exists for this book."""
    # Try exact match first
    processed_path = Path(processed_base) / artist / book_name
    
    if processed_path.exists() and processed_path.is_dir():
        pdf_files = list(processed_path.glob("*.pdf"))
        return {
            'ProcessedExists': True,
            'ProcessedPath': str(processed_path.relative_to(processed_base)),
            'FileCount': len(pdf_files),
            'MatchType': 'exact'
        }
    
    # Try normalized name (convert underscores to brackets)
    normalized_name = normalize_book_name(book_name)
    if normalized_name != book_name:
        processed_path = Path(processed_base) / artist / normalized_name
        if processed_path.exists() and processed_path.is_dir():
            pdf_files = list(processed_path.glob("*.pdf"))
            return {
                'ProcessedExists': True,
                'ProcessedPath': str(processed_path.relative_to(processed_base)),
                'FileCount': len(pdf_files),
                'MatchType': 'normalized'
            }
    
    # Not found
    return {
        'ProcessedExists': False,
        'ProcessedPath': '',
        'FileCount': 0,
        'MatchType': 'none'
    }

def main():
    sheetmusic_base = "SheetMusic"
    processed_base = "ProcessedSongs"
    
    print("=" * 60)
    print("VALIDATING COMPLETE BOOK INVENTORY")
    print("=" * 60)
    print()
    
    # Get all source PDFs
    print(f"Scanning source PDFs in {sheetmusic_base}...")
    source_pdfs = get_all_source_pdfs(sheetmusic_base)
    print(f"Found {len(source_pdfs)} source PDF files")
    print()
    
    # Check processed folders for each source PDF
    print(f"Checking processed folders in {processed_base}...")
    results = []
    
    processed_count = 0
    missing_count = 0
    total_files = 0
    
    for pdf in source_pdfs:
        artist = pdf['Artist']
        book_name = pdf['BookName']
        
        # Check if processed folder exists
        processed_info = check_processed_folder(artist, book_name, processed_base)
        
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
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total source PDFs:        {len(source_pdfs)}")
    print(f"Processed (complete):     {processed_count}")
    print(f"Missing (not processed):  {missing_count}")
    print(f"Total output PDF files:   {total_files}")
    print()
    print(f"Results written to: {output_file}")
    print()
    
    # Show missing books
    if missing_count > 0:
        print("=" * 60)
        print(f"MISSING BOOKS ({missing_count})")
        print("=" * 60)
        for result in results:
            if result['Status'] == 'MISSING':
                print(f"  {result['Artist']} / {result['BookName']}")
        print()

if __name__ == "__main__":
    main()
