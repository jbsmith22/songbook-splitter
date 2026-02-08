#!/usr/bin/env python3
"""
MobileSheets Prep Script
Copies sheet music PDFs to Google Drive and generates import CSV.

Run with: py copy_to_mobilesheets.py
"""

import csv
import shutil
from pathlib import Path
from datetime import datetime

# === CONFIGURATION ===
SOURCE_DIRS = [
    r"D:\Work\songbook-splitter\ProcessedSongs",
    r"D:\Work\songbook-splitter\SheetMusicIndividualSheets"
]

DEST_DIR = Path(r"G:\My Drive\SheetMusicMobileSheets")
CSV_FILE = DEST_DIR / "mobilesheets_import.csv"

# MobileSheets CSV fields (semicolon-separated)
FIELDS = ['title', 'artists', 'albums', 'collections', 'files']


def clean_title(filename):
    """Extract clean song title from filename."""
    return Path(filename).stem.replace('_', ' ').strip()


def process_source(source_path, dest_base):
    """
    Process one source directory.
    Copies files and yields metadata dicts.
    """
    source = Path(source_path)
    source_name = source.name  # e.g., "ProcessedSongs"
    dest_root = dest_base / source_name
    
    if not source.exists():
        print(f"  WARNING: Source not found: {source_path}")
        return
    
    print(f"\nProcessing: {source_path}")
    
    copied = 0
    skipped = 0
    total = 0
    
    for pdf in source.rglob("*.pdf"):
        total += 1
        rel_path = pdf.relative_to(source)
        parts = rel_path.parts
        
        # Extract metadata from path structure
        if len(parts) >= 3:
            # Artist/Songbook/Song.pdf
            artist = parts[0]
            album = parts[1]
            title = clean_title(parts[-1])
        elif len(parts) == 2:
            # Artist/Song.pdf
            artist = parts[0]
            album = ""
            title = clean_title(parts[-1])
        else:
            artist = ""
            album = ""
            title = clean_title(pdf.name)
        
        # Destination path (preserves structure under source name)
        dest_file = dest_root / rel_path
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy if new or updated
        if not dest_file.exists():
            shutil.copy2(pdf, dest_file)
            copied += 1
        elif pdf.stat().st_mtime > dest_file.stat().st_mtime:
            shutil.copy2(pdf, dest_file)
            copied += 1
        else:
            skipped += 1
        
        # Progress every 500 files
        if total % 500 == 0:
            print(f"  ... {total} files processed")
        
        # Relative path for CSV (relative to DEST_DIR)
        csv_path = f"{source_name}/{rel_path.as_posix()}"
        
        yield {
            'title': title,
            'artists': artist,
            'albums': album,
            'collections': source_name,  # Use source as collection for easy filtering
            'files': csv_path
        }
    
    print(f"  Total: {total} | Copied: {copied} | Unchanged: {skipped}")


def main():
    print("=" * 60)
    print("MobileSheets Prep Script")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print(f"\nDestination: {DEST_DIR}")
    
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    
    # Collect all entries
    all_entries = []
    for source_dir in SOURCE_DIRS:
        for entry in process_source(source_dir, DEST_DIR):
            all_entries.append(entry)
    
    # Sort by artist, album, title
    all_entries.sort(key=lambda x: (
        x['artists'].lower(),
        x['albums'].lower(),
        x['title'].lower()
    ))
    
    # Write CSV (semicolon delimiter for MobileSheets)
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, delimiter=';')
        writer.writeheader()
        writer.writerows(all_entries)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"CSV generated: {CSV_FILE}")
    print(f"Total songs: {len(all_entries)}")
    
    # Stats by collection
    collections = {}
    for e in all_entries:
        c = e['collections']
        collections[c] = collections.get(c, 0) + 1
    
    print("\nBy source:")
    for c, count in sorted(collections.items()):
        print(f"  {c}: {count}")
    
    # Artist count
    artists = set(e['artists'] for e in all_entries if e['artists'])
    print(f"\nUnique artists: {len(artists)}")
    
    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Wait for Google Drive to sync")
    print("2. On tablet, open MobileSheets")
    print("3. Settings > Backup and Restore > CSV File Import")
    print("4. Browse to Google Drive > SheetMusicMobileSheets")
    print("5. Select mobilesheets_import.csv")
    print("=" * 60)


if __name__ == "__main__":
    main()
