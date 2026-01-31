#!/usr/bin/env python3
"""Check book count and identify duplicates."""

import json
from collections import defaultdict

with open('complete_page_lineage.json', 'r') as f:
    data = json.load(f)

print(f"Total entries in JSON: {len(data['books'])}")
print()

# Group by artist and book name
artist_books = defaultdict(list)
for book in data['books']:
    key = (book['artist'], book['book_name'])
    artist_books[key].append(book)

print(f"Unique artist/book combinations: {len(artist_books)}")
print()

# Find duplicates
duplicates = {k: v for k, v in artist_books.items() if len(v) > 1}
if duplicates:
    print(f"Found {len(duplicates)} duplicate artist/book combinations:")
    for (artist, book_name), entries in sorted(duplicates.items())[:10]:
        print(f"\n  {artist} / {book_name} ({len(entries)} entries)")
        for entry in entries:
            print(f"    - {entry['book_dir']}")
            print(f"      Songs: {len(entry['extracted_songs'])}, Pages: {entry['total_pages']}")
