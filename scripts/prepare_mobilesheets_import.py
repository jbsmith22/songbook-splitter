#!/usr/bin/env python3
"""
Copy processed song PDFs to MobileSheets import structure with arrangement naming.
Format: SheetMusic_ForImport/<Artist>/<Book>/<Song Title>[ - <Arrangement>].pdf
"""

import json
import re
import shutil
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.utils.sanitization import sanitize_song_title

# Directories
ARTIFACTS_DIR = Path("SheetMusic_Artifacts")
OUTPUT_DIR = Path("SheetMusic_Output")
IMPORT_DIR = Path("SheetMusic_ForImport")

def detect_arrangement_type(book_name: str) -> str:
    """
    Detect arrangement type from book name.
    Returns arrangement suffix or empty string.
    """
    book_lower = book_name.lower()

    # Check for specific arrangement markers
    if "guitar tab" in book_lower or "_guitar tab_" in book_lower:
        return "Guitar Tab"
    if "piano solo" in book_lower or "_piano solo_" in book_lower:
        return "Piano Solo"
    if "_solo_" in book_lower and "piano" not in book_lower:
        return "Solo"
    if "vocal" in book_lower:
        return "Vocal"
    if "easy piano" in book_lower:
        return "Easy Piano"

    return ""

def normalize_title(title: str) -> str:
    """Normalize song title for comparison (case-insensitive, strip whitespace)."""
    return title.strip().upper()

def normalize_for_matching(text: str) -> str:
    """
    Normalize text for fuzzy filename matching.
    Removes all punctuation and special characters, converts to lowercase.
    """
    # Remove all non-alphanumeric characters except spaces
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    # Collapse multiple spaces and convert to lowercase
    normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
    return normalized

def collect_all_songs() -> Tuple[Dict, Dict]:
    """
    Collect all songs across all books and identify duplicates.
    Returns: (song_occurrences, book_songs)
    """
    # song_occurrences: normalized_title -> list of (artist, book, original_title, arrangement_type)
    song_occurrences = defaultdict(list)
    # book_songs: (artist, book) -> list of song entries
    book_songs = {}

    for artist_dir in ARTIFACTS_DIR.iterdir():
        if not artist_dir.is_dir():
            continue

        artist = artist_dir.name

        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue

            book = book_dir.name
            verified_path = book_dir / "verified_songs.json"

            if not verified_path.exists():
                continue

            # Load verified songs
            with open(verified_path, 'r', encoding='utf-8') as f:
                verified_data = json.load(f)

            # Load output files to get actual song-level artist
            output_path = book_dir / "output_files.json"
            song_artists = {}
            if output_path.exists():
                with open(output_path, 'r', encoding='utf-8') as f:
                    output_data = json.load(f)
                for output_file in output_data.get('output_files', []):
                    song_artists[output_file['song_title']] = output_file['artist']

            songs = verified_data.get('verified_songs', [])
            arrangement_type = detect_arrangement_type(book)

            # Track songs for this book
            book_songs[(artist, book)] = []

            for song in songs:
                title = song['song_title']
                normalized = normalize_title(title)
                # Get actual song artist from output_files.json, fallback to book artist
                song_artist = song_artists.get(title, artist)

                # Record occurrence
                song_occurrences[normalized].append({
                    'artist': artist,
                    'book': book,
                    'original_title': title,
                    'song_artist': song_artist,  # Add actual song artist
                    'arrangement': arrangement_type,
                    'start_page': song['start_page'],
                    'end_page': song['end_page']
                })

                # Track for this book
                book_songs[(artist, book)].append({
                    'title': title,
                    'normalized': normalized,
                    'song_artist': song_artist,
                    'arrangement': arrangement_type
                })

    return song_occurrences, book_songs

def assign_arrangement_names(song_occurrences: Dict, book_songs: Dict) -> Dict:
    """
    Assign arrangement suffixes to songs.
    Returns: (artist, book, original_title) -> {'filename': str, 'song_artist': str}
    """
    filename_map = {}

    # Process each unique song title
    for normalized_title, occurrences in song_occurrences.items():
        if len(occurrences) == 1:
            # Only one version - no suffix needed
            occ = occurrences[0]
            key = (occ['artist'], occ['book'], occ['original_title'])
            # Use sanitized title for filename (just song title, no artist prefix)
            sanitized_title = sanitize_song_title(occ['original_title'])
            filename_map[key] = {
                'filename': f"{sanitized_title}.pdf",
                'song_artist': occ['song_artist']
            }

        else:
            # Multiple versions - need to assign suffixes
            # Group by arrangement type
            by_arrangement = defaultdict(list)
            for occ in occurrences:
                arr_type = occ['arrangement'] if occ['arrangement'] else "Standard"
                by_arrangement[arr_type].append(occ)

            # Determine which version is "main" (can skip suffix)
            # Priority: Standard > Guitar Tab > Piano Solo > Solo > Others
            priority_order = ["Standard", "Guitar Tab", "Piano Solo", "Solo", "Easy Piano", "Vocal"]
            main_arrangement = None
            for arr_type in priority_order:
                if arr_type in by_arrangement:
                    main_arrangement = arr_type
                    break
            if main_arrangement is None:
                main_arrangement = list(by_arrangement.keys())[0]

            # Assign filenames
            arr_counter = {}
            for arr_type, arr_occurrences in by_arrangement.items():
                # Sort by (artist, book) to be consistent
                arr_occurrences.sort(key=lambda x: (x['artist'], x['book'], x['start_page']))

                for idx, occ in enumerate(arr_occurrences):
                    key = (occ['artist'], occ['book'], occ['original_title'])
                    sanitized_title = sanitize_song_title(occ['original_title'])

                    # First occurrence of main arrangement type - no suffix (main version)
                    if arr_type == main_arrangement and idx == 0:
                        filename = f"{sanitized_title}.pdf"

                    # Has arrangement type from book name
                    elif arr_type != "Standard":
                        # Check if there are multiple of this arrangement type
                        if len(arr_occurrences) > 1:
                            # Multiple versions of same arrangement - add counter
                            filename = f"{sanitized_title} - {arr_type} {idx + 1}.pdf"
                        else:
                            filename = f"{sanitized_title} - {arr_type}.pdf"

                    # Additional standard arrangements (not the first/main one)
                    else:
                        # Start counter at 2 for additional versions
                        if arr_type not in arr_counter:
                            arr_counter[arr_type] = 2
                        else:
                            arr_counter[arr_type] += 1
                        filename = f"{sanitized_title} - Arr {arr_counter[arr_type]}.pdf"

                    filename_map[key] = {
                        'filename': filename,
                        'song_artist': occ['song_artist']
                    }

    return filename_map

def copy_songs_to_import_structure(filename_map: Dict) -> None:
    """Copy songs to import structure with proper filenames."""

    IMPORT_DIR.mkdir(exist_ok=True)

    total_files = 0
    total_artists = set()
    total_books = 0
    renamed_count = 0

    current_book_key = None

    for (artist, book, original_title), file_info in sorted(filename_map.items()):
        target_filename = file_info['filename']
        song_artist = file_info['song_artist']

        # Track progress
        book_key = (artist, book)
        if book_key != current_book_key:
            total_books += 1
            current_book_key = book_key
            total_artists.add(artist)

        # Source file (with sanitized naming - title-cased and special characters replaced)
        # Use sanitize_song_title which includes title-casing (how actual files were created)
        # Use song_artist (not book artist) for Various Artists books
        sanitized_title = sanitize_song_title(original_title)
        source_file = OUTPUT_DIR / artist / book / f"{song_artist} - {sanitized_title}.pdf"

        # Check if source exists with exact case
        if not source_file.exists():
            # Try case-insensitive match
            book_dir = OUTPUT_DIR / artist / book
            if book_dir.exists():
                expected_name_lower = f"{song_artist} - {sanitized_title}.pdf".lower()
                found = False
                for pdf_file in book_dir.glob("*.pdf"):
                    if pdf_file.name.lower() == expected_name_lower:
                        source_file = pdf_file
                        found = True
                        break

                # If still not found, try legacy naming (without trailing period removal)
                # Some older files have titles ending in . which results in ..pdf
                if not found and original_title.endswith('.'):
                    legacy_sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F\x7F]', '-', original_title)
                    expected_legacy_lower = f"{song_artist} - {legacy_sanitized}.pdf".lower()
                    for pdf_file in book_dir.glob("*.pdf"):
                        if pdf_file.name.lower() == expected_legacy_lower:
                            source_file = pdf_file
                            found = True
                            break

                # If still not found, try fuzzy matching (removes all punctuation)
                # This handles various historical sanitization inconsistencies
                if not found:
                    expected_normalized = normalize_for_matching(f"{song_artist} - {original_title}")
                    for pdf_file in book_dir.glob("*.pdf"):
                        file_normalized = normalize_for_matching(pdf_file.stem)  # stem = filename without .pdf
                        if file_normalized == expected_normalized:
                            source_file = pdf_file
                            found = True
                            break

                if not found:
                    print(f"  WARNING: Missing source file: {song_artist} - {original_title}.pdf")
                    continue
            else:
                print(f"  WARNING: Missing source file: {source_file.name}")
                continue

        # Target directory and file
        target_dir = IMPORT_DIR / artist / book
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / target_filename

        # Copy file
        shutil.copy2(source_file, target_file)
        total_files += 1

        # Track if renamed
        if source_file.name != target_filename:
            renamed_count += 1

    print(f"\n{'='*80}")
    print(f"COPY COMPLETE")
    print(f"{'='*80}")
    print(f"  Artists: {len(total_artists)}")
    print(f"  Books:   {total_books}")
    print(f"  Songs:   {total_files}")
    print(f"  Renamed: {renamed_count} (arrangement suffixes added)")
    print(f"\nImport folder ready at: {IMPORT_DIR.absolute()}")

def main():
    """Main entry point."""

    if not ARTIFACTS_DIR.exists():
        print(f"Error: {ARTIFACTS_DIR} does not exist")
        return

    if not OUTPUT_DIR.exists():
        print(f"Error: {OUTPUT_DIR} does not exist")
        return

    print("Step 1: Collecting all songs across books...")
    song_occurrences, book_songs = collect_all_songs()

    total_unique = len(song_occurrences)
    duplicates = sum(1 for occs in song_occurrences.values() if len(occs) > 1)
    print(f"  Found {total_unique} unique song titles")
    print(f"  {duplicates} titles appear in multiple versions")

    print("\nStep 2: Assigning arrangement names...")
    filename_map = assign_arrangement_names(song_occurrences, book_songs)

    print(f"  Generated {len(filename_map)} filename mappings")

    print("\nStep 3: Copying songs to import structure...")
    copy_songs_to_import_structure(filename_map)

if __name__ == "__main__":
    main()
