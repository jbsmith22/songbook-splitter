import boto3
import json
import base64
import fitz
from PIL import Image
import io

bedrock = boto3.client('bedrock-runtime')

# Check what's on page 9 (where "Big Shot" should be)
doc = fitz.open("test-billy-joel.pdf")
page = doc[9]

# Render as image
pix = page.get_pixmap(dpi=150)
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
song_title = response_body['content'][0]['text'].strip()

print(f"Page 9 (TOC said 'Big Shot' page 10):")
print(f"Bedrock says the song is: {song_title}")

doc.close()
