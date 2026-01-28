"""
Verify the final extracted PDFs using vision.
"""
import boto3
import json
import base64
import fitz
from PIL import Image
import io
from pathlib import Path

bedrock = boto3.client('bedrock-runtime')

songs = {
    "Big_Shot.pdf": "Big Shot",
    "Honesty.pdf": "Honesty",
    "My_Life.pdf": "My Life",
    "Zanzibar.pdf": "Zanzibar",
    "Rosalindas_Eyes.pdf": "Rosalinda's Eyes",
    "Half_A_Mile_Away.pdf": "Half A Mile Away",
    "Until_The_Night.pdf": "Until The Night"
}

output_dir = Path("test_output_final")

print("Verifying final extracted PDFs...")
print("=" * 60)

for filename, expected_title in songs.items():
    pdf_path = output_dir / filename
    
    if not pdf_path.exists():
        print(f"❌ {filename}: FILE NOT FOUND")
        continue
    
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        
        # Render as image
        pix = first_page.get_pixmap(dpi=72)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Ask Bedrock if this page contains the expected title
        prompt = f"""Look at this sheet music page. Does the song title "{expected_title}" appear on this page?

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
        
        if answer == "YES":
            print(f"✅ {filename}: CORRECT - Contains '{expected_title}' ({len(doc)} pages)")
        else:
            print(f"❌ {filename}: WRONG - Does NOT contain '{expected_title}' ({len(doc)} pages)")
        
        doc.close()
        
    except Exception as e:
        print(f"❌ {filename}: ERROR - {e}")

print("=" * 60)
