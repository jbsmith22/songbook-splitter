import os
from pathlib import Path
import csv
from difflib import SequenceMatcher

# Get all input PDFs with normalized keys
input_folder = r'SheetMusic'
input_pdfs = {}  # normalized_key -> (actual_path, artist, book_name)

for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.lower().endswith('.pdf'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, input_folder)
            
            parts = rel_path.split(os.sep)
            if len(parts) >= 2:
                artist = parts[0]
                book_pdf = parts[-1]
                book_name = book_pdf[:-4] if book_pdf.lower().endswith('.pdf') else book_pdf
                
                # Create a normalized key for matching
                normalized_key = f"{artist.lower()}|||{book_name.lower()}"
                input_pdfs[normalized_key] = (rel_path, artist, book_name)

print(f"Total input PDFs: {len(input_pdfs)}")

# Get all output folders
output_folder = r'ProcessedSongs'
output_folders = {}  # normalized_key -> (actual_path, artist, book_name, pdf_count, pdf_list)

for root, dirs, files in os.walk(output_folder):
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    if pdf_files:
        rel_path = os.path.relpath(root, output_folder)
        parts = rel_path.split(os.sep)
        if len(parts) >= 2:
            artist = parts[0]
            book = parts[1]
            
            normalized_key = f"{artist.lower()}|||{book.lower()}"
            output_folders[normalized_key] = (rel_path, artist, book, len(pdf_files), sorted(pdf_files))

print(f"Total output folders: {len(output_folders)}")

# Find output folders that could match the same input
print("\n" + "=" * 80)
print("FINDING DUPLICATE OUTPUT FOLDERS")
print("=" * 80)

# Group output folders by artist
outputs_by_artist = {}
for norm_key, (path, artist, book, count, pdfs) in output_folders.items():
    artist_lower = artist.lower()
    if artist_lower not in outputs_by_artist:
        outputs_by_artist[artist_lower] = []
    outputs_by_artist[artist_lower].append((norm_key, path, artist, book, count, pdfs))

# For each input PDF, find all possible output matches
duplicates = []

for input_key, (input_path, input_artist, input_book) in input_pdfs.items():
    artist_lower = input_artist.lower()
    
    if artist_lower not in outputs_by_artist:
        continue
    
    # Find all output folders for this artist that could match this input
    possible_matches = []
    
    for out_key, out_path, out_artist, out_book, count, pdfs in outputs_by_artist[artist_lower]:
        # Check if the book names are similar
        input_book_lower = input_book.lower()
        out_book_lower = out_book.lower()
        
        # Remove common variations for comparison
        def normalize_for_comparison(s):
            s = s.lower()
            # Replace bracket styles
            s = s.replace('[', '_').replace(']', '_')
            s = s.replace('(', '_').replace(')', '_')
            # Remove extra spaces
            s = ' '.join(s.split())
            return s
        
        input_normalized = normalize_for_comparison(input_book)
        output_normalized = normalize_for_comparison(out_book)
        
        # Calculate similarity
        similarity = SequenceMatcher(None, input_normalized, output_normalized).ratio()
        
        if similarity > 0.7:  # 70% similar
            possible_matches.append((out_path, out_artist, out_book, count, pdfs, similarity))
    
    # If we found multiple matches for this input, it's a duplicate
    if len(possible_matches) > 1:
        duplicates.append({
            'input': input_path,
            'input_artist': input_artist,
            'input_book': input_book,
            'matches': possible_matches
        })

print(f"\nFound {len(duplicates)} input PDFs with multiple output folders")

# Display duplicates
if duplicates:
    print("\n" + "=" * 80)
    print("DUPLICATE OUTPUT FOLDERS (Multiple outputs for same input)")
    print("=" * 80)
    
    for dup in duplicates:
        print(f"\nInput: {dup['input']}")
        print(f"  Possible output folders ({len(dup['matches'])}):")
        
        for i, (path, artist, book, count, pdfs, similarity) in enumerate(dup['matches'], 1):
            print(f"\n  {i}. {path}")
            print(f"     PDFs: {count}")
            print(f"     Similarity: {similarity*100:.1f}%")
            print(f"     First 3 files:")
            for pdf in pdfs[:3]:
                print(f"       - {pdf}")
            if len(pdfs) > 3:
                print(f"       ... and {len(pdfs) - 3} more")

# Save to CSV for review
with open('duplicate_output_folders.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Input PDF', 'Output Folder 1', 'PDF Count 1', 'Output Folder 2', 'PDF Count 2', 'Similarity', 'Action Needed'])
    
    for dup in duplicates:
        matches = sorted(dup['matches'], key=lambda x: -x[5])  # Sort by similarity
        if len(matches) >= 2:
            writer.writerow([
                dup['input'],
                matches[0][0],  # Best match path
                matches[0][3],  # Best match count
                matches[1][0],  # Second match path
                matches[1][3],  # Second match count
                f"{matches[0][5]*100:.1f}% vs {matches[1][5]*100:.1f}%",
                'Compare and choose'
            ])

print(f"\n\nResults saved to: duplicate_output_folders.csv")
