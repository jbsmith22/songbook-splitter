#!/usr/bin/env python3
"""Compare SheetMusic source books vs TOC cache entries."""

import json
from pathlib import Path
from collections import defaultdict

# Count actual source books in SheetMusic (recursively)
SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")
source_books = []

print("Scanning SheetMusic folder (recursively)...")
for pdf_file in SHEET_MUSIC_PATH.rglob("*.pdf"):
    # Get artist from parent directory structure
    relative = pdf_file.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        book = pdf_file.stem
        source_books.append({
            'artist': artist,
            'book': book,
            'path': str(pdf_file)
        })

print(f"Source books in SheetMusic: {len(source_books)}")
print()

# Count TOC cache entries
TOC_CACHE_DIR = Path("toc_cache")
toc_entries = []

print("Scanning TOC cache...")
for toc_file in TOC_CACHE_DIR.glob("*.json"):
    try:
        with open(toc_file, 'r') as f:
            data = json.load(f)
        
        output = data.get('output', {})
        if output and 'output_files' in output and output['output_files']:
            first_file = output['output_files'][0]
            artist = first_file.get('artist', 'Unknown')
            output_uri = first_file.get('output_uri', '')
            
            if output_uri:
                parts = output_uri.replace('s3://jsmith-output/', '').split('/')
                if len(parts) >= 2:
                    book_name = parts[1]
                    toc_entries.append({
                        'artist': artist,
                        'book': book_name,
                        'toc_file': toc_file.name,
                        'songs': len(output['output_files'])
                    })
    except:
        pass

print(f"TOC cache entries: {len(toc_entries)}")
print()

# Deduplicate TOC entries
toc_map = defaultdict(list)
for entry in toc_entries:
    key = (entry['artist'], entry['book'])
    toc_map[key].append(entry)

print(f"Unique TOC entries (after dedup): {len(toc_map)}")
print()

# Show duplicates
duplicates = {k: v for k, v in toc_map.items() if len(v) > 1}
if duplicates:
    print(f"TOC duplicates found: {len(duplicates)}")
    for (artist, book), entries in sorted(duplicates.items())[:5]:
        print(f"  {artist} / {book}: {len(entries)} entries")
    print()

# Compare: find TOC entries not in source
source_set = {(b['artist'], b['book']) for b in source_books}
toc_set = set(toc_map.keys())

print("=" * 80)
print("COMPARISON")
print("=" * 80)
print(f"Source books (SheetMusic): {len(source_set)}")
print(f"TOC cache unique books: {len(toc_set)}")
print(f"TOC entries NOT in source: {len(toc_set - source_set)}")
print(f"Source books NOT in TOC: {len(source_set - toc_set)}")
print()

# Show some examples of TOC entries not in source
if toc_set - source_set:
    print("Sample TOC entries NOT in SheetMusic (first 10):")
    for artist, book in sorted(toc_set - source_set)[:10]:
        print(f"  {artist} / {book}")
