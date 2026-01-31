"""
Analyze the TOC and verify where songs actually start in the source PDF.
"""
import boto3
import json
import base64
import fitz
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')

# TOC from previous parsing
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

doc = fitz.open("test-billy-joel.pdf")
total_pages = len(doc)

print(f"Source PDF has {total_pages} pages")
print("=" * 60)

# Check a few pages around each TOC entry
for entry in toc_entries[:4]:  # Just check first 4 to save API calls
    song = entry["song"]
    toc_page = entry["toc_page"]
    
    print(f"\n{song} (TOC says page {toc_page}):")
    
    # Check pages around the TOC page number
    for offset in [-2, -1, 0, 1, 2]:
        pdf_index = toc_page + offset
        
        if pdf_index < 0 or pdf_index >= total_pages:
            continue
        
        page = doc[pdf_index]
        
        # Render as image
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Ask Bedrock if this page contains the song title
        prompt = f"""Look at this sheet music page. Does the song title "{song}" appear on this page?

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
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        answer = response_body['content'][0]['text'].strip().upper()
        
        marker = "✅" if answer == "YES" else "  "
        print(f"  {marker} PDF index {pdf_index} (TOC+{offset:+d}): {answer}")

doc.close()
print("=" * 60)
