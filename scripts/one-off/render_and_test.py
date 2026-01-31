"""
Render all pages and test vision on known song locations.
"""
import fitz
import boto3
import json
import base64
from pathlib import Path
from PIL import Image
import io

# User told us: Big Shot at index 3, TOC page 10, offset = -7
OFFSET = -7

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

print("Step 1: Rendering all pages...")
doc = fitz.open("test-billy-joel.pdf")
total_pages = len(doc)

output_dir = Path("rendered_pages")
output_dir.mkdir(exist_ok=True)

page_images = {}
for i in range(total_pages):
    page = doc[i]
    pix = page.get_pixmap(dpi=72)
    img_bytes = pix.tobytes("png")
    
    png_path = output_dir / f"page_{i:03d}.png"
    with open(png_path, 'wb') as f:
        f.write(img_bytes)
    
    page_images[i] = img_bytes
    
    if (i + 1) % 10 == 0:
        print(f"  Rendered {i + 1}/{total_pages} pages...")

print(f"All {total_pages} pages saved to {output_dir}/")
doc.close()

print("\nStep 2: Testing vision on known song locations...")
bedrock = boto3.client('bedrock-runtime')

for entry in TOC_ENTRIES:
    pdf_index = entry["toc_page"] + OFFSET
    
    if pdf_index < 0 or pdf_index >= total_pages:
        print(f"❌ {entry['song']:20s} index {pdf_index} OUT OF RANGE")
        continue
    
    # Get the pre-rendered image
    img_bytes = page_images[pdf_index]
    img = Image.open(io.BytesIO(img_bytes))
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Ask vision if this page has the song title
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

print("\nDONE! Check rendered_pages/ folder for all PNG files.")
