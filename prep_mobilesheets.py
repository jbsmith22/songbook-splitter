#!/usr/bin/env python3
"""
MobileSheets Prep Script with PDF Metadata Embedding
1. Embeds Artist/Title/Album metadata into PDFs using exiftool
2. Copies PDFs to Google Drive

PREREQUISITE: Install exiftool from https://exiftool.org/
  - Download Windows executable
  - Extract exiftool(-k).exe, rename to exiftool.exe
  - Place in same folder as this script OR add to PATH

Run with: py prep_mobilesheets.py
"""

import subprocess
import shutil
from pathlib import Path
from datetime import datetime
import sys

# === CONFIGURATION ===
SOURCE_DIRS = [
    r"D:\Work\songbook-splitter\ProcessedSongs",
    r"D:\Work\songbook-splitter\SheetMusicIndividualSheets"
]

DEST_DIR = Path(r"G:\My Drive\SheetMusicMobileSheets")

# Path to exiftool (if not in PATH, put full path here)
EXIFTOOL = "exiftool"  # or r"D:\Tools\exiftool.exe"


def check_exiftool():
    """Verify exiftool is available."""
    try:
        result = subprocess.run([EXIFTOOL, "-ver"], capture_output=True, text=True)
        print(f"ExifTool version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("ERROR: exiftool not found!")
        print("Download from https://exiftool.org/")
        print("Place exiftool.exe in this folder or add to PATH")
        return False


def clean_title(filename):
    """Extract clean song title from filename."""
    return Path(filename).stem.replace('_', ' ').strip()


def embed_metadata_and_copy(pdf_path, dest_path, title, artist, album):
    """
    Embed metadata into PDF and copy to destination.
    Uses exiftool to write metadata directly.
    """
    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # First copy the file to destination
    shutil.copy2(pdf_path, dest_path)
    
    # Build exiftool command to embed metadata
    # MobileSheets reads standard PDF fields + XMP
    cmd = [
        EXIFTOOL,
        f"-Title={title}",
        f"-Author={artist}",           # PDF Author -> MobileSheets Artist
        f"-Subject={album}",           # PDF Subject -> can use for Album
        f"-XMP-dc:Title={title}",      # XMP Dublin Core Title
        f"-XMP-dc:Creator={artist}",   # XMP Dublin Core Creator -> Artist
        f"-XMP-dc:Description={album}",# XMP Description -> Album
        "-overwrite_original",
        str(dest_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  Warning: exiftool error on {dest_path.name}: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"  Error processing {dest_path.name}: {e}")
        return False


def process_source(source_path, dest_base):
    """Process all PDFs in a source directory."""
    source = Path(source_path)
    source_name = source.name
    dest_root = dest_base / source_name
    
    if not source.exists():
        print(f"  WARNING: Source not found: {source_path}")
        return 0, 0
    
    print(f"\nProcessing: {source_path}")
    
    processed = 0
    errors = 0
    
    for pdf in source.rglob("*.pdf"):
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
        
        dest_file = dest_root / rel_path
        
        # Skip if destination exists and is newer
        if dest_file.exists() and dest_file.stat().st_mtime >= pdf.stat().st_mtime:
            processed += 1
            continue
        
        if embed_metadata_and_copy(pdf, dest_file, title, artist, album):
            processed += 1
        else:
            errors += 1
        
        # Progress every 100 files
        if processed % 100 == 0:
            print(f"  ... {processed} files processed")
    
    print(f"  Completed: {processed} files, {errors} errors")
    return processed, errors


def main():
    print("=" * 60)
    print("MobileSheets Prep with PDF Metadata Embedding")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    if not check_exiftool():
        sys.exit(1)
    
    print(f"\nDestination: {DEST_DIR}")
    DEST_DIR.mkdir(parents=True, exist_ok=True)
    
    total_processed = 0
    total_errors = 0
    
    for source_dir in SOURCE_DIRS:
        processed, errors = process_source(source_dir, DEST_DIR)
        total_processed += processed
        total_errors += errors
    
    print("\n" + "=" * 60)
    print(f"Total: {total_processed} files processed, {total_errors} errors")
    print(f"\nFiles are in: {DEST_DIR}")
    print("\nNEXT STEPS ON TABLET:")
    print("1. Open MobileSheets")
    print("2. Settings > Import Settings > Enable 'Extract PDF metadata'")
    print("3. Import > Google Drive > SheetMusicMobileSheets")
    print("4. Select files/folders and import")
    print("=" * 60)


if __name__ == "__main__":
    main()
