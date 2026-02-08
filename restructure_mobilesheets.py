#!/usr/bin/env python3
"""
Restructure MobileSheets ProcessedSongs folder.

For regular artists:
    FROM: Artist/Artist - Album/Artist - Song.pdf
    TO:   Artist/Album/Song.pdf

For Various Artists:
    FROM: Various Artists/Various Artists - Album/[Artist or Various Artists] - Song.pdf
    TO:   Various Artists/Album/[Artist - Song.pdf or Song.pdf]

Run with: py restructure_mobilesheets.py
"""

import os
import re
from pathlib import Path

# Configuration
ROOT_DIR = Path(r"G:\My Drive\SheetMusicMobileSheets\ProcessedSongs")

# Special folders where we DON'T remove artist prefix from songs
# (but we still remove the folder prefix from album names)
VARIOUS_ARTIST_FOLDERS = {
    "Various Artists",
    "_broadway Shows", 
    "_movie And Tv",
}


def clean_prefix(prefix, name):
    """Remove 'Prefix - ' from the beginning of a name."""
    # Match "Prefix - " or "Prefix- " at the start (case insensitive)
    pattern = rf"^{re.escape(prefix)}\s*-\s*"
    result = re.sub(pattern, "", name, flags=re.IGNORECASE)
    return result.strip() if result.strip() else name


def process_artist(artist_path, stats):
    """Process all albums and songs for one artist."""
    artist_name = artist_path.name
    is_various = artist_name in VARIOUS_ARTIST_FOLDERS
    
    for album_path in list(artist_path.iterdir()):
        if not album_path.is_dir():
            continue
        
        # === RENAME ALBUM FOLDER ===
        # Always remove artist prefix from album folder name
        new_album_name = clean_prefix(artist_name, album_path.name)
        
        if new_album_name != album_path.name:
            new_album_path = artist_path / new_album_name
            
            if new_album_path.exists():
                print(f"  SKIP (exists): {album_path.name}")
                continue
            
            try:
                album_path.rename(new_album_path)
                print(f"  FOLDER: {album_path.name} -> {new_album_name}")
                stats['folders'] += 1
                album_path = new_album_path
            except Exception as e:
                print(f"  ERROR renaming folder: {e}")
                continue
        
        # === RENAME SONG FILES ===
        for song_file in list(album_path.iterdir()):
            if not song_file.is_file():
                continue
            if song_file.suffix.lower() != '.pdf':
                continue
            
            stem = song_file.stem
            suffix = song_file.suffix
            
            if is_various:
                # For Various Artists folders, only remove "Various Artists - " prefix
                # Keep actual artist names like "Bob Dylan - Song.pdf"
                new_stem = clean_prefix("Various Artists", stem)
            else:
                # For regular artists, remove artist prefix
                new_stem = clean_prefix(artist_name, stem)
            
            if new_stem != stem:
                new_song_path = album_path / (new_stem + suffix)
                
                if new_song_path.exists():
                    print(f"    SKIP (exists): {song_file.name}")
                    continue
                
                try:
                    song_file.rename(new_song_path)
                    stats['files'] += 1
                except Exception as e:
                    print(f"    ERROR renaming file: {e}")


def main():
    print("=" * 70)
    print("MobileSheets Folder Restructure")
    print(f"Root: {ROOT_DIR}")
    print("=" * 70)
    
    if not ROOT_DIR.exists():
        print(f"ERROR: Directory not found: {ROOT_DIR}")
        return
    
    stats = {'folders': 0, 'files': 0}
    
    # Get list of artist folders
    artists = sorted([p for p in ROOT_DIR.iterdir() if p.is_dir()])
    print(f"\nFound {len(artists)} artist folders\n")
    
    for i, artist_path in enumerate(artists, 1):
        print(f"[{i}/{len(artists)}] {artist_path.name}")
        process_artist(artist_path, stats)
    
    print("\n" + "=" * 70)
    print(f"Done! Renamed {stats['folders']} folders and {stats['files']} files")
    print("=" * 70)


if __name__ == "__main__":
    main()
