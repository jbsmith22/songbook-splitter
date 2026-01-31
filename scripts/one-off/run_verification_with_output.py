#!/usr/bin/env python3
"""
Run Bedrock verification and generate web-based review interface.
"""

import json
import base64
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List
import boto3
from tqdm import tqdm

# Configuration
PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("S:/SlowImageCache/pdf_verification")
BEDROCK_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"
JPG_QUALITY = 85  # Reduced from 90 to keep under 5MB
RENDER_DPI = 200  # Reduced from 300 to keep under 5MB and 8000px limit
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB Bedrock limit
MAX_DIMENSION = 8000  # Bedrock pixel dimension limit

@dataclass
class PageAnalysis:
    page_num: int
    image_path: str
    has_issue: bool
    issue_description: str
    bedrock_response: str

@dataclass
class VerificationResult:
    pdf_path: str
    pdf_name: str
    page_count: int
    passed: bool
    issues: List[str]
    page_analyses: List[PageAnalysis]
    processing_time: float
    cost_estimate: float


class BedrockVisionClient:
    """Client for AWS Bedrock Claude 3.5 Sonnet."""
    
    def __init__(self, region: str = BEDROCK_REGION):
        self.client = boto3.client('bedrock-runtime', region_name=region)
        self.model_id = BEDROCK_MODEL
        
    def analyze_image(self, image_path: Path, prompt: str) -> dict:
        """Call Bedrock with image."""
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Check file size
            if len(image_bytes) > MAX_IMAGE_SIZE:
                return {
                    'error': f'Image too large: {len(image_bytes)} bytes > {MAX_IMAGE_SIZE} bytes',
                    'cost': 0
                }
            
            # Check dimensions
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(image_bytes))
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                return {
                    'error': f'Image dimensions too large: {img.width}x{img.height} > {MAX_DIMENSION}px',
                    'cost': 0
                }
            
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            response_body = json.loads(response['body'].read())
            
            input_tokens = response_body.get('usage', {}).get('input_tokens', 0)
            output_tokens = response_body.get('usage', {}).get('output_tokens', 0)
            cost = (input_tokens / 1000000 * 3.0) + (output_tokens / 1000000 * 15.0)
            
            return {
                'text': response_body['content'][0]['text'],
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'cost': cost
            }
            
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return {'error': str(e), 'cost': 0}


def render_pdf_pages(pdf_path: Path) -> List[Path]:
    """Render PDF pages to JPG."""
    import fitz
    
    rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
    artist = rel_path.parts[0]
    book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
    
    cache_dir = CACHE_PATH / artist / book
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    rendered_pages = []
    try:
        doc = fitz.open(pdf_path)
        zoom = RENDER_DPI / 72
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in range(len(doc)):
            cache_file = cache_dir / f"{pdf_path.stem}_page_{page_num}.jpg"
            
            if not cache_file.exists():
                page = doc[page_num]
                pix = page.get_pixmap(matrix=mat)
                pix.save(str(cache_file), "jpeg", jpg_quality=JPG_QUALITY)
            
            rendered_pages.append(cache_file)
        
        doc.close()
    except Exception as e:
        print(f"Error rendering {pdf_path}: {e}")
    
    return rendered_pages


def verify_pdf_with_bedrock(pdf_path: Path, bedrock_client: BedrockVisionClient) -> VerificationResult:
    """Verify a PDF using Bedrock."""
    start_time = time.time()
    total_cost = 0
    
    rendered_pages = render_pdf_pages(pdf_path)
    if not rendered_pages:
        return VerificationResult(
            pdf_path=str(pdf_path),
            pdf_name=pdf_path.name,
            page_count=0,
            passed=False,
            issues=["Failed to render pages"],
            page_analyses=[],
            processing_time=time.time() - start_time,
            cost_estimate=0
        )
    
    issues = []
    page_analyses = []
    
    for i in range(len(rendered_pages)):
        is_first = (i == 0)
        is_last = (i == len(rendered_pages) - 1)
        
        if is_first:
            prompt = f"""Look at this sheet music page very carefully.

This is page 1 of {len(rendered_pages)} in this PDF.

CRITICAL QUESTION: Does this page contain MORE THAN ONE COMPLETE SONG?

Look for:
1. Multiple distinct song titles on the same page
2. Each with their own first measures/bars
3. Clear visual breaks between songs

Answer YES if you see multiple complete songs starting on this single page.
Answer NO if you see only one song (even if it starts mid-page after another song ends).

Respond with ONLY "YES" or "NO" followed by a brief explanation (one sentence)."""
        else:
            prompt = f"""Look at this sheet music page very carefully.

This is page {i+1} of {len(rendered_pages)} in this PDF.

CRITICAL QUESTION: Does this page show the CLEAR BEGINNING of a COMPLETELY NEW AND DIFFERENT SONG?

To answer YES, you must see:
1. A prominent song title (even if the page is mostly blank)
2. OR the very first measures/bars of a new song with a clear visual break
3. This should be a DIFFERENT song from what came before

Answer YES if:
- You see a new song title (even without notation yet)
- You see the start of a new song with different title/key/tempo
- You see "TAG" or "SEGUE" sections that are separate songs

Answer NO if:
- This is just a continuation of the current song
- There are section markers within the same song
- There is supplementary content (photos, text, discography)

Respond with ONLY "YES" or "NO" followed by a brief explanation (one sentence)."""

        result = bedrock_client.analyze_image(rendered_pages[i], prompt)
        total_cost += result.get('cost', 0)
        
        if 'error' in result:
            continue
        
        response_text = result['text'].strip()
        has_issue = response_text.upper().startswith('YES')
        
        if has_issue:
            if is_first:
                issue_desc = f"Page 1 has multiple songs (should be split)"
            else:
                page_type = "Last page" if is_last else f"Page {i+1}"
                issue_desc = f"{page_type} has new song starting (missed split)"
            issues.append(issue_desc)
        else:
            issue_desc = ""
        
        page_analyses.append(PageAnalysis(
            page_num=i+1,
            image_path=str(rendered_pages[i]),
            has_issue=has_issue,
            issue_description=issue_desc,
            bedrock_response=response_text
        ))
    
    passed = len(issues) == 0
    processing_time = time.time() - start_time
    
    return VerificationResult(
        pdf_path=str(pdf_path),
        pdf_name=pdf_path.name,
        page_count=len(rendered_pages),
        passed=passed,
        issues=issues,
        page_analyses=page_analyses,
        processing_time=processing_time,
        cost_estimate=total_cost
    )


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py run_verification_with_output.py <pdf_list_file>")
        print("  pdf_list_file: Text file with one PDF path per line")
        return
    
    pdf_list_file = Path(sys.argv[1])
    if not pdf_list_file.exists():
        print(f"Error: {pdf_list_file} not found")
        return
    
    # Read PDF list
    with open(pdf_list_file, 'r') as f:
        pdf_paths = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(pdf_paths)} PDFs to verify")
    
    # Initialize Bedrock
    try:
        bedrock = BedrockVisionClient()
        print("✓ Bedrock client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Bedrock: {e}")
        return
    
    # Run verification
    results = []
    total_cost = 0
    
    for pdf_rel_path in tqdm(pdf_paths, desc="Verifying PDFs"):
        pdf_path = PROCESSED_SONGS_PATH / pdf_rel_path
        
        if not pdf_path.exists():
            print(f"\n✗ Not found: {pdf_path}")
            continue
        
        result = verify_pdf_with_bedrock(pdf_path, bedrock)
        results.append(result)
        total_cost += result.cost_estimate
    
    # Save results
    output_file = Path("verification_results/bedrock_results.json")
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Flagged: {sum(1 for r in results if not r.passed)}/{len(results)}")


if __name__ == "__main__":
    main()
