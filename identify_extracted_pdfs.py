"""
Identify what song titles are actually in the extracted PDFs.
"""
import boto3
import json
import base64
import fitz
from PIL import Image
import io
from pathlib import Path

bedrock = boto3.client('bedrock-runtime')

# Files to check
files = [
    "Big_Shot.pdf",
    "Half_A_Mile_Away.pdf",
    "Honesty.pdf",
    "My_Life.pdf",
    "Rosalinda's_Eyes.pdf",
    "Until_The_Night.pdf",
    "Zanzibar.pdf"
]

output_dir = Path("test_output_aws_v2")

print("Identifying song titles in extracted PDFs...")
print("=" * 60)

for filename in files:
    pdf_path = output_dir / filename
    
    if not pdf_path.exists():
        print(f"❌ {filename}: FILE NOT FOUND")
        continue
    
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        
        # Render as image
        pix = first_page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Ask Bedrock what song this is
        prompt = """Look at this sheet music page. What is the song title shown on this page?

Look for the title at the top of the page. It might be in various fonts or styles.

Respond with ONLY the song title, nothing else."""

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
        
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            body=json.dumps(request_body)
        )
        
        response_body = json.loads(response['body'].read())
        actual_title = response_body['content'][0]['text'].strip()
        
        print(f"{filename} ({len(doc)} pages):")
        print(f"  Actual title: {actual_title}")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ {filename}: ERROR - {e}")

print("=" * 60)
