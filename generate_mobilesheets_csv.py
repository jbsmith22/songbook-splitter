#!/usr/bin/env python3
"""
MobileSheets Metadata Generator
Scans sheet music folder structure and generates CSV for MobileSheets import.

Expected folder structures:
  - Artist/Songbook/Song.pdf  (organized in books)
  - Artist/Song.pdf           (loose songs)

Output: Semicolon-separated CSV compatible with MobileSheets batch import
"""

import os
import csv
from pathlib import Path
from datetime import datetime

# Configuration - modify these paths as needed
SOURCE_DIRS = [
    r"D:\Work\songbook-splitter\ProcessedSongs",
    r"D:\Work\songbook-splitter\SheetMusicIndividualSheets"
]

OUTPUT_FILE = r"D:\Work\songbook-splitter\mobilesheets_import.csv"

# MobileSheets CSV fields we'll populate
# Full list: title, artists, albums, genres, composers, collections, customgroups, 
#            keys, keywords, tempo, signature, difficulty, duration, rating, notes, source
FIELDS = [
    'title',
    'artists', 
    'albums',      # Will use for songbook name
    'collections', # Will use for category (Broadway, Movie/TV, etc.)
    'source',      # Will store source folder info
    'files'        # Path to the PDF file
]

def clean_title(filename):
    """Extract clean song title from filename."""
    # Remove .pdf extension
    title = Path(filename).stem
    # Clean up common patterns
    title = title.replace('_', ' ')
    return title.strip()

def categorize_artist(artist_name):
    """Attempt to categorize artist into a collection/genre."""
    # You can customize these categories
    broadway_keywords = ['broadway', 'musical', 'wicked', 'hamilton', 'phantom']
    movie_keywords = ['movie', 'film', 'disney', 'soundtrack']
    
    artist_lower = artist_name.lower()
    
    # Could add more sophisticated categorization here
    return ""  # Leave blank for manual categorization

def scan_directory(base_path):
    """
    Scan a directory for PDF files and extract metadata from path structure.
    Yields dictionaries with metadata for each PDF found.
    """
    base = Path(base_path)
    
    if not base.exists():
        print(f"Warning: Directory does not exist: {base_path}")
        return
    
    print(f"Scanning: {base_path}")
    file_count = 0
    
    for pdf_file in base.rglob("*.pdf"):
        # Get relative path parts
        rel_path = pdf_file.relative_to(base)
        parts = rel_path.parts
        
        if len(parts) == 2:
            # Structure: Artist/Song.pdf (loose song)
            artist = parts[0]
            album = ""  # No songbook
            title = clean_title(parts[1])
        elif len(parts) >= 3:
            # Structure: Artist/Songbook/Song.pdf
            artist = parts[0]
            album = parts[1]  # Songbook name
            title = clean_title(parts[-1])
        else:
            # Just a PDF in root (shouldn't happen but handle it)
            artist = ""
            album = ""
            title = clean_title(pdf_file.name)
        
        file_count += 1
        
        yield {
            'title': title,
            'artists': artist,
            'albums': album,
            'collections': categorize_artist(artist),
            'source': base.name,  # ProcessedSongs or SheetMusicIndividualSheets
            'files': str(pdf_file)  # Full path to PDF
        }
    
    print(f"  Found {file_count} PDF files")

def generate_csv(output_path, source_dirs):
    """Generate MobileSheets-compatible CSV from all source directories."""
    
    all_entries = []
    
    for source_dir in source_dirs:
        for entry in scan_directory(source_dir):
            all_entries.append(entry)
    
    # Sort by artist, then album, then title
    all_entries.sort(key=lambda x: (x['artists'].lower(), x['albums'].lower(), x['title'].lower()))
    
    # Write CSV with semicolon separator (MobileSheets requirement)
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=';')
        writer.writeheader()
        writer.writerows(all_entries)
    
    print(f"\nGenerated: {output_path}")
    print(f"Total entries: {len(all_entries)}")
    
    # Print summary by artist
    artists = {}
    for entry in all_entries:
        artist = entry['artists'] or "(Unknown)"
        artists[artist] = artists.get(artist, 0) + 1
    
    print(f"\nArtists: {len(artists)}")
    print("\nTop 20 artists by song count:")
    for artist, count in sorted(artists.items(), key=lambda x: -x[1])[:20]:
        print(f"  {artist}: {count}")

def main():
    print("=" * 60)
    print("MobileSheets Metadata Generator")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    generate_csv(OUTPUT_FILE, SOURCE_DIRS)
    
    print("\n" + "=" * 60)
    print("Done! Import the CSV into MobileSheets using:")
    print("  Settings > Backup and Restore > CSV File Import")
    print("=" * 60)

if __name__ == "__main__":
    main()
