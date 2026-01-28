"""
Check what's actually on pages 47 and 55 to resolve the confusion.
"""
import boto3
import json
import base64
from pathlib import Path
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')
rendered_dir = Path("rendered_pages")

pages_to_check = [47, 55]

for pdf_idx in pages_to_check:
    png_path = rendered_dir / f"page_{pdf_idx:03d}.png"
    
    print(f"\n{'=' * 80}")
    print(f"Checking PDF index {pdf_idx}")
    print('=' * 80)
    
    with open(png_path, 'rb') as f:
        img_bytes = f.read()
    
    img = Image.open(io.BytesIO(img_bytes))
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    prompt = """Look at this sheet music page carefully.

1. What is the SONG TITLE at the top of this page?
2. What is the PRINTED PAGE NUMBER at the bottom?
3. Is there an ARTIST NAME on the page?

Be very precise about the song title - read it exactly as written."""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 200,
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
        
        print(f"\nVision Response:")
        print(answer)
        
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n{'=' * 80}")
print("SUMMARY")
print('=' * 80)
print("\nBased on TOC:")
print("- '52nd Street' should be at TOC page 60")
print("- 'Until the Night' should be at TOC page 68")
print("\nUser told us:")
print("- 'Until the Night' starts at PDF index 47")
print("- '52nd Street' starts at PDF index 55")
