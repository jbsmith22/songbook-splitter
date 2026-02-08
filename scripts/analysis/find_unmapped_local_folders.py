"""
Scan actual local folders to find matches for the 21 NO_MAPPING source PDFs
"""
import csv
from pathlib import Path
import re

def normalize_for_matching(text):
    """Normalize for case-insensitive matching"""
    return re.sub(r'[^a-z0-9]', '', text.lower())

print('Scanning local folders for unmapped source PDFs...\n')

# Read the updated mapping
rows = []
with open('data/analysis/provenance_verified_mapping_updated.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Get NO_MAPPING entries
no_mapping = [r for r in rows if r['status'] == 'NO_MAPPING']
print(f'Found {len(no_mapping)} NO_MAPPING source PDFs:\n')
for r in no_mapping:
    print(f'  {r["source_pdf"]}')

# Scan all local folders (both active and archive)
active_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')
archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')

all_local_folders = {}

# Scan active folders
if active_root.exists():
    for artist_dir in active_root.iterdir():
        if not artist_dir.is_dir():
            continue
        for songbook_dir in artist_dir.iterdir():
            if not songbook_dir.is_dir():
                continue
            relative_path = songbook_dir.relative_to(active_root).as_posix()
            all_local_folders[relative_path] = {
                'path': str(songbook_dir),
                'location': 'active'
            }

# Scan archive folders
if archive_root.exists():
    for artist_dir in archive_root.iterdir():
        if not artist_dir.is_dir():
            continue
        for songbook_dir in artist_dir.iterdir():
            if not songbook_dir.is_dir():
                continue
            relative_path = songbook_dir.relative_to(archive_root).as_posix()
            all_local_folders[relative_path] = {
                'path': str(songbook_dir),
                'location': 'archive'
            }

print(f'\nFound {len(all_local_folders)} total local folders\n')

# Try to match NO_MAPPING source PDFs to local folders
matches = []
for no_map_row in no_mapping:
    source_pdf = no_map_row['source_pdf']
    source_normalized = normalize_for_matching(source_pdf.replace('.pdf', ''))

    best_match = None
    best_score = 0

    for local_folder, folder_info in all_local_folders.items():
        local_normalized = normalize_for_matching(local_folder)

        # Calculate similarity score
        if source_normalized == local_normalized:
            score = 1.0
        elif source_normalized in local_normalized:
            score = len(source_normalized) / len(local_normalized)
        elif local_normalized in source_normalized:
            score = len(local_normalized) / len(source_normalized)
        else:
            # Count matching characters
            matches_chars = sum(1 for a, b in zip(source_normalized, local_normalized) if a == b)
            score = matches_chars / max(len(source_normalized), len(local_normalized))

        if score > best_score and score >= 0.8:  # High threshold for confidence
            best_score = score
            best_match = (local_folder, folder_info)

    if best_match:
        matches.append({
            'source_pdf': source_pdf,
            'local_folder': best_match[0],
            'location': best_match[1]['location'],
            'score': best_score
        })
        print(f'MATCH ({best_score:.2f}): {source_pdf}')
        print(f'     -> {best_match[0]} ({best_match[1]["location"]})')

print(f'\nFound {len(matches)} potential matches')

# Save matches for review
import json
with open('data/analysis/found_local_folders.json', 'w', encoding='utf-8') as f:
    json.dump({
        'matches': matches,
        'remaining_unmapped': len(no_mapping) - len(matches)
    }, f, indent=2)

print(f'\nMatches saved to: data/analysis/found_local_folders.json')
