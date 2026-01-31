"""
Create a plan to rename folders to exactly match PDF filenames.
This ensures 1:1 exact name matching between source PDFs and output folders.
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
                return [normalized, parts[1].strip()]
    return [normalized]

def main():
    sheetmusic_base = Path("SheetMusic")
    processed_base = Path("ProcessedSongs")
    
    print("=" * 70)
    print("CREATING EXACT MATCH RENAME PLAN")
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
    
    # Get ALL folders
    print("Scanning all folders...")
    all_folders = {}
    
    for artist_dir in processed_base.iterdir():
        if not artist_dir.is_dir():
            continue
        
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            folder_name = book_dir.name
            pdf_count = len(list(book_dir.glob("*.pdf")))
            
            normalized_names = normalize_name(folder_name)
            for norm_name in normalized_names:
                if norm_name not in all_folders:
                    all_folders[norm_name] = []
                all_folders[norm_name].append({
                    'artist': artist_dir.name,
                    'folder_name': folder_name,
                    'full_path': str(book_dir),
                    'pdf_count': pdf_count
                })
    
    print(f"Found {sum(len(v) for v in all_folders.values())} folders")
    print()
    
    # Create rename plan
    print("Creating rename plan...")
    rename_operations = []
    exact_match_count = 0
    needs_rename_count = 0
    
    for pdf in all_pdfs:
        artist = pdf['artist']
        book_name = pdf['book_name']
        
        # Find matching folder
        normalized_names = normalize_name(book_name)
        matched_folder = None
        
        for norm_name in normalized_names:
            if norm_name in all_folders:
                candidates = all_folders[norm_name]
                for candidate in candidates:
                    if candidate['artist'].lower() == artist.lower():
                        matched_folder = candidate
                        break
                
                if not matched_folder and candidates:
                    matched_folder = candidates[0]
                
                if matched_folder:
                    break
        
        if matched_folder:
            current_folder_name = matched_folder['folder_name']
            target_folder_name = book_name  # Exact match to PDF name
            
            if current_folder_name == target_folder_name:
                # Already exact match
                exact_match_count += 1
            else:
                # Needs rename
                needs_rename_count += 1
                old_path = matched_folder['full_path']
                new_path = str(Path(old_path).parent / target_folder_name)
                
                rename_operations.append({
                    'Artist': artist,
                    'OldFolderName': current_folder_name,
                    'NewFolderName': target_folder_name,
                    'OldPath': old_path,
                    'NewPath': new_path,
                    'FileCount': matched_folder['pdf_count']
                })
    
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print(f"Total matched pairs:      {len(all_pdfs)}")
    print(f"Already exact matches:    {exact_match_count}")
    print(f"Need renaming:            {needs_rename_count}")
    print()
    
    if needs_rename_count > 0:
        # Write rename plan to CSV
        output_file = "exact_match_rename_plan.csv"
        fieldnames = ['Artist', 'OldFolderName', 'NewFolderName', 'OldPath', 'NewPath', 'FileCount']
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rename_operations)
        
        print(f"Rename plan written to: {output_file}")
        print()
        print("Sample renames:")
        for op in rename_operations[:10]:
            print(f"  {op['OldFolderName']}")
            print(f"    -> {op['NewFolderName']}")
        if needs_rename_count > 10:
            print(f"  ... and {needs_rename_count - 10} more")
        print()
    else:
        print("✅ All folders already match PDF names exactly!")
        print()

if __name__ == "__main__":
    main()
