#!/usr/bin/env python3
"""
Simple Flask server to provide auto-detection of songs in PDFs.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import base64
from pathlib import Path
import boto3

app = Flask(__name__)
CORS(app)  # Enable CORS for local HTML file access

BEDROCK_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"
CACHE_PATH = Path("S:/SlowImageCache/pdf_verification")

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime', region_name=BEDROCK_REGION)
        self.model_id = BEDROCK_MODEL
    
    def analyze_images(self, image_paths, prompt):
        """Analyze multiple images with a single prompt."""
        try:
            # Build content array with all images
            content = []
            for img_path in image_paths:
                with open(img_path, 'rb') as f:
                    image_bytes = f.read()
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": image_base64
                    }
                })
            
            # Add text prompt
            content.append({
                "type": "text",
                "text": prompt
            })
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [
                    {
                        "role": "user",
                        "content": content
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
            
        except Exception as e:
            return f"Error: {str(e)}"

bedrock = BedrockClient()

@app.route('/api/detect-songs', methods=['POST'])
def detect_songs():
    """Auto-detect songs in a PDF using Claude."""
    try:
        data = request.json
        pdf_path = data.get('pdf_path')
        image_paths = data.get('image_paths', [])
        
        if not image_paths:
            return jsonify({'error': 'No images provided'}), 400
        
        # Convert string paths to Path objects
        image_paths = [Path(p) for p in image_paths]
        
        # Build prompt for Claude
        prompt = f"""You are looking at {len(image_paths)} pages of sheet music, numbered 1 through {len(image_paths)}.

YOUR TASK: Identify every distinct song in these pages.

STEP 1: For each page, identify if there's a song title visible
STEP 2: Determine which pages belong to each song
STEP 3: List each song with its page range

CRITICAL RULES:
- ONLY report songs you can actually see in the images
- ONLY use page numbers from 1 to {len(image_paths)}
- DO NOT make up songs or page numbers
- A song title is usually at the top of the page in larger text
- If you see multiple song titles, list each one separately
- If a song spans multiple consecutive pages, use a range like "1-3"
- If multiple songs are on the same page, list each with that page number

Respond in this exact JSON format:
{{
  "songs": [
    {{"title": "Exact Song Title From Page", "pages": "1-3"}},
    {{"title": "Another Song Title", "pages": "4"}}
  ]
}}

VERIFICATION: Before responding, count your songs and make sure every page number you list is between 1 and {len(image_paths)}.

ONLY return the JSON, no other text."""

        # Call Claude
        response = bedrock.analyze_images(image_paths, prompt)
        
        # Parse JSON response
        try:
            # Extract JSON from response (Claude might add text around it)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                return jsonify(result)
            else:
                return jsonify({'error': 'Could not parse response', 'raw': response}), 500
        except json.JSONDecodeError as e:
            return jsonify({'error': f'JSON parse error: {str(e)}', 'raw': response}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("Starting split detection server...")
    print("Server will run on http://localhost:5000")
    print("Press Ctrl+C to stop")
    app.run(debug=True, port=5000)
