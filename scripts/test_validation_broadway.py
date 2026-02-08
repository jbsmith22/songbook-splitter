#!/usr/bin/env python3
"""Quick test of vision validation on Broadway book."""

import json
import base64
import requests
from pathlib import Path

# Load artifacts
toc_data = json.load(open('temp_broadway_toc.json'))
page_analysis = json.load(open('temp_broadway_page_analysis.json'))

songs = page_analysis.get('songs', [])
print(f"Found {len(songs)} songs\n")

# Get first song
song = songs[0]
print(f"Testing Song 1: {song.get('title')}")
print(f"  PDF Pages: {song.get('start_pdf_page')}-{song.get('end_pdf_page')}")
print(f"  TOC Page: {song.get('toc_page')}")
print(f"  Match Method: {song.get('match_method')}")
print(f"  Confidence: {song.get('confidence')}")
print(f"  Verified: {song.get('verified')}\n")

# Find cached image for first page
start_page = song.get('start_pdf_page', song.get('actual_pdf_start'))
cache_dir = Path("S:/SlowImageCache/pdf_verification_v2/_Broadway Shows/A Treasury Of Gilbert And Sullivan Part 2")
page_image = cache_dir / f"page_{start_page-1:04d}.jpg"

if not page_image.exists():
    print(f"ERROR: Image not found: {page_image}")
    exit(1)

print(f"Found cached image: {page_image}\n")

# Load and encode image
with open(page_image, 'rb') as f:
    image_bytes = f.read()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')

# Call Ollama
print("Calling Ollama vision model...")
expected_title = song.get('title')
prompt = f"""Look at this sheet music page. What is the song title shown at the top?

Expected title: "{expected_title}"

Please respond with ONLY the exact title you see on the page, or "NO TITLE VISIBLE" if you cannot see a clear title."""

payload = {
    "model": "llama3.2-vision:11b",
    "prompt": prompt,
    "images": [image_base64],
    "stream": False
}

response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=60)
result = response.json()
actual_title = result.get('response', '').strip()

print(f"\nRESULTS:")
print(f"  Expected: {expected_title}")
print(f"  Actual:   {actual_title}")

# Check match
matches = expected_title.lower() in actual_title.lower() or actual_title.lower() in expected_title.lower()
status = 'PASS' if matches else 'FAIL'
print(f"  Match:    {status}")
