"""
Verify the correct mapping based on user corrections.
"""
import json

# Load the page analysis
with open("page_analysis.json", "r") as f:
    page_data = json.load(f)

# TOC entries from the user (9 songs)
toc_entries = [
    {"song": "Big Shot", "toc_page": 10},
    {"song": "Honesty", "toc_page": 19},
    {"song": "My Life", "toc_page": 25},
    {"song": "Zanzibar", "toc_page": 33},
    {"song": "Stiletto", "toc_page": 40},
    {"song": "Rosalinda's Eyes", "toc_page": 46},
    {"song": "Half A Mile Away", "toc_page": 52},
    {"song": "52nd Street", "toc_page": 60},
    {"song": "Until the Night", "toc_page": 68},
]

print("=" * 80)
print("CORRECTED SONG MAPPING")
print("=" * 80)
print()

# Filter out false positives:
# - PDF index 1: Title page (52nd Street) - NOT a song start
# - PDF index 41: "Lit - tle Ge - o" - NOT a song start (lyrics within a song)
# - PDF index 55: "52nd Street" - This is the ACTUAL song start for 52nd Street

valid_song_starts = []
for page in page_data:
    if page["is_song_start"] == "YES":
        pdf_idx = page["pdf_index"]
        title = page["song_title"]
        
        # Skip false positives
        if pdf_idx == 1:
            print(f"❌ SKIPPING PDF {pdf_idx}: '{title}' - Title page, not a song")
            continue
        if pdf_idx == 41:
            print(f"❌ SKIPPING PDF {pdf_idx}: '{title}' - Lyrics within a song, not a song start")
            continue
        
        valid_song_starts.append(page)
        print(f"✓ PDF {pdf_idx:3d}: '{title}' (printed page {page['printed_page']})")

print()
print("=" * 80)
print("CORRECT MAPPING: TOC → PDF INDEX")
print("=" * 80)
print()

# Now match TOC entries with valid song starts
print(f"{'TOC Song':<25} {'TOC Page':>8} → {'PDF Index':>10} {'Printed':>8} {'Offset':>8}")
print("-" * 80)

for toc in toc_entries:
    matched = None
    
    # Match by printed page number first (most reliable)
    for start in valid_song_starts:
        if start["printed_page"] != "none":
            try:
                if int(start["printed_page"]) == toc["toc_page"]:
                    matched = start
                    break
            except:
                pass
    
    # If no match by page number, try by title
    if not matched:
        for start in valid_song_starts:
            title_upper = start["song_title"].upper()
            song_upper = toc["song"].upper()
            
            # Check for title match
            if song_upper in title_upper or title_upper in song_upper:
                matched = start
                break
    
    if matched:
        offset = matched["pdf_index"] - toc["toc_page"]
        print(f"{toc['song']:<25} {toc['toc_page']:>8} → {matched['pdf_index']:>10} {matched['printed_page']:>8} {offset:>8}")
    else:
        print(f"{toc['song']:<25} {toc['toc_page']:>8} → {'NOT FOUND':>10}")

print()
print("=" * 80)
print("VERIFICATION")
print("=" * 80)
print()
print(f"TOC entries: {len(toc_entries)}")
print(f"Valid song starts detected: {len(valid_song_starts)}")
print()

if len(valid_song_starts) == len(toc_entries):
    print("✓ All 9 songs detected correctly!")
else:
    print(f"⚠ Mismatch: Expected {len(toc_entries)} songs, found {len(valid_song_starts)}")
