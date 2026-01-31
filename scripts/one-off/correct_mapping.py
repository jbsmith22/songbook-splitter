"""
Build the correct mapping based on TOC and vision analysis.
"""
import json

# Load the page analysis
with open("page_analysis.json", "r") as f:
    page_data = json.load(f)

# CORRECT TOC entries from the image
toc_entries = [
    {"song": "Big Shot", "toc_page": 10},
    {"song": "Honesty", "toc_page": 19},
    {"song": "My Life", "toc_page": 25},
    {"song": "Zanzibar", "toc_page": 33},
    {"song": "Stiletto", "toc_page": 40},
    {"song": "Rosalinda's Eyes", "toc_page": 46},
    {"song": "Half A Mile Away", "toc_page": 52},
    {"song": "Until The Night", "toc_page": 60},  # CORRECTED
    {"song": "52nd Street", "toc_page": 68},      # CORRECTED
]

print("=" * 80)
print("CORRECT MAPPING: TOC → PDF INDEX")
print("=" * 80)
print()

# Filter valid song starts (exclude PDF 1 and 41)
valid_starts = []
for page in page_data:
    if page["is_song_start"] == "YES" and page["pdf_index"] not in [1, 41]:
        valid_starts.append(page)

print(f"{'TOC Song':<25} {'TOC Page':>8} → {'PDF Index':>10} {'Printed':>8} {'Offset':>8}")
print("-" * 80)

for toc in toc_entries:
    # Match by printed page number
    matched = None
    for start in valid_starts:
        if start["printed_page"] != "none":
            try:
                if int(start["printed_page"]) == toc["toc_page"]:
                    matched = start
                    break
            except:
                pass
    
    if matched:
        offset = matched["pdf_index"] - toc["toc_page"]
        print(f"{toc['song']:<25} {toc['toc_page']:>8} → {matched['pdf_index']:>10} {matched['printed_page']:>8} {offset:>8}")
    else:
        print(f"{toc['song']:<25} {toc['toc_page']:>8} → {'NOT FOUND':>10}")

print()
print("=" * 80)
print("ALGORITHM SHOULD FIND:")
print("=" * 80)
print()

for toc in toc_entries:
    for start in valid_starts:
        if start["printed_page"] != "none":
            try:
                if int(start["printed_page"]) == toc["toc_page"]:
                    print(f"'{toc['song']}' at PDF index {start['pdf_index']}")
                    break
            except:
                pass

print()
print("The current algorithm with vision should find all 9 songs correctly!")
print("The vision just needs to skip:")
print("  - PDF 1: Title page (no music)")
print("  - PDF 41: Lyrics within a song (not a song start)")
