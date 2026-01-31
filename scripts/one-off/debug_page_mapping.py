"""
Debug the page mapping algorithm to see what it calculated.
"""

# TOC from previous parsing (sorted by page number)
toc_entries = [
    {"song": "Big Shot", "toc_page": 10},
    {"song": "Honesty", "toc_page": 19},
    {"song": "My Life", "toc_page": 25},
    {"song": "Zanzibar", "toc_page": 33},
    {"song": "Stiletto", "toc_page": 40},
    {"song": "Rosalinda's Eyes", "toc_page": 46},
    {"song": "Half A Mile Away", "toc_page": 52},
    {"song": "52nd Street", "toc_page": 60}
]

# First song found at PDF index 8
first_song_pdf_index = 8
first_song_toc_page = 10

print("TOC Analysis:")
print("=" * 60)
print(f"First song: {toc_entries[0]['song']}")
print(f"  TOC page: {first_song_toc_page}")
print(f"  Actual PDF index: {first_song_pdf_index}")
print(f"  Offset: {first_song_pdf_index - first_song_toc_page}")
print()

print("Song Length Calculations (from TOC page differences):")
print("-" * 60)

current_pdf_index = first_song_pdf_index

for i, entry in enumerate(toc_entries):
    if i < len(toc_entries) - 1:
        # Length = next song's TOC page - this song's TOC page
        song_length = toc_entries[i + 1]["toc_page"] - entry["toc_page"]
    else:
        song_length = None
    
    print(f"{entry['song']}:")
    print(f"  TOC page: {entry['toc_page']}")
    print(f"  Calculated PDF start: {current_pdf_index}")
    print(f"  Song length (from TOC): {song_length}")
    
    if song_length is not None:
        next_pdf_index = current_pdf_index + song_length
        print(f"  Next song would start at: {next_pdf_index}")
        current_pdf_index = next_pdf_index
    
    print()

print("=" * 60)
print("\nPROBLEM IDENTIFIED:")
print("The algorithm assumes TOC page numbers represent song lengths,")
print("but they actually represent the PRINTED page numbers in the book.")
print("\nThe correct approach:")
print("1. Find first song at actual PDF index (8)")
print("2. Calculate offset: 8 - 10 = -2")
print("3. Apply offset to ALL TOC page numbers:")
for entry in toc_entries:
    pdf_index = entry["toc_page"] - 2
    print(f"   {entry['song']}: TOC page {entry['toc_page']} -> PDF index {pdf_index}")
