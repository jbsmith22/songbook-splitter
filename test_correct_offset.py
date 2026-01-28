"""
Test with CORRECT offset: -8
Big Shot at PDF index 2, TOC page 10
"""
import boto3
import json
import base64
from pathlib import Path
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')
rendered_dir = Path("rendered_pages")

# CORRECT offset from user
OFFSET = -8

TOC_ENTRIES = [
    {"song": "Big Shot", "toc_page": 10},
    {"song": "Honesty", "toc_page": 19},
    {"song": "My Life", "toc_page": 25},
    {"song": "Zanzibar", "toc_page": 33},
    {"song": "Stiletto", "toc_page": 40},
    {"song": "Rosalinda's Eyes", "toc_page": 46},
    {"song": "Half A Mile Away", "toc_page": 52},
    {"song": "52nd Street", "toc_page": 60},
    {"song": "Until the Night", "toc_page": 68}
]

print("Testing with CORRECT offset: -8")
print("Big Shot: TOC page 10 -> PDF index 2")
print("=" * 60)

for entry in TOC_ENTRIES:
    pdf_index = entry["toc_page"] + OFFSET
    
    if pdf_index < 0 or pdf_index >= 59:
        print(f"❌ {entry['song']:20s} TOC {entry['toc_page']:3d} -> index {pdf_index:3d}: OUT OF RANGE")
        continue
    
    png_path = rendered_dir / f"page_{pdf_index:03d}.png"
    
    with open(png_path, 'rb') as f:
        img_bytes = f.read()
    
    img = Image.open(io.BytesIO(img_bytes))
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    prompt = f"""Look at this sheet music page. Does the song title "{entry['song']}" appear on this page?

Answer with ONLY "YES" or "NO" - nothing else."""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 10,
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
        answer = response_body['content'][0]['text'].strip().upper()
        
        if answer == "YES":
            print(f"✅ {entry['song']:20s} TOC {entry['toc_page']:3d} -> index {pdf_index:3d}: FOUND")
        else:
            print(f"❌ {entry['song']:20s} TOC {entry['toc_page']:3d} -> index {pdf_index:3d}: NOT FOUND")
    except Exception as e:
        print(f"❌ {entry['song']:20s} TOC {entry['toc_page']:3d} -> index {pdf_index:3d}: ERROR - {e}")

print("=" * 60)
