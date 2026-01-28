"""
Verify that Big Shot actually starts at PDF index 3 as the user stated.
"""
import boto3
import json
import base64
import fitz
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')

doc = fitz.open("test-billy-joel.pdf")
total_pages = len(doc)

print(f"Source PDF has {total_pages} pages")
print("=" * 60)
print("\nChecking pages around index 3 for 'Big Shot':")
print("-" * 60)

for pdf_index in range(0, 10):
    page = doc[pdf_index]
    
    # Render as image
    pix = page.get_pixmap(dpi=72)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    
    # Convert to base64
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    # Ask Bedrock if this page contains "Big Shot"
    prompt = """Look at this sheet music page. Does the song title "Big Shot" appear on this page?

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
    print(f"{marker} PDF index {pdf_index}: {answer}")

doc.close()
print("=" * 60)
