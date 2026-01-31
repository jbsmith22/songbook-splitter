"""
Check what vision actually sees on the pages we think songs start.
"""
import boto3
import json
import base64
from pathlib import Path
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')

# Check specific pages
pages_to_check = [3, 12, 18, 26, 33, 39, 45, 53]

rendered_dir = Path("rendered_pages")

for page_num in pages_to_check:
    png_path = rendered_dir / f"page_{page_num:03d}.png"
    
    if not png_path.exists():
        print(f"Page {page_num}: FILE NOT FOUND")
        continue
    
    with open(png_path, 'rb') as f:
        img_bytes = f.read()
    
    img = Image.open(io.BytesIO(img_bytes))
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Ask what's on this page
    prompt = """Look at this sheet music page. What is the song title shown on this page?

Look for the title at the top of the page. It might be in various fonts or styles.

Respond with ONLY the song title, nothing else. If you don't see a title, say "NO TITLE"."""

    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 50,
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
        
        print(f"Page {page_num:3d}: {answer}")
    except Exception as e:
        print(f"Page {page_num:3d}: ERROR - {e}")
