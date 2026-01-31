#!/usr/bin/env python3
"""
Generate a CSV inventory of all original books and their conversion status.
"""
from pathlib import Path
import csv

def get_original_books():
    """Get all original PDF books from SheetMusic directory, excluding Sheets folders."""
    sheet_music_dir = Path('SheetMusic')
    
    books = []
    
    for artist_dir in sorted(sheet_music_dir.iterdir()):
        if not artist_dir.is_dir():
            continue
        
        artist_name = artist_dir.name
        
        # Find all PDF files in this artist's directory
        for pdf_file in artist_dir.rglob('*.pdf'):
            # Skip files in "Sheets" folders
            if 'Sheets' in pdf_file.parts:
                continue
            
            # Get relative path from artist directory
            rel_path = pdf_file.relative_to(artist_dir)
            book_name = pdf_file.stem  # Filename without .pdf extension
            
            books.append({
                'artist': artist_name,
                'book_path': str(rel_path),
                'book_name': book_name,
                'full_path': str(pdf_file)
            })
    
    return books

def get_converted_songs():
    """Get all converted songs from ProcessedSongs directory."""
    processed_dir = Path('ProcessedSongs')
    
    # Count songs per artist/book combination
    song_counts = {}
    
    for artist_dir in processed_dir.iterdir():
        if not artist_dir.is_dir():
            continue
        
        artist_name = artist_dir.name
        
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            book_name = book_dir.name
            
            # Count PDF files in this book directory
            song_count = len(list(book_dir.glob('*.pdf')))
            
            key = (artist_name, book_name)
            song_counts[key] = song_count
    
    return song_counts

def normalize_artist_name(name):
    """Normalize artist name for comparison."""
    # Handle common variations
    normalized = name.lower().strip()
    
    # Remove common prefixes/suffixes
    normalized = normalized.replace('the ', '')
    
    return normalized

def find_matching_book(artist, book_name, song_counts):
    """
    Try to find a matching book in the converted songs.
    Returns (matched_key, song_count) or (None, 0) if not found.
    """
    # Normalize artist name
    artist_norm = normalize_artist_name(artist)
    book_norm = book_name.lower().strip()
    
    # Try exact match first
    for (conv_artist, conv_book), count in song_counts.items():
        if normalize_artist_name(conv_artist) == artist_norm:
            if conv_book.lower().strip() == book_norm:
                return ((conv_artist, conv_book), count)
    
    # Try partial match on book name
    for (conv_artist, conv_book), count in song_counts.items():
        if normalize_artist_name(conv_artist) == artist_norm:
            if book_norm in conv_book.lower() or conv_book.lower() in book_norm:
                return ((conv_artist, conv_book), count)
    
    return (None, 0)

def main():
    print("Generating book inventory...")
    print()
    
    print("Scanning original books...")
    original_books = get_original_books()
    print(f"Found {len(original_books)} original book files")
    
    print("Scanning converted songs...")
    song_counts = get_converted_songs()
    print(f"Found {len(song_counts)} converted book folders")
    print()
    
    # Match books
    print("Matching books...")
    inventory = []
    
    for book in original_books:
        artist = book['artist']
        book_name = book['book_name']
        
        matched_key, song_count = find_matching_book(artist, book_name, song_counts)
        
        has_converted = matched_key is not None
        converted_folder = f"{matched_key[0]}\\{matched_key[1]}" if matched_key else ""
        
        inventory.append({
            'artist': artist,
            'original_book_name': book_name,
            'original_book_path': book['book_path'],
            'has_converted_songs': 'Yes' if has_converted else 'No',
            'song_count': song_count,
            'converted_folder': converted_folder
        })
    
    # Write to CSV
    output_file = 'book-inventory-updated.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['artist', 'original_book_name', 'original_book_path', 
                      'has_converted_songs', 'song_count', 'converted_folder']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(inventory)
    
    print(f"Inventory written to: {output_file}")
    print()
    
    # Statistics
    converted_count = sum(1 for item in inventory if item['has_converted_songs'] == 'Yes')
    not_converted_count = len(inventory) - converted_count
    total_songs = sum(item['song_count'] for item in inventory)
    
    print("=" * 80)
    print("Summary:")
    print(f"  Total original books: {len(inventory)}")
    print(f"  Books with converted songs: {converted_count}")
    print(f"  Books without converted songs: {not_converted_count}")
    print(f"  Total converted songs: {total_songs}")
    print("=" * 80)

if __name__ == '__main__':
    main()
