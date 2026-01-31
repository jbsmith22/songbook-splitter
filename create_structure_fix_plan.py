"""
Create a plan to restructure SheetMusic to match ProcessedSongs structure.
- Remove Books subfolders
- Fix artist folder casing
- Ensure structure: SheetMusic\Artist\Book.pdf matches ProcessedSongs\Artist\Book\
"""
import csv
from pathlib import Path
from collections import defaultdict

def main():
    sheetmusic_base = Path("SheetMusic")
    processed_base = Path("ProcessedSongs")
    
    print("=" * 70)
    print("CREATING STRUCTURE FIX PLAN")
    print("=" * 70)
    print()
    
    # Get all current PDFs and their locations
    print("Scanning current PDF locations...")
    current_pdfs = []
    for pdf_file in sheetmusic_base.rglob("*.pdf"):
        relative_path = pdf_file.relative_to(sheetmusic_base)
        parts = relative_path.parts
        
        # Determine current artist folder
        current_artist = parts[0] if len(parts) > 0 else "Unknown"
        book_name = pdf_file.stem
        
        current_pdfs.append({
            'book_name': book_name,
            'current_artist': current_artist,
            'current_path': str(pdf_file),
            'has_books_subfolder': 'Books' in parts or 'books' in parts
        })
    
    print(f"Found {len(current_pdfs)} PDFs")
    print()
    
    # Get all processed folders to determine correct artist casing
    print("Scanning ProcessedSongs for correct artist names...")
    artist_casing = {}  # lowercase -> correct casing
    
    for artist_dir in processed_base.iterdir():
        if artist_dir.is_dir():
            artist_name = artist_dir.name
            artist_casing[artist_name.lower()] = artist_name
    
    print(f"Found {len(artist_casing)} artist folders in ProcessedSongs")
    print()
    
    # Create restructure plan
    print("Creating restructure plan...")
    operations = []
    
    for pdf in current_pdfs:
        book_name = pdf['book_name']
        current_artist = pdf['current_artist']
        current_path = Path(pdf['current_path'])
        
        # Determine correct artist casing from ProcessedSongs
        correct_artist = artist_casing.get(current_artist.lower(), current_artist)
        
        # Target path: SheetMusic\Artist\Book.pdf (no Books subfolder)
        target_path = sheetmusic_base / correct_artist / f"{book_name}.pdf"
        
        # Check if move is needed
        if current_path != target_path:
            operations.append({
                'BookName': book_name,
                'CurrentArtist': current_artist,
                'CorrectArtist': correct_artist,
                'CurrentPath': str(current_path),
                'TargetPath': str(target_path),
                'NeedsArtistRename': current_artist != correct_artist,
                'NeedsFolderRestructure': pdf['has_books_subfolder']
            })
    
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Total PDFs:                    {len(current_pdfs)}")
    print(f"Need restructuring:            {len(operations)}")
    print(f"Already correct:               {len(current_pdfs) - len(operations)}")
    print()
    
    # Breakdown by type of change
    artist_rename_count = sum(1 for op in operations if op['NeedsArtistRename'])
    folder_restructure_count = sum(1 for op in operations if op['NeedsFolderRestructure'])
    
    print(f"Need artist casing fix:        {artist_rename_count}")
    print(f"Need Books folder removal:     {folder_restructure_count}")
    print()
    
    if operations:
        # Write to CSV
        output_file = "structure_fix_plan.csv"
        fieldnames = ['BookName', 'CurrentArtist', 'CorrectArtist', 'CurrentPath', 
                      'TargetPath', 'NeedsArtistRename', 'NeedsFolderRestructure']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(operations)
        
        print(f"Plan written to: {output_file}")
        print()
        
        # Show samples
        print("Sample operations:")
        for op in operations[:10]:
            print(f"  {op['CurrentPath']}")
            print(f"    -> {op['TargetPath']}")
        if len(operations) > 10:
            print(f"  ... and {len(operations) - 10} more")
        print()
    else:
        print("✅ All PDFs already in correct structure!")
        print()

if __name__ == "__main__":
    main()
