"""
Validate current state: Find ALL PDFs and ALL folders, match them up.
Don't rely on normalization plan - work with actual current names.
"""
import csv
from pathlib import Path

def normalize_name(name):
    """Normalize for matching: lowercase, remove common variations."""
    normalized = name.lower()
    # Remove artist prefix patterns
    for sep in [' - ', ' -', '- ']:
        if sep in normalized:
            parts = normalized.split(sep, 1)
            if len(parts) == 2:
                # Keep both full name and without-prefix version
                return [normalized, parts[1].strip()]
    return [normalized]

def main():
    sheetmusic_base = Path("SheetMusic")
    processed_base = Path("ProcessedSongs")
    
    print("=" * 70)
    print("VALIDATING CURRENT STATE")
    print("=" * 70)
    print()
    
    # Get ALL PDFs
    print("Scanning all PDFs...")
    all_pdfs = []
    for pdf_file in sheetmusic_base.rglob("*.pdf"):
        relative_path = pdf_file.relative_to(sheetmusic_base)
        artist = relative_path.parts[0] if len(relative_path.parts) > 0 else "Unknown"
        book_name = pdf_file.stem
        
        all_pdfs.append({
            'artist': artist,
            'book_name': book_name,
            'path': str(relative_path),
            'full_path': str(pdf_file)
        })
    
    print(f"Found {len(all_pdfs)} PDFs")
    print()
    
    # Get ALL folders (book folders, not artist folders)
    print("Scanning all folders...")
    all_folders = {}  # key: normalized name, value: folder info
    
    for artist_dir in processed_base.iterdir():
        if not artist_dir.is_dir():
            continue
        
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            folder_name = book_dir.name
            pdf_count = len(list(book_dir.glob("*.pdf")))
            
            # Store with normalized names as keys
            normalized_names = normalize_name(folder_name)
            for norm_name in normalized_names:
                if norm_name not in all_folders:
                    all_folders[norm_name] = []
                all_folders[norm_name].append({
                    'artist': artist_dir.name,
                    'folder_name': folder_name,
                    'path': str(book_dir.relative_to(processed_base)),
                    'pdf_count': pdf_count
                })
    
    print(f"Found {sum(len(v) for v in all_folders.values())} folders")
    print()
    
    # Match PDFs to folders
    print("Matching PDFs to folders...")
    results = []
    matched_count = 0
    unmatched_count = 0
    total_files = 0
    
    for pdf in all_pdfs:
        artist = pdf['artist']
        book_name = pdf['book_name']
        
        # Try to find matching folder
        normalized_names = normalize_name(book_name)
        matched_folder = None
        
        for norm_name in normalized_names:
            if norm_name in all_folders:
                # Found potential matches
                candidates = all_folders[norm_name]
                # Prefer match in same artist folder (case-insensitive)
                for candidate in candidates:
                    if candidate['artist'].lower() == artist.lower():
                        matched_folder = candidate
                        break
                
                # If no artist match, take first candidate
                if not matched_folder and candidates:
                    matched_folder = candidates[0]
                
                if matched_folder:
                    break
        
        if matched_folder:
            results.append({
                'Artist': artist,
                'BookName': book_name,
                'SourcePath': pdf['path'],
                'SourceExists': 'YES',
                'ProcessedFolderName': matched_folder['folder_name'],
                'ProcessedPath': matched_folder['path'],
                'ProcessedExists': 'YES',
                'FileCount': matched_folder['pdf_count'],
                'Status': 'COMPLETE'
            })
            matched_count += 1
            total_files += matched_folder['pdf_count']
        else:
            results.append({
                'Artist': artist,
                'BookName': book_name,
                'SourcePath': pdf['path'],
                'SourceExists': 'YES',
                'ProcessedFolderName': '',
                'ProcessedPath': '',
                'ProcessedExists': 'NO',
                'FileCount': 0,
                'Status': 'MISSING'
            })
            unmatched_count += 1
    
    # Sort by artist, then book name
    results.sort(key=lambda x: (x['Artist'], x['BookName']))
    
    # Write to CSV
    output_file = "book_reconciliation_validated.csv"
    fieldnames = ['Artist', 'BookName', 'SourcePath', 'SourceExists',
                  'ProcessedFolderName', 'ProcessedPath', 'ProcessedExists',
                  'FileCount', 'Status']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total source PDFs:        {len(all_pdfs)}")
    print(f"Matched (COMPLETE):       {matched_count}")
    print(f"Unmatched (MISSING):      {unmatched_count}")
    print(f"Total output PDF files:   {total_files}")
    print()
    print(f"Completion rate: {matched_count}/{len(all_pdfs)} ({100*matched_count/len(all_pdfs):.1f}%)")
    print()
    print(f"Results written to: {output_file}")
    print()
    
    # Show missing
    if unmatched_count > 0:
        print("=" * 70)
        print(f"MISSING FOLDERS ({unmatched_count})")
        print("=" * 70)
        missing = [r for r in results if r['Status'] == 'MISSING']
        for r in missing[:20]:  # Show first 20
            print(f"  {r['Artist']} / {r['BookName']}")
        if unmatched_count > 20:
            print(f"  ... and {unmatched_count - 20} more")
        print()

if __name__ == "__main__":
    main()
