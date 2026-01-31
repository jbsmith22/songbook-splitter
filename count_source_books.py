#!/usr/bin/env python3
"""Count source books in SheetMusic folder."""

from pathlib import Path

SHEET_MUSIC_PATH = Path("c:/Work/AWSMusic/SheetMusic")

# Count PDF files
pdf_files = list(SHEET_MUSIC_PATH.rglob("*.pdf"))

print(f"Total PDF files in SheetMusic: {len(pdf_files)}")
print()

# Group by artist
from collections import defaultdict
by_artist = defaultdict(list)

for pdf in pdf_files:
    # Get artist from path structure
    relative = pdf.relative_to(SHEET_MUSIC_PATH)
    if len(relative.parts) >= 2:
        artist = relative.parts[0]
        by_artist[artist].append(pdf.name)

print(f"Artists: {len(by_artist)}")
print()
print("Sample artists and book counts:")
for artist, books in sorted(by_artist.items(), key=lambda x: -len(x[1]))[:10]:
    print(f"  {artist}: {len(books)} books")
