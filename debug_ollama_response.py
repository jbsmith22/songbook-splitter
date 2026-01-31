#!/usr/bin/env python3
"""
Debug script to see what Ollama is actually returning.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from verify_pdf_splits import OllamaVisionClient, PDFRenderer, PROCESSED_SONGS_PATH

# Initialize
ollama = OllamaVisionClient()
renderer = PDFRenderer()

# Find a sample PDF
pdfs = list(PROCESSED_SONGS_PATH.rglob("*.pdf"))
sample_pdf = pdfs[0]

print(f"Testing with: {sample_pdf.name}")
print("=" * 80)

# Render first page
print("\nRendering first page...")
image_path = renderer.render_page(sample_pdf, 0)
print(f"Rendered to: {image_path}")

# Test Ollama
print("\nCalling Ollama...")
prompt = """Look at this sheet music page. Answer these questions concisely:
1. Is there a song title visible at the top? (YES/NO)
2. What is the song title? (write the title or "NONE")
3. Does this look like the first page of a song? (YES/NO)
4. Are there any signs this is a continuation page? (YES/NO)

Format your answer as:
TITLE: YES/NO
TITLE_TEXT: [title or NONE]
FIRST_PAGE: YES/NO
CONTINUATION: YES/NO"""

response = ollama.analyze_image(image_path, prompt)

print("\n" + "=" * 80)
print("RAW OLLAMA RESPONSE:")
print("=" * 80)
print(response)
print("=" * 80)

if 'response' in response:
    print("\nEXTRACTED TEXT:")
    print("=" * 80)
    print(response['response'])
    print("=" * 80)
