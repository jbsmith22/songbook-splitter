#!/usr/bin/env python3
"""
Generate a human-readable summary of the normalization plan.
"""

import csv
from pathlib import Path
from collections import defaultdict

input_file = Path("normalization_plan_fixed.csv")

print("=" * 80)
print("NORMALIZATION PLAN SUMMARY")
print("=" * 80)
print()

# Read all entries
entries = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    entries = list(reader)

# Group by artist
by_artist = defaultdict(list)
for entry in entries:
    by_artist[entry['Artist']].append(entry)

# Statistics
total_pdfs = sum(1 for e in entries if e['Type'] == 'PDF')
total_folders = sum(1 for e in entries if e['Type'] == 'FOLDER')

print(f"Total renames: {len(entries)}")
print(f"  - PDFs: {total_pdfs}")
print(f"  - Folders: {total_folders}")
print(f"  - Artists affected: {len(by_artist)}")
print()

# Show examples by category
print("=" * 80)
print("EXAMPLE CHANGES BY CATEGORY")
print("=" * 80)
print()

# 1. Capitalization changes
print("1. CAPITALIZATION NORMALIZATION (Title Case)")
print("-" * 80)
cap_examples = [e for e in entries if e['Old_Name'].lower() == e['New_Name'].lower() and e['Old_Name'] != e['New_Name']][:5]
for e in cap_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

# 2. Bracket/Parentheses removal
print("2. BRACKET/PARENTHESES CONTENT PRESERVED")
print("-" * 80)
bracket_examples = [e for e in entries if '[' in e['Old_Name'] or '(' in e['Old_Name']][:5]
for e in bracket_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

# 3. Page info with underscores
print("3. PAGE INFO WITH UNDERSCORES")
print("-" * 80)
page_examples = [e for e in entries if 'page' in e['Old_Name'].lower()][:5]
for e in page_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

# 4. Ampersand replacement
print("4. AMPERSAND (&) REPLACED WITH 'AND'")
print("-" * 80)
amp_examples = [e for e in entries if '&' in e['Old_Name']][:5]
for e in amp_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

# 5. Duplicate handling
print("5. DUPLICATE NAME HANDLING (Numeric Suffixes)")
print("-" * 80)
dup_examples = [e for e in entries if e['New_Name'].endswith(' - 2')][:5]
for e in dup_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

# 6. Acronym preservation
print("6. ACRONYM PRESERVATION (PVG, SATB, etc.)")
print("-" * 80)
acronym_examples = [e for e in entries if any(acr in e['New_Name'] for acr in ['PVG', 'SATB', 'MTI', 'RSC'])][:5]
for e in acronym_examples:
    print(f"   {e['Type']:6} | {e['Artist']}")
    print(f"   Old: {e['Old_Name']}")
    print(f"   New: {e['New_Name']}")
    print()

print("=" * 80)
print("BREAKDOWN BY ARTIST (Top 10)")
print("=" * 80)
print()

# Sort artists by number of renames
sorted_artists = sorted(by_artist.items(), key=lambda x: len(x[1]), reverse=True)[:10]
for artist, artist_entries in sorted_artists:
    pdf_count = sum(1 for e in artist_entries if e['Type'] == 'PDF')
    folder_count = sum(1 for e in artist_entries if e['Type'] == 'FOLDER')
    print(f"{artist}: {len(artist_entries)} renames ({pdf_count} PDFs, {folder_count} folders)")

print()
print("=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("1. Review this summary")
print("2. Check normalization_plan_fixed.csv for full details")
print("3. Run execution script to perform the renames")
print()
