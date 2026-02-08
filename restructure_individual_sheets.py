#!/usr/bin/env python3
"""
Restructure SheetMusicIndividualSheets folder.

For regular artists:
    FROM: Artist/Sheets/Artist - Song.pdf  OR  Artist/Album/Artist - Song.pdf
    TO:   Artist/Song.pdf  (flatten all into artist folder)

For Various Artists / _Broadway / _Movie:
    FROM: Various Artists/Various Artists - Songbook/Artist - Song.pdf
    TO:   Various Artists/Songbook/Artist - Song.pdf  (keep songbook structure)

Run with: py restructure_individual_sheets.py
"""

import os
import re
from pathlib import Path

# Configuration
ROOT_DIR = Path(r"G:\My Drive\SheetMusicMobileSheets\SheetMusicIndividualSheets")

# Special folders - keep songbook structure, just clean prefixes
KEEP_SONGBOOK_STRUCTURE = {
    "Various Artists",
    "_Broadway Shows",
    "_Movie and TV",
    "_Fake Books",
}


def clean_prefix(prefix, name):
    """Remove 'Prefix - ' from the beginning of a name."""
    pattern = rf"^{re.escape(prefix)}\s*-\s*"
    result = re.sub(pattern, "", name, flags=re.IGNORECASE)
    return result.strip() if result.strip() else name


def get_unique_filename(target_dir, filename):
    """Get a unique filename, adding (2), (3), etc. if needed."""
    target_path = target_dir / filename
    if not target_path.exists():
        return filename
    
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    counter = 2
    
    while True:
        new_filename = f"{stem} ({counter}){suffix}"
        new_path = target_dir / new_filename
        if not new_path.exists():
            return new_filename
        counter += 1
        if counter > 100:  # Safety limit
            raise Exception(f"Too many duplicates for {filename}")


def process_regular_artist(artist_path, stats):
    """Flatten all songs into Artist/Song.pdf format."""
    artist_name = artist_path.name
    
    # Collect all PDFs from all subdirectories
    all_pdfs = []
    for subdir in list(artist_path.iterdir()):
        if subdir.is_dir():
            for pdf in subdir.rglob("*.pdf"):
                all_pdfs.append(pdf)
    
    # Move each PDF to artist root with cleaned name
    for pdf in all_pdfs:
        stem = pdf.stem
        suffix = pdf.suffix
        
        # Remove artist prefix from filename
        new_stem = clean_prefix(artist_name, stem)
        new_filename = get_unique_filename(artist_path, new_stem + suffix)
        new_path = artist_path / new_filename
        
        try:
            pdf.rename(new_path)
            stats['files'] += 1
            if new_filename != new_stem + suffix:
                print(f"    MOVED (renamed for dup): {pdf.name} -> {new_filename}")
        except Exception as e:
            print(f"    ERROR moving {pdf.name}: {e}")
    
    # Remove empty subdirectories
    for subdir in list(artist_path.iterdir()):
        if subdir.is_dir():
            try:
                # Check if empty (only after moving files out)
                remaining = list(subdir.iterdir())
                if not remaining:
                    subdir.rmdir()
                    stats['folders_removed'] += 1
                    print(f"  REMOVED empty folder: {subdir.name}")
                else:
                    # Try to remove recursively if all subdirs are empty
                    remove_empty_dirs(subdir, stats)
            except Exception as e:
                print(f"  Could not remove {subdir.name}: {e}")


def remove_empty_dirs(path, stats):
    """Recursively remove empty directories."""
    if not path.is_dir():
        return
    
    for child in list(path.iterdir()):
        if child.is_dir():
            remove_empty_dirs(child, stats)
    
    # Check if now empty
    if not list(path.iterdir()):
        try:
            path.rmdir()
            stats['folders_removed'] += 1
            print(f"  REMOVED empty folder: {path.name}")
        except:
            pass


def process_various_artist(artist_path, stats):
    """Keep songbook structure, just clean folder and file prefixes."""
    artist_name = artist_path.name  # e.g., "Various Artists"
    
    for songbook_path in list(artist_path.iterdir()):
        if not songbook_path.is_dir():
            continue
        
        # Clean songbook folder name (remove "Various Artists - " prefix)
        new_songbook_name = clean_prefix(artist_name, songbook_path.name)
        
        if new_songbook_name != songbook_path.name:
            new_songbook_path = artist_path / new_songbook_name
            
            if new_songbook_path.exists():
                print(f"  SKIP (exists): {songbook_path.name}")
                continue
            
            try:
                songbook_path.rename(new_songbook_path)
                print(f"  FOLDER: {songbook_path.name} -> {new_songbook_name}")
                stats['folders'] += 1
                songbook_path = new_songbook_path
            except Exception as e:
                print(f"  ERROR renaming folder: {e}")
                continue
        
        # Clean song filenames - remove "Various Artists - " prefix only
        # Keep actual artist names like "Bob Dylan - Song.pdf"
        for song_file in list(songbook_path.iterdir()):
            if not song_file.is_file() or song_file.suffix.lower() != '.pdf':
                continue
            
            stem = song_file.stem
            suffix = song_file.suffix
            
            new_stem = clean_prefix(artist_name, stem)
            
            if new_stem != stem:
                new_song_path = songbook_path / (new_stem + suffix)
                
                if new_song_path.exists():
                    print(f"    SKIP (exists): {song_file.name}")
                    continue
                
                try:
                    song_file.rename(new_song_path)
                    stats['files'] += 1
                except Exception as e:
                    print(f"    ERROR: {e}")


def main():
    print("=" * 70)
    print("SheetMusicIndividualSheets Restructure")
    print(f"Root: {ROOT_DIR}")
    print("=" * 70)
    
    if not ROOT_DIR.exists():
        print(f"ERROR: Directory not found: {ROOT_DIR}")
        return
    
    stats = {'folders': 0, 'folders_removed': 0, 'files': 0}
    
    artists = sorted([p for p in ROOT_DIR.iterdir() if p.is_dir()])
    print(f"\nFound {len(artists)} artist folders\n")
    
    for i, artist_path in enumerate(artists, 1):
        print(f"[{i}/{len(artists)}] {artist_path.name}")
        
        if artist_path.name in KEEP_SONGBOOK_STRUCTURE:
            process_various_artist(artist_path, stats)
        else:
            process_regular_artist(artist_path, stats)
    
    print("\n" + "=" * 70)
    print(f"Done!")
    print(f"  Renamed {stats['folders']} folders")
    print(f"  Moved/renamed {stats['files']} files")
    print(f"  Removed {stats['folders_removed']} empty folders")
    print("=" * 70)


if __name__ == "__main__":
    main()
