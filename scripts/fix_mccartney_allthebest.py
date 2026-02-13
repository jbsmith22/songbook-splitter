"""Apply corrected splits for Paul McCartney / All The Best from manual export."""
import json
import os
import sys
import subprocess
from pypdf import PdfReader, PdfWriter

DRY_RUN = "--dry-run" in sys.argv

ARTIST = "Paul McCartney"
BOOK = "All The Best"
BASE = r"d:\Work\songbook-splitter"
SOURCE_PDF = os.path.join(BASE, "SheetMusic_Input", ARTIST, f"{ARTIST} - {BOOK}.pdf")
OUTPUT_DIR = os.path.join(BASE, "SheetMusic_Output", ARTIST, BOOK)
ARTIFACT_DIR = os.path.join(BASE, "SheetMusic_Artifacts", ARTIST, BOOK)
EXPORT_FILE = os.path.join(BASE, "v3_splits_594e8e0eb2c37bd0 (10).json")

S3_OUTPUT_PREFIX = f"s3://jsmith-output/v3/Paul Mccartney/{BOOK}"
S3_ARTIFACT_PREFIX = f"s3://jsmith-artifacts/v3/{ARTIST}/{BOOK}"

# Load corrected data
with open(EXPORT_FILE) as f:
    export = json.load(f)

new_verified = export["verified_songs"]
new_page_mapping = export["page_mapping"]

# Load current data
with open(os.path.join(ARTIFACT_DIR, "verified_songs.json")) as f:
    old_data = json.load(f)
book_id = old_data["book_id"]

with open(os.path.join(ARTIFACT_DIR, "output_files.json")) as f:
    old_output = json.load(f)

# Build lookup of old songs by title+range for comparison
old_songs = {}
for s in old_data["verified_songs"]:
    key = (s["song_title"], s["start_page"], s["end_page"])
    old_songs[key] = s

old_output_by_title = {}
for o in old_output["output_files"]:
    old_output_by_title[o["song_title"]] = o

# Determine which songs changed
changed = []
unchanged = []
for s in new_verified:
    key = (s["song_title"], s["start_page"], s["end_page"])
    if key in old_songs:
        unchanged.append(s)
    else:
        changed.append(s)

# Songs removed (in old but not in new by title)
new_titles = {s["song_title"] for s in new_verified}
removed = [s for s in old_data["verified_songs"] if s["song_title"] not in new_titles]

print(f"Book: {ARTIST} / {BOOK}")
print(f"Old songs: {len(old_data['verified_songs'])}")
print(f"New songs: {len(new_verified)}")
print(f"Unchanged: {len(unchanged)}")
print(f"Changed: {len(changed)}")
print(f"Removed: {len(removed)}")
print()

for s in changed:
    print(f"  RE-EXTRACT: {s['song_title']} (pages {s['start_page']}-{s['end_page']})")
for s in removed:
    print(f"  DELETE: {s['song_title']} (pages {s['start_page']}-{s['end_page']})")

if DRY_RUN:
    print("\n[DRY RUN] No changes made.")
    sys.exit(0)

print("\n--- Applying changes ---")

# Read source PDF
reader = PdfReader(SOURCE_PDF)
print(f"Source PDF: {len(reader.pages)} pages")

# Build new output_files
new_output_files = []
for s in new_verified:
    title = s["song_title"]
    start = s["start_page"]
    end = s["end_page"]

    # Generate filename (Title Case)
    safe_title = title.title().replace("/", "-").replace("?", "-").replace("'", "'")
    filename = f"Paul Mccartney - {safe_title}.pdf"
    output_path = os.path.join(OUTPUT_DIR, filename)
    s3_uri = f"{S3_OUTPUT_PREFIX}/{filename}"

    key = (title, start, end)
    if key in old_songs and title in old_output_by_title:
        # Unchanged - keep existing output info
        old_o = old_output_by_title[title]
        new_output_files.append({
            "song_title": title,
            "artist": ARTIST,
            "output_uri": old_o["output_uri"],
            "file_size_bytes": old_o["file_size_bytes"],
            "page_range": [start, end]
        })
        print(f"  KEEP: {title}")
    else:
        # Changed - re-extract
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        with open(output_path, "wb") as f:
            writer.write(f)
        size = os.path.getsize(output_path)

        new_output_files.append({
            "song_title": title,
            "artist": ARTIST,
            "output_uri": s3_uri,
            "file_size_bytes": size,
            "page_range": [start, end]
        })
        print(f"  EXTRACTED: {title} -> {size:,} bytes ({end-start} pages)")

        # Upload to S3
        subprocess.run(["aws", "s3", "cp", output_path, s3_uri], check=True)

# Delete removed songs from S3 and local
for s in removed:
    title = s["song_title"]
    if title in old_output_by_title:
        old_uri = old_output_by_title[title]["output_uri"]
        print(f"  S3 DELETE: {old_uri}")
        subprocess.run(["aws", "s3", "rm", old_uri], check=True)

        # Try local delete
        safe_title = title.title().replace("/", "-").replace("?", "-").replace("'", "'")
        local_path = os.path.join(OUTPUT_DIR, f"Paul Mccartney - {safe_title}.pdf")
        if os.path.exists(local_path):
            os.remove(local_path)
            print(f"  LOCAL DELETE: {local_path}")

# Also delete old files for changed songs that had different S3 URIs
for s in changed:
    title = s["song_title"]
    if title in old_output_by_title:
        old_uri = old_output_by_title[title]["output_uri"]
        new_safe = title.title().replace("/", "-").replace("?", "-").replace("'", "'")
        new_uri = f"{S3_OUTPUT_PREFIX}/Paul Mccartney - {new_safe}.pdf"
        if old_uri != new_uri:
            print(f"  S3 DELETE OLD: {old_uri}")
            subprocess.run(["aws", "s3", "rm", old_uri])

# Write updated artifacts
verified_out = {"book_id": book_id, "verified_songs": new_verified}
with open(os.path.join(ARTIFACT_DIR, "verified_songs.json"), "w") as f:
    json.dump(verified_out, f, indent=2)
print("Updated verified_songs.json")

# Strip 'source' from verified_songs for clean output
clean_verified = []
for s in new_verified:
    clean = {k: v for k, v in s.items() if k != "source"}
    clean_verified.append(clean)
verified_out = {"book_id": book_id, "verified_songs": clean_verified}
with open(os.path.join(ARTIFACT_DIR, "verified_songs.json"), "w") as f:
    json.dump(verified_out, f, indent=2)

output_out = {"book_id": book_id, "output_files": new_output_files}
with open(os.path.join(ARTIFACT_DIR, "output_files.json"), "w") as f:
    json.dump(output_out, f, indent=2)
print("Updated output_files.json")

pm_out = {"book_id": book_id, **{k: v for k, v in new_page_mapping.items() if k != "book_id"}}
with open(os.path.join(ARTIFACT_DIR, "page_mapping.json"), "w") as f:
    json.dump(pm_out, f, indent=2)
print("Updated page_mapping.json")

# Upload artifacts to S3
for artifact in ["verified_songs.json", "output_files.json", "page_mapping.json"]:
    local = os.path.join(ARTIFACT_DIR, artifact)
    s3 = f"{S3_ARTIFACT_PREFIX}/{artifact}"
    subprocess.run(["aws", "s3", "cp", local, s3], check=True)
print("Uploaded artifacts to S3")

print(f"\nDone! {len(new_verified)} songs, {len(changed)} re-extracted, {len(removed)} deleted.")
