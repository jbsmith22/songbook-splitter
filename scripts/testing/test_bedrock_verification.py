#!/usr/bin/env python3
"""
Test AWS Bedrock (Claude 3.5 Sonnet) on the 50 manually reviewed PDFs.

This validates accuracy before running the full 11,976 PDF verification.
"""

import json
import base64
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional
import boto3
from tqdm import tqdm

# Configuration
PROCESSED_SONGS_PATH = Path("C:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("S:/SlowImageCache/pdf_verification")  # Use slow cache for testing
# Use cross-region inference profile for Claude 3.5 Sonnet v2
# This allows access without enabling the model in a specific region
BEDROCK_MODEL = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_REGION = "us-east-1"
JPG_QUALITY = 90
RENDER_DPI = 300

# Known errors that SHOULD be flagged
KNOWN_ERRORS = {
    "The Police - Every Breath You Take.pdf": "Page 6 has Forever Young",
    "Oscar Hammerstein - Climb Ev'ry Mountain.pdf": "Two songs on one page",
    "Billy Joel - Opus 8 Suite For Piano (star-crossed) I. Innamorato.pdf": "Starts mid-song, split at page 3",
    "The Lion King - Under The Stars.pdf": "Splits on pages 2 and 3",
    "Bob Dylan - It's Alright, Ma (i'm Only Bleeding).pdf": "Starts mid-song, split on page 2",
}

@dataclass
class BedrockResult:
    pdf_path: str
    page_count: int
    passed: bool
    issues: List[str]
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
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare request
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
            
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body)
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            
            # Calculate cost (approximate)
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
    
    # Get cache directory
    rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
    artist = rel_path.parts[0]
    book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
    
    cache_dir = CACHE_PATH / artist / book
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Render pages
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


def verify_pdf_with_bedrock(pdf_path: Path, bedrock_client: BedrockVisionClient) -> BedrockResult:
    """Verify a PDF using Bedrock."""
    start_time = time.time()
    total_cost = 0
    
    # Render pages
    rendered_pages = render_pdf_pages(pdf_path)
    if not rendered_pages:
        return BedrockResult(
            pdf_path=str(pdf_path),
            page_count=0,
            passed=False,
            issues=["Failed to render pages"],
            processing_time=time.time() - start_time,
            cost_estimate=0
        )
    
    issues = []
    
    # Check all pages (including page 1 for multi-song single-page PDFs)
    for i in range(len(rendered_pages)):
        is_first = (i == 0)
        is_last = (i == len(rendered_pages) - 1)
        
        # Different prompts for first page vs others
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
        
        # Check if it says YES
        if response_text.upper().startswith('YES'):
            if is_first:
                issues.append(f"Page 1 has multiple songs (should be split)")
            else:
                page_type = "Last page" if is_last else f"Page {i+1}"
                issues.append(f"{page_type} has new song starting (missed split)")
    
    passed = len(issues) == 0
    processing_time = time.time() - start_time
    
    return BedrockResult(
        pdf_path=str(pdf_path),
        page_count=len(rendered_pages),
        passed=passed,
        issues=issues,
        processing_time=processing_time,
        cost_estimate=total_cost
    )


def main():
    print("AWS Bedrock Verification Test")
    print("=" * 80)
    print(f"Model: {BEDROCK_MODEL}")
    print(f"Cache: {CACHE_PATH}")
    print("=" * 80)
    
    # Initialize Bedrock client
    try:
        bedrock = BedrockVisionClient()
        print("✓ Bedrock client initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Bedrock: {e}")
        print("\nMake sure you're logged in:")
        print("  aws sso login --profile default")
        return
    
    # Load the 50 test PDFs from the most recent pilot run
    # For now, let's test with the 5 known errors
    test_pdfs = [
        PROCESSED_SONGS_PATH / "Various Artists/Best Of 80s Rock [pvg]/The Police - Every Breath You Take.pdf",
        PROCESSED_SONGS_PATH / "_broadway Shows/Various Artists - The Ultimate Broadway Fakebook/Oscar Hammerstein - Climb Ev'ry Mountain.pdf",
        PROCESSED_SONGS_PATH / "Billy Joel/Fantasies & Delusions/Billy Joel - Opus 8 Suite For Piano (star-crossed) I. Innamorato.pdf",
        PROCESSED_SONGS_PATH / "_broadway Shows/Various Artists - Lion King [score]/The Lion King - Under The Stars.pdf",
        PROCESSED_SONGS_PATH / "Bob Dylan/Anthology 2/Bob Dylan - It's Alright, Ma (i'm Only Bleeding).pdf",
    ]
    
    print(f"\nTesting {len(test_pdfs)} known error PDFs...")
    print("=" * 80)
    
    results = []
    total_cost = 0
    
    for pdf_path in tqdm(test_pdfs, desc="Verifying PDFs"):
        if not pdf_path.exists():
            print(f"\n✗ Not found: {pdf_path.name}")
            continue
        
        result = verify_pdf_with_bedrock(pdf_path, bedrock)
        results.append(result)
        total_cost += result.cost_estimate
        
        # Show result
        status = "✗ MISSED" if result.passed else "✓ CAUGHT"
        print(f"\n{status}: {pdf_path.name}")
        if result.issues:
            for issue in result.issues:
                print(f"  - {issue}")
        print(f"  Cost: ${result.cost_estimate:.4f}, Time: {result.processing_time:.1f}s")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    caught = sum(1 for r in results if not r.passed)
    print(f"Caught: {caught}/{len(results)}")
    print(f"Total cost: ${total_cost:.4f}")
    print(f"Average cost per PDF: ${total_cost/len(results):.4f}")
    
    # Extrapolate to full run
    full_cost = (total_cost / len(results)) * 11976
    print(f"\nEstimated cost for 11,976 PDFs: ${full_cost:.2f}")


if __name__ == "__main__":
    main()
