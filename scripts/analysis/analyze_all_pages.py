"""
Analyze every PNG to extract page numbers and identify song starts.
"""
import boto3
import json
import base64
from pathlib import Path
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')
rendered_dir = Path("rendered_pages")

print("Analyzing all 59 pages...")
print("=" * 80)

page_data = []

for i in range(59):
    png_path = rendered_dir / f"page_{i:03d}.png"
    
    with open(png_path, 'rb') as f:
        img_bytes = f.read()
    
    img = Image.open(io.BytesIO(img_bytes))
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Ask for page number and if it's a song start
    prompt = """Look at this sheet music page.

1. What is the PRINTED PAGE NUMBER on this page? (Look at bottom of page)
2. Is this the FIRST PAGE of a song? (Has a song title at the top)
3. If it's a song start, what is the SONG TITLE?

Respond in this exact format:
PAGE_NUMBER: [number or "none"]
SONG_START: [YES or NO]
SONG_TITLE: [title or "none"]"""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "temperature": 0.0
    }
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text'].strip()
        
        # Parse response
        lines = answer.split('\n')
        page_num = "?"
        is_start = "?"
        title = "?"
        
        for line in lines:
            if line.startswith("PAGE_NUMBER:"):
                page_num = line.split(":", 1)[1].strip()
            elif line.startswith("SONG_START:"):
                is_start = line.split(":", 1)[1].strip()
            elif line.startswith("SONG_TITLE:"):
                title = line.split(":", 1)[1].strip()
        
        page_data.append({
            "pdf_index": i,
            "printed_page": page_num,
            "is_song_start": is_start,
            "song_title": title
        })
        
        marker = "🎵" if is_start == "YES" else "  "
        print(f"{marker} PDF {i:3d} | Printed: {page_num:>4s} | Start: {is_start:3s} | Title: {title}")
        
    except Exception as e:
        print(f"   PDF {i:3d} | ERROR: {e}")
        page_data.append({
            "pdf_index": i,
            "printed_page": "ERROR",
            "is_song_start": "ERROR",
            "song_title": "ERROR"
        })
    
    if (i + 1) % 10 == 0:
        print(f"--- Processed {i + 1}/59 pages ---")

print("=" * 80)

# Save results
import json
with open("page_analysis.json", "w") as f:
    json.dump(page_data, f, indent=2)

print("\nResults saved to page_analysis.json")

# Print summary of song starts
print("\nSong Starts Found:")
print("-" * 80)
for data in page_data:
    if data["is_song_start"] == "YES":
        print(f"PDF Index {data['pdf_index']:3d} | Printed Page {data['printed_page']:>4s} | {data['song_title']}")
