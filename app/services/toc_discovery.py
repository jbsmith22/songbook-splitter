"""
TOC Discovery Service - Locates and extracts text from Table of Contents pages.

This module provides functions for:
- Rendering PDF pages as images
- Extracting text using AWS Textract (or mock for local mode)
- Identifying TOC pages based on content patterns
"""

import io
from typing import List, Dict, Optional
from pathlib import Path
import logging
from PIL import Image
import fitz  # PyMuPDF
import boto3
from botocore.exceptions import ClientError
from app.models import TOCDiscoveryResult

logger = logging.getLogger(__name__)


class MockTextract:
    """Mock Textract implementation for local mode."""
    
    def __init__(self):
        logger.info("MockTextract initialized")
    
    def detect_document_text(self, Document: dict) -> dict:
        """
        Mock text detection that returns a simple response.
        In a real implementation, this could use local OCR or pre-recorded responses.
        """
        # Return a mock response structure
        return {
            'Blocks': [
                {
                    'BlockType': 'LINE',
                    'Text': 'Table of Contents',
                    'Confidence': 95.0
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Song Title 1 ............... 10',
                    'Confidence': 92.0
                },
                {
                    'BlockType': 'LINE',
                    'Text': 'Song Title 2 ............... 15',
                    'Confidence': 93.0
                }
            ]
        }


class TOCDiscoveryService:
    """Service for discovering and extracting TOC pages from PDFs."""
    
    def __init__(self, local_mode: bool = False):
        """
        Initialize TOC discovery service.
        
        Args:
            local_mode: If True, use mock Textract instead of real service
        """
        self.local_mode = local_mode
        
        if local_mode:
            self.textract = MockTextract()
            logger.info("TOCDiscoveryService initialized in local mode")
        else:
            self.textract_client = boto3.client('textract')
            logger.info("TOCDiscoveryService initialized with AWS Textract")
    
    def discover_toc(self, pdf_path: str, max_pages: int = 20) -> TOCDiscoveryResult:
        """
        Find TOC pages in PDF and extract text.
        
        Args:
            pdf_path: Path to PDF file (local or downloaded from S3)
            max_pages: Maximum number of pages to scan for TOC
        
        Returns:
            TOCDiscoveryResult with identified TOC pages and extracted text
        """
        logger.info(f"Starting TOC discovery for {pdf_path}, scanning up to {max_pages} pages")
        
        # Render pages as images
        images = self.render_pages(pdf_path, range(max_pages))
        
        # Extract text from each page
        extracted_text = {}
        confidence_scores = {}
        
        for page_num, image in images.items():
            try:
                text, confidence = self.extract_text_from_image(image, page_num)
                extracted_text[page_num] = text
                confidence_scores[page_num] = confidence
                logger.debug(f"Extracted text from page {page_num}, confidence: {confidence:.2f}")
            except Exception as e:
                logger.error(f"Error extracting text from page {page_num}: {e}")
                extracted_text[page_num] = ""
                confidence_scores[page_num] = 0.0
        
        # Score pages for TOC likelihood using vision
        scored_pages = []
        for page_num, image in images.items():
            score = self.score_toc_likelihood_vision(image, page_num)
            scored_pages.append((page_num, score))
            logger.debug(f"Page {page_num} TOC vision score: {score:.2f}")
        
        # Select pages above threshold
        toc_pages = self.select_toc_pages(scored_pages, threshold=0.5)
        
        result = TOCDiscoveryResult(
            toc_pages=toc_pages,
            extracted_text=extracted_text,
            confidence_scores=confidence_scores,
            textract_responses_s3_uri=""  # Will be set when saving to S3
        )
        
        logger.info(f"TOC discovery complete. Found {len(toc_pages)} candidate pages")
        return result
    
    def render_pages(self, pdf_path: str, page_range: range) -> Dict[int, Image.Image]:
        """
        Render PDF pages as images.
        
        Args:
            pdf_path: Path to PDF file
            page_range: Range of page numbers to render
        
        Returns:
            Dictionary mapping page number to PIL Image
        """
        images = {}
        
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            for page_num in page_range:
                if page_num >= total_pages:
                    logger.warning(f"Page {page_num} exceeds document length ({total_pages})")
                    break
                
                page = doc[page_num]
                
                # Render at 150 DPI for good quality without excessive size
                mat = fitz.Matrix(150/72, 150/72)
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                
                images[page_num] = image
                logger.debug(f"Rendered page {page_num} at {image.size}")
            
            doc.close()
            logger.info(f"Rendered {len(images)} pages from {pdf_path}")
            
        except Exception as e:
            logger.error(f"Error rendering pages: {e}")
            raise
        
        return images
    
    def extract_text_from_image(self, image: Image.Image, page_num: int) -> tuple[str, float]:
        """
        Extract text from image using Textract.
        
        Args:
            image: PIL Image object
            page_num: Page number (for logging)
        
        Returns:
            Tuple of (extracted_text, average_confidence)
        """
        try:
            # Convert image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Call Textract
            if self.local_mode:
                response = self.textract.detect_document_text(
                    Document={'Bytes': img_bytes.getvalue()}
                )
            else:
                response = self.textract_client.detect_document_text(
                    Document={'Bytes': img_bytes.getvalue()}
                )
            
            # Extract text and confidence from blocks
            text_lines = []
            confidences = []
            
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_lines.append(block.get('Text', ''))
                    confidences.append(block.get('Confidence', 0.0))
            
            full_text = '\n'.join(text_lines)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return full_text, avg_confidence
            
        except ClientError as e:
            logger.error(f"Textract API error on page {page_num}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error extracting text from page {page_num}: {e}")
            raise
    
    def extract_text_textract(self, images: List[Image.Image]) -> List[dict]:
        """
        Call Textract DetectDocumentText for multiple images.
        
        Args:
            images: List of PIL Image objects
        
        Returns:
            List of Textract response dictionaries
        """
        responses = []
        
        for i, image in enumerate(images):
            try:
                text, confidence = self.extract_text_from_image(image, i)
                responses.append({
                    'page_num': i,
                    'text': text,
                    'confidence': confidence
                })
            except Exception as e:
                logger.error(f"Error processing image {i}: {e}")
                responses.append({
                    'page_num': i,
                    'text': '',
                    'confidence': 0.0,
                    'error': str(e)
                })
        
        return responses

    
    def score_toc_likelihood_vision(self, image: Image.Image, page_num: int) -> float:
        """
        Score page for TOC-likeness using Bedrock vision (Claude).
        
        Uses Claude to analyze the page image and determine if it's a TOC.
        
        Args:
            image: PIL Image of the page
            page_num: Page number (for logging)
        
        Returns:
            Confidence score 0.0-1.0
        """
        try:
            import boto3
            import base64
            import json
            
            # Convert image to base64
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            image_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
            
            # Call Bedrock with vision
            if self.local_mode:
                # Mock response for local mode
                logger.info(f"Local mode: Mocking vision analysis for page {page_num}")
                # Return high score for page 1, low for others
                return 0.95 if page_num == 1 else 0.1
            
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            prompt = """Analyze this page image and determine if it is a Table of Contents (TOC) for a music book.

A Table of Contents typically has:
- A list of song titles
- Page numbers next to each song
- May have dots or lines connecting titles to page numbers
- Usually appears near the beginning of a book
- Clean, organized layout

Sheet music pages have:
- Musical staff lines (5 horizontal lines)
- Musical notes and symbols
- Chord symbols (like Em, F7, Dm)
- Lyrics under the staff lines

Return a JSON object with:
{
  "is_toc": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}"""

            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 500,
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
                ]
            })
            
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=body
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text']
            
            # Parse JSON response
            # Extract JSON from response (may have markdown code blocks)
            import re
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                is_toc = result.get('is_toc', False)
                confidence = result.get('confidence', 0.0)
                reasoning = result.get('reasoning', '')
                
                logger.info(f"Page {page_num} vision analysis: is_toc={is_toc}, confidence={confidence}, reasoning={reasoning}")
                
                return confidence if is_toc else 0.0
            else:
                logger.warning(f"Could not parse JSON from Bedrock response for page {page_num}")
                return 0.0
                
        except Exception as e:
            logger.error(f"Error in vision-based TOC detection for page {page_num}: {e}")
            # Fallback to text-based heuristics
            return 0.0
    
    def select_toc_pages(self, scored_pages: List[tuple[int, float]],
                        threshold: float = 0.5) -> List[int]:
        """
        Select pages that are likely TOC based on scores.

        Handles multi-page TOCs by including consecutive pages after a high-scoring TOC page.

        Args:
            scored_pages: List of (page_num, score) tuples
            threshold: Minimum score to consider a page as TOC

        Returns:
            List of page indices that are likely TOC pages
        """
        # Sort by score descending
        scored_pages_by_score = sorted(scored_pages, key=lambda x: x[1], reverse=True)

        # Create a dict for easy lookup
        score_dict = {page_num: score for page_num, score in scored_pages}

        # Select pages above threshold
        toc_pages = set(page_num for page_num, score in scored_pages if score >= threshold)

        # If no pages meet threshold, take the top page
        if not toc_pages and scored_pages_by_score:
            toc_pages.add(scored_pages_by_score[0][0])

        # MULTI-PAGE TOC HANDLING: Include consecutive pages after high-scoring TOC pages
        # A page immediately following a TOC page is likely also TOC (continuation)
        # Use a lower threshold (0.2) for consecutive pages
        consecutive_threshold = 0.2
        pages_to_add = set()
        for page_num in list(toc_pages):
            next_page = page_num + 1
            if next_page in score_dict:
                # Include next page if it has any reasonable score
                if score_dict[next_page] >= consecutive_threshold:
                    pages_to_add.add(next_page)
                    logger.info(f"Including consecutive TOC page {next_page} (score: {score_dict[next_page]:.2f})")

        toc_pages.update(pages_to_add)

        # Sort by page number for output
        toc_pages_list = sorted(toc_pages)

        logger.info(f"Selected {len(toc_pages_list)} TOC pages with threshold {threshold}")
        return toc_pages_list
