#!/usr/bin/env python3
"""
Debug script to see what Bedrock is actually saying about the missed PDFs.
"""

import json
import base64
from pathlib import Path
import boto3

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("S:/SlowImageCache/pdf_verification")
BEDROCK_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"
JPG_QUALITY = 90
RENDER_DPI = 300

def render_pdf_pages(pdf_path: Path) -> list:
    """Render PDF pages to JPG."""
    import fitz
    
    rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
    artist = rel_path.parts[0]
    book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
    
    cache_dir = CACHE_PATH / artist / book
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    rendered_pages = []
    doc = fitz.open(pdf_path)
    zoom = RENDER_DPI / 72
    mat = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(doc)):
        cache_file = cache_dir / f"{pdf_path.stem}_page_{page_num}.jpg"
        
        if not cache_file.exists():
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            pix.save(str(cache_file), "jpeg", jpg_quality=JPG_QUALITY)
        
        rendered_pages.append(cache_file)
    
    doc.close()
    return rendered_pages


def analyze_with_bedrock(image_path: Path, prompt: str):
    """Call Bedrock."""
    client = boto3.client('bedrock-runtime', region_name=BEDROCK_REGION)
    
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    response = client.invoke_model(
        modelId=BEDROCK_MODEL,
        body=json.dumps(request_body)
    )
    
    response_body = json.loads(response['body'].read())
    return response_body['content'][0]['text']


# Test the two missed PDFs
test_cases = [
    {
        "name": "Climb Ev'ry Mountain (single page, two songs)",
        "path": PROCESSED_SONGS_PATH / "_broadway Shows/Various Artists - The Ultimate Broadway Fakebook/Oscar Hammerstein - Climb Ev'ry Mountain.pdf",
        "pages_to_check": [0]  # Check page 1 (index 0)
    },
    {
        "name": "The Lion King - Under The Stars (splits on pages 2 and 3)",
        "path": PROCESSED_SONGS_PATH / "_broadway Shows/Various Artists - Lion King [score]/The Lion King - Under The Stars.pdf",
        "pages_to_check": [1, 2]  # Check pages 2 and 3 (indices 1 and 2)
    }
]

prompt = """Look at this sheet music page very carefully.

CRITICAL QUESTION: Does this page show the CLEAR BEGINNING of a COMPLETELY NEW AND DIFFERENT SONG?

To answer YES, you must see ALL of these:
1. A prominent song title that is DIFFERENT from the previous song
2. The very first measures/bars of that new song
3. Clear visual break indicating a new song starts here

Answer YES ONLY if you are ABSOLUTELY CERTAIN a new song starts on this page.
Answer NO if:
- This is just a continuation of the current song
- There are section markers, tempo changes, or other musical notation
- There is supplementary content (photos, text, discography)
- You see end bars or the song is finishing

Respond with ONLY "YES" or "NO" followed by a brief explanation (one sentence)."""

print("Debugging Bedrock Responses")
print("=" * 80)

for test in test_cases:
    print(f"\n{test['name']}")
    print(f"Path: {test['path'].name}")
    
    if not test['path'].exists():
        print("  ✗ File not found")
        continue
    
    pages = render_pdf_pages(test['path'])
    print(f"  Total pages: {len(pages)}")
    
    for page_idx in test['pages_to_check']:
        if page_idx >= len(pages):
            print(f"  ✗ Page {page_idx + 1} doesn't exist")
            continue
        
        print(f"\n  Analyzing page {page_idx + 1}...")
        response = analyze_with_bedrock(pages[page_idx], prompt)
        print(f"  Response: {response}")
        print(f"  Image: file:///{pages[page_idx]}")

print("\n" + "=" * 80)
