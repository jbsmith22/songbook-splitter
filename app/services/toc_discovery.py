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
        
        # Score pages for TOC likelihood
        scored_pages = []
        for page_num, text in extracted_text.items():
            score = self.score_toc_likelihood(text)
            scored_pages.append((page_num, score))
            logger.debug(f"Page {page_num} TOC score: {score:.2f}")
        
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

    
    def score_toc_likelihood(self, text: str) -> float:
        """
        Score page for TOC-likeness based on patterns.
        
        Uses heuristics:
        - Presence of page numbers (numeric patterns)
        - Keywords like "Contents", "Index", "Songs"
        - High density of short lines (song titles)
        - Columnar layout indicators (dots, tabs)
        - Ratio of numbers to text
        
        Args:
            text: Extracted text from page
        
        Returns:
            Confidence score 0.0-1.0
        """
        if not text or len(text.strip()) < 10:
            return 0.0
        
        score = 0.0
        lines = text.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if not non_empty_lines:
            return 0.0
        
        # Heuristic 1: Keywords (weight: 0.25)
        keywords = ['contents', 'index', 'songs', 'table of contents', 'toc']
        text_lower = text.lower()
        keyword_found = any(keyword in text_lower for keyword in keywords)
        if keyword_found:
            score += 0.25
        
        # Heuristic 2: Page numbers (weight: 0.30)
        # Count lines with numbers at the end
        import re
        lines_with_page_numbers = 0
        for line in non_empty_lines:
            # Match patterns like "Song Title ... 42" or "Song Title 42"
            if re.search(r'\d+\s*$', line):
                lines_with_page_numbers += 1
        
        page_number_ratio = lines_with_page_numbers / len(non_empty_lines)
        if page_number_ratio > 0.3:  # At least 30% of lines have page numbers
            score += 0.30 * min(page_number_ratio / 0.5, 1.0)  # Cap at 50%
        
        # Heuristic 3: Dots/leader characters (weight: 0.20)
        # TOCs often have "Song Title ........ 42"
        lines_with_dots = sum(1 for line in non_empty_lines if '...' in line or '\t' in line)
        dots_ratio = lines_with_dots / len(non_empty_lines)
        if dots_ratio > 0.2:
            score += 0.20 * min(dots_ratio / 0.4, 1.0)
        
        # Heuristic 4: Short lines (weight: 0.15)
        # TOC entries are typically short (song titles)
        avg_line_length = sum(len(line) for line in non_empty_lines) / len(non_empty_lines)
        if 20 < avg_line_length < 80:  # Typical TOC entry length
            score += 0.15
        
        # Heuristic 5: High line density (weight: 0.10)
        # TOCs have many lines relative to text length
        line_density = len(non_empty_lines) / len(text)
        if line_density > 0.01:  # At least 1 line per 100 characters
            score += 0.10 * min(line_density / 0.02, 1.0)
        
        return min(score, 1.0)
    
    def select_toc_pages(self, scored_pages: List[tuple[int, float]], 
                        threshold: float = 0.5) -> List[int]:
        """
        Select pages that are likely TOC based on scores.
        
        Args:
            scored_pages: List of (page_num, score) tuples
            threshold: Minimum score to consider a page as TOC
        
        Returns:
            List of page indices that are likely TOC pages
        """
        # Sort by score descending
        scored_pages.sort(key=lambda x: x[1], reverse=True)
        
        # Select pages above threshold
        toc_pages = [page_num for page_num, score in scored_pages if score >= threshold]
        
        # If no pages meet threshold, take the top 2 pages (likely to be TOC)
        if not toc_pages and scored_pages:
            toc_pages = [scored_pages[0][0]]
            if len(scored_pages) > 1:
                toc_pages.append(scored_pages[1][0])
        
        # Sort by page number for output
        toc_pages.sort()
        
        logger.info(f"Selected {len(toc_pages)} TOC pages with threshold {threshold}")
        return toc_pages
