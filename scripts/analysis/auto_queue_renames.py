"""
Automatically queue rename actions for all files that need sheet artist to folder artist normalization
This script analyzes the match quality data and creates rename decisions for files that have
detailed sheet music attributions that should be collapsed to the folder-level artist.
"""
import json
import re
from datetime import datetime

def extract_folder_artist(folder_path):
    """Extract the top-level artist from folder path"""
    parts = folder_path.split('/')
    return parts[0]

def normalize_filename(filename, folder_artist):
    """
    Normalize filename to <artist> - <songname> format
    Removes detailed sheet music attributions
    """
    # Remove .pdf extension
    name = re.sub(r'\.pdf$', '', filename, flags=re.IGNORECASE)

    # Split by ' - ' to get parts
    parts = name.split(' - ')

    if len(parts) < 2:
        # No artist-song separation, return as-is
        return filename

    # Get the first part (current artist) and last part (song name)
    first_part = parts[0].strip()
    song_name = parts[-1].strip()

    # Check if the first part matches the folder artist (case insensitive)
    if first_part.lower() == folder_artist.lower():
        # Artist matches, check if there are extra attribution parts
        if len(parts) > 2:
            # Has extra attribution parts like "Malcolm Young - Brian Johnson"
            # Collapse to just folder artist and song name
            return f"{folder_artist} - {song_name}.pdf"
        else:
            # Already correct format
            return filename
    else:
        # First part doesn't match folder artist
        # Replace it with folder artist
        return f"{folder_artist} - {song_name}.pdf"

def needs_rename(filename, folder_artist):
    """Check if a filename needs normalization"""
    normalized = normalize_filename(filename, folder_artist)
    return normalized != filename

def main():
    print("=== Auto-Queueing Rename Actions ===\n")

    # Load match quality data
    print("Loading match_quality_data.json...")
    with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Prepare decisions structure
    decisions = {}

    total_folders = 0
    total_local_renames = 0
    total_s3_renames = 0

    # Process each quality tier
    for tier_name, folders in data['quality_tiers'].items():
        for folder in folders:
            local_path = folder['local_path']
            s3_path = folder['s3_path']
            book_id = folder['book_id']

            # Skip Various Artists, Broadway Shows, and Movie/TV folders
            if (local_path.startswith('Various Artists/') or
                local_path.startswith('_broadway Shows/') or
                local_path.startswith('_movie And Tv/')):
                continue

            folder_artist = extract_folder_artist(local_path)
            fc = folder.get('file_comparison', {})

            local_renames = 0
            s3_renames = 0

            # Process local-only files
            for item in fc.get('local_only_files', []):
                filename = item['filename'] if isinstance(item, dict) else item
                if needs_rename(filename, folder_artist):
                    normalized = normalize_filename(filename, folder_artist)

                    if local_path not in decisions:
                        decisions[local_path] = {'fileDecisions': {}}

                    decisions[local_path]['fileDecisions'][filename] = {
                        'action': 'rename-local',
                        'status': 'rename',
                        'filepath': filename,
                        'normalized_name': normalized,
                        'local_path': local_path,
                        's3_path': s3_path,
                        'book_id': book_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    local_renames += 1

            # Process S3-only files
            for item in fc.get('s3_only_files', []):
                filename = item['filename'] if isinstance(item, dict) else item
                if needs_rename(filename, folder_artist):
                    normalized = normalize_filename(filename, folder_artist)

                    if local_path not in decisions:
                        decisions[local_path] = {'fileDecisions': {}}

                    decisions[local_path]['fileDecisions'][filename] = {
                        'action': 'rename-s3',
                        'status': 'rename',
                        'filepath': filename,
                        'normalized_name': normalized,
                        'local_path': local_path,
                        's3_path': s3_path,
                        'book_id': book_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    s3_renames += 1

            # Process hash mismatches (both local and S3)
            for item in fc.get('hash_mismatches', []):
                filename = item['filename']

                # Check local
                if needs_rename(filename, folder_artist):
                    normalized = normalize_filename(filename, folder_artist)

                    if local_path not in decisions:
                        decisions[local_path] = {'fileDecisions': {}}

                    # Use a unique key for local rename
                    key = f"{filename}__LOCAL"
                    decisions[local_path]['fileDecisions'][key] = {
                        'action': 'rename-local',
                        'status': 'rename',
                        'filepath': filename,
                        'normalized_name': normalized,
                        'local_path': local_path,
                        's3_path': s3_path,
                        'book_id': book_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    local_renames += 1

                # Check S3
                if needs_rename(filename, folder_artist):
                    normalized = normalize_filename(filename, folder_artist)

                    if local_path not in decisions:
                        decisions[local_path] = {'fileDecisions': {}}

                    # Use a unique key for S3 rename
                    key = f"{filename}__S3"
                    decisions[local_path]['fileDecisions'][key] = {
                        'action': 'rename-s3',
                        'status': 'rename',
                        'filepath': filename,
                        'normalized_name': normalized,
                        'local_path': local_path,
                        's3_path': s3_path,
                        'book_id': book_id,
                        'timestamp': datetime.now().isoformat()
                    }
                    s3_renames += 1

            if local_renames > 0 or s3_renames > 0:
                total_folders += 1
                total_local_renames += local_renames
                total_s3_renames += s3_renames
                print(f"  {local_path}: {local_renames} local, {s3_renames} S3")

    # Save decisions
    output_file = 'data/analysis/auto_rename_decisions.json'
    print(f"\nSaving decisions to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(decisions, f, indent=2)

    print("\n=== Summary ===")
    print(f"Folders with renames: {total_folders}")
    print(f"Total local renames: {total_local_renames}")
    print(f"Total S3 renames: {total_s3_renames}")
    print(f"Total renames: {total_local_renames + total_s3_renames}")
    print(f"\nDecisions saved to: {output_file}")
    print("\nYou can import this file in the web viewer or use it to script the actual rename operations.")

if __name__ == '__main__':
    main()
