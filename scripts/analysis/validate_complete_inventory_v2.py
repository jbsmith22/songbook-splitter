"""
Validate complete inventory of source PDFs and processed output folders.
Handles various naming conventions and normalizations.
"""
import os
import csv
import re
from pathlib import Path

def normalize_for_comparison(name):
    """Normalize name for fuzzy matching."""
    # Convert to lowercase
    normalized = name.lower()
    # Replace underscores with spaces
    normalized = normalized.replace('_', ' ')
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    # Remove common punctuation
    normalized = normalized.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
    return normalized

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
                full_book_name = pdf_file.stem  # filename without .pdf extension
                
                pdfs.append({
                    'Artist': artist_name,
                    'FullBookName': full_book_name,
                    'SourcePath': str(pdf_file.relative_to(base)),
                    'SourceExists': True
                })
    
    return pdfs

def find_matching_processed_folder(artist, full_book_name, processed_base):
    """Find matching processed folder with fuzzy matching."""
    artist_path = Path(processed_base) / artist
    
    if not artist_path.exists():
        return None
    
    # Normalize the source book name for comparison
    source_normalized = normalize_for_comparison(full_book_name)
    
    # Try to find matching folder
    best_match = None
    best_score = 0
    
    for folder in artist_path.iterdir():
        if not folder.is_dir():
            continue
        
        folder_name = folder.name
        folder_normalized = normalize_for_comparison(folder_name)
        
        # Check for exact match after normalization
        if source_normalized == folder_normalized:
            pdf_files = list(folder.glob("*.pdf"))
            return {
                'ProcessedExists': True,
                'ProcessedPath': str(folder.relative_to(processed_base)),
                'ProcessedFolderName': folder_name,
                'FileCount': len(pdf_files),
                'MatchType': 'exact_normalized'
            }
        
        # Check if folder name is contained in source name or vice versa
        if folder_normalized in source_normalized or source_normalized in folder_normalized:
            # Calculate similarity score (longer match is better)
            score = min(len(folder_normalized), len(source_normalized))
            if score > best_score:
                best_score = score
                pdf_files = list(folder.glob("*.pdf"))
                best_match = {
                    'ProcessedExists': True,
                    'ProcessedPath': str(folder.relative_to(processed_base)),
                    'ProcessedFolderName': folder_name,
                    'FileCount': len(pdf_files),
                    'MatchType': 'fuzzy'
                }
    
    if best_match:
        return best_match
    
    # Not found
    return {
        'ProcessedExists': False,
        'ProcessedPath': '',
        'ProcessedFolderName': '',
        'FileCount': 0,
        'MatchType': 'none'
    }

def main():
    sheetmusic_base = "SheetMusic"
    processed_base = "ProcessedSongs"
    
    print("=" * 70)
    print("VALIDATING COMPLETE BOOK INVENTORY")
    print("=" * 70)
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
        full_book_name = pdf['FullBookName']
        
        # Find matching processed folder
        processed_info = find_matching_processed_folder(artist, full_book_name, processed_base)
        
        # Combine information
        result = {
            'Artist': artist,
            'SourceBookName': full_book_name,
            'SourcePath': pdf['SourcePath'],
            'SourceExists': 'YES',
            'ProcessedFolderName': processed_info.get('ProcessedFolderName', ''),
            'ProcessedPath': processed_info['ProcessedPath'],
            'ProcessedExists': 'YES' if processed_info['ProcessedExists'] else 'NO',
            'FileCount': processed_info['FileCount'],
            'MatchType': processed_info['MatchType'],
            'Status': 'COMPLETE' if processed_info['ProcessedExists'] else 'MISSING'
        }
        
        results.append(result)
        
        if processed_info['ProcessedExists']:
            processed_count += 1
            total_files += processed_info['FileCount']
        else:
            missing_count += 1
    
    # Sort by Artist, then SourceBookName
    results.sort(key=lambda x: (x['Artist'], x['SourceBookName']))
    
    # Write to CSV
    output_file = "book_reconciliation_validated.csv"
    fieldnames = ['Artist', 'SourceBookName', 'SourcePath', 'SourceExists', 
                  'ProcessedFolderName', 'ProcessedPath', 'ProcessedExists', 
                  'FileCount', 'MatchType', 'Status']
    
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
                print(f"  {result['Artist']} / {result['SourceBookName']}")
        print()

if __name__ == "__main__":
    main()
