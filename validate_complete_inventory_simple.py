"""
Simple validation: For every PDF in SheetMusic, find a matching folder in ProcessedSongs.
A folder matches if its name equals the PDF filename (without .pdf extension).
"""
import os
import csv
from pathlib import Path

def get_all_source_pdfs(base_path):
    """Get ALL PDF files from SheetMusic directory, recursively."""
    pdfs = []
    base = Path(base_path)
    
    if not base.exists():
        print(f"ERROR: SheetMusic directory not found at {base_path}")
        return pdfs
    
    # Find all PDFs recursively
    for pdf_file in base.rglob("*.pdf"):
        book_name = pdf_file.stem  # filename without .pdf extension
        
        # Determine artist from path
        # Path structure: SheetMusic/Artist/...
        relative_path = pdf_file.relative_to(base)
        artist = relative_path.parts[0] if len(relative_path.parts) > 0 else "Unknown"
        
        pdfs.append({
            'Artist': artist,
            'BookName': book_name,
            'SourcePath': str(relative_path),
            'SourceFullPath': str(pdf_file)
        })
    
    return pdfs

def find_processed_folder(book_name, artist, processed_base):
    """Find a folder in ProcessedSongs that matches the book name."""
    base = Path(processed_base)
    
    if not base.exists():
        return None
    
    # Try exact match first (search recursively)
    for folder in base.rglob("*"):
        if folder.is_dir() and folder.name == book_name:
            pdf_files = list(folder.glob("*.pdf"))
            return {
                'ProcessedPath': str(folder.relative_to(base)),
                'FileCount': len(pdf_files),
                'FullPath': str(folder),
                'MatchType': 'exact'
            }
    
    # Try without artist prefix (e.g., "ACDC - Anthology" -> "Anthology")
    # Common patterns: "Artist - Book", "Artist - Book [Type]", etc.
    book_without_prefix = book_name
    if ' - ' in book_name:
        parts = book_name.split(' - ', 1)
        if len(parts) == 2:
            # Check if first part matches artist (case-insensitive)
            if parts[0].lower() == artist.lower():
                book_without_prefix = parts[1]
                
                # Search for folder with this name
                for folder in base.rglob("*"):
                    if folder.is_dir() and folder.name == book_without_prefix:
                        pdf_files = list(folder.glob("*.pdf"))
                        return {
                            'ProcessedPath': str(folder.relative_to(base)),
                            'FileCount': len(pdf_files),
                            'FullPath': str(folder),
                            'MatchType': 'without_artist_prefix'
                        }
    
    # Not found
    return None

def main():
    sheetmusic_base = "SheetMusic"
    processed_base = "ProcessedSongs"
    
    print("=" * 70)
    print("VALIDATING COMPLETE BOOK INVENTORY")
    print("=" * 70)
    print()
    
    # Get all source PDFs
    print(f"Scanning ALL PDFs in {sheetmusic_base} (recursively)...")
    source_pdfs = get_all_source_pdfs(sheetmusic_base)
    print(f"Found {len(source_pdfs)} source PDF files")
    print()
    
    # Check processed folders for each source PDF
    print(f"Searching for matching folders in {processed_base}...")
    results = []
    
    processed_count = 0
    missing_count = 0
    total_files = 0
    
    for i, pdf in enumerate(source_pdfs):
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(source_pdfs)}...")
        
        artist = pdf['Artist']
        book_name = pdf['BookName']
        
        # Find matching processed folder
        processed_info = find_processed_folder(book_name, artist, processed_base)
        
        if processed_info:
            result = {
                'Artist': artist,
                'BookName': book_name,
                'SourcePath': pdf['SourcePath'],
                'SourceExists': 'YES',
                'ProcessedPath': processed_info['ProcessedPath'],
                'ProcessedExists': 'YES',
                'FileCount': processed_info['FileCount'],
                'MatchType': processed_info['MatchType'],
                'Status': 'COMPLETE'
            }
            processed_count += 1
            total_files += processed_info['FileCount']
        else:
            result = {
                'Artist': artist,
                'BookName': book_name,
                'SourcePath': pdf['SourcePath'],
                'SourceExists': 'YES',
                'ProcessedPath': '',
                'ProcessedExists': 'NO',
                'FileCount': 0,
                'MatchType': 'none',
                'Status': 'MISSING'
            }
            missing_count += 1
        
        results.append(result)
    
    print(f"  Processed {len(source_pdfs)}/{len(source_pdfs)}")
    print()
    
    # Sort by Artist, then BookName
    results.sort(key=lambda x: (x['Artist'], x['BookName']))
    
    # Write to CSV
    output_file = "book_reconciliation_validated.csv"
    fieldnames = ['Artist', 'BookName', 'SourcePath', 'SourceExists', 
                  'ProcessedPath', 'ProcessedExists', 'FileCount', 'MatchType', 'Status']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print("Validation complete!")
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
