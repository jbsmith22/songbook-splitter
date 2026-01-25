"""
Page Mapper Service - Maps printed page numbers from TOC to actual PDF page indices.

This module provides functions for:
- Sampling TOC entries for verification
- Verifying page matches using fuzzy string matching
- Calculating offset between printed pages and PDF indices
- Applying mapping to all TOC entries
"""

import re
import json
from typing import List, Tuple, Optional
from dataclasses import dataclass
import logging
import fitz  # PyMuPDF
from difflib import SequenceMatcher
from app.models import TOCEntry, SongLocation, PageMapping

logger = logging.getLogger(__name__)


@dataclass
class OffsetModel:
    """Represents the offset calculation model."""
    offset: int
    confidence: float  # R² score or similar
    samples_verified: int


class PageMapperService:
    """Service for mapping printed page numbers to PDF indices."""
    
    def __init__(self, use_vision: bool = True):
        """
        Initialize page mapper service.
        
        Args:
            use_vision: If True, use vision-based verification for image PDFs
        """
        self.use_vision = use_vision
        if use_vision:
            try:
                import boto3
                self.bedrock_runtime = boto3.client('bedrock-runtime')
                logger.info("PageMapperService initialized with vision support")
            except Exception as e:
                logger.warning(f"Could not initialize Bedrock client: {e}")
                self.use_vision = False
                logger.info("PageMapperService initialized without vision support")
        else:
            logger.info("PageMapperService initialized without vision support")
    
    def build_page_mapping(self, pdf_path: str, toc_entries: List[TOCEntry], 
                          sample_size: int = 3) -> PageMapping:
        """
        Calculate page mapping by finding ALL songs using vision verification.
        
        The TOC page numbers are printed page numbers from the book, but PDF indices
        can be wildly offset and the offset may change throughout the book.
        We use vision to find each song's actual start page.
        
        Args:
            pdf_path: Path to PDF file
            toc_entries: List of TOC entries with printed page numbers (sorted)
            sample_size: Number of entries to sample for verification (unused, kept for compatibility)
        
        Returns:
            PageMapping with song locations
        """
        logger.info(f"Building page mapping for {len(toc_entries)} TOC entries using vision verification")
        
        if not toc_entries:
            return PageMapping(
                offset=0,
                confidence=0.0,
                samples_verified=0,
                song_locations=[]
            )
        
        # Sort entries by page number to ensure correct order
        sorted_entries = sorted(toc_entries, key=lambda e: e.page_number)
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        song_locations = []
        verified_count = 0
        expected_pdf_index = 0  # Start searching from beginning
        
        for i, entry in enumerate(sorted_entries):
            logger.info(f"Finding '{entry.song_title}' (TOC page {entry.page_number})...")
            
            # Calculate expected PDF index based on initial offset (if we have one)
            if i == 0:
                # For first song, search from beginning
                search_start = 0
            else:
                # For subsequent songs, start from expected position
                # Expected = previous song's PDF index + (this TOC page - previous TOC page)
                prev_location = song_locations[-1]
                toc_page_diff = entry.page_number - sorted_entries[i-1].page_number
                expected_pdf_index = prev_location.pdf_index + toc_page_diff
                search_start = expected_pdf_index
            
            # Find the song starting from expected position - search entire remaining PDF
            actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages, max_search=total_pages)
            
            if actual_pdf_index is None:
                logger.warning(f"Could not find '{entry.song_title}' - skipping")
                continue
            
            song_locations.append(SongLocation(
                song_title=entry.song_title,
                printed_page=entry.page_number,
                pdf_index=actual_pdf_index,
                artist=entry.artist
            ))
            
            verified_count += 1
            
            if i == 0:
                offset = actual_pdf_index - entry.page_number
                logger.info(f"Found first song '{entry.song_title}' at PDF index {actual_pdf_index} (TOC page {entry.page_number}, offset={offset})")
            else:
                offset_from_expected = actual_pdf_index - expected_pdf_index
                logger.info(f"Found '{entry.song_title}' at PDF index {actual_pdf_index} (expected {expected_pdf_index}, offset={offset_from_expected:+d})")
        
        doc.close()
        
        # Calculate average offset for confidence metric
        if song_locations:
            offsets = [loc.pdf_index - loc.printed_page for loc in song_locations]
            avg_offset = sum(offsets) // len(offsets)
            confidence = verified_count / len(sorted_entries)
        else:
            avg_offset = 0
            confidence = 0.0
        
        logger.info(f"Page mapping complete: verified {verified_count}/{len(sorted_entries)} songs")
        
        return PageMapping(
            offset=avg_offset,
            confidence=confidence,
            samples_verified=verified_count,
            song_locations=song_locations
        )
    
    def _find_song_forward(self, doc: fitz.Document, song_title: str, 
                          start_index: int, total_pages: int, max_search: int = 20) -> Optional[int]:
        """
        Search forward from start_index to find a page with the given song title.
        
        If we find music staffs but no title, we've gone too far into a song.
        
        Args:
            doc: PyMuPDF document
            song_title: Song title to find
            start_index: PDF index to start searching from
            total_pages: Total pages in document
            max_search: Maximum pages to search forward
        
        Returns:
            PDF index where song starts, or None if not found
        """
        for offset in range(max_search):
            pdf_index = start_index + offset
            
            if pdf_index >= total_pages:
                break
            
            page = doc[pdf_index]
            
            # Check if this page has the song title
            if self.verify_page_match(doc, pdf_index, song_title):
                return pdf_index
            
            # Check if we've gone too far (music staffs but no title)
            # This would indicate we're in the middle of a different song
            if offset > 5 and self._has_music_staffs_no_title(page):
                logger.warning(f"Found music without title at index {pdf_index} - may have missed '{song_title}'")
                break
        
        return None
    
    def _has_music_staffs_no_title(self, page: fitz.Page) -> bool:
        """
        Check if page has music staffs but no visible title.
        This is a heuristic to detect when we've gone too far.
        
        Args:
            page: PyMuPDF page
        
        Returns:
            True if page appears to have music but no title
        """
        # For now, just return False - we can implement this later if needed
        # A proper implementation would look for horizontal lines (staffs)
        # and check if the top 20% of the page is mostly empty
        return False
    
    def sample_entries(self, toc_entries: List[TOCEntry], sample_size: int = 3) -> List[TOCEntry]:
        """
        Select representative entries for sampling.
        
        Selects first, middle, last, and random entries to get good coverage.
        
        Args:
            toc_entries: List of TOC entries
            sample_size: Number of entries to sample (minimum 3)
        
        Returns:
            Subset of TOC entries
        """
        if not toc_entries:
            return []
        
        if len(toc_entries) <= sample_size:
            return toc_entries
        
        samples = []
        
        # Always include first entry
        samples.append(toc_entries[0])
        
        # Always include last entry
        samples.append(toc_entries[-1])
        
        # Include middle entry
        if len(toc_entries) > 2:
            mid_idx = len(toc_entries) // 2
            samples.append(toc_entries[mid_idx])
        
        # Add more samples if needed
        remaining = sample_size - len(samples)
        if remaining > 0 and len(toc_entries) > 3:
            # Sample evenly distributed entries
            step = len(toc_entries) // (remaining + 1)
            for i in range(1, remaining + 1):
                idx = i * step
                if idx < len(toc_entries) and toc_entries[idx] not in samples:
                    samples.append(toc_entries[idx])
        
        logger.info(f"Sampled {len(samples)} entries from {len(toc_entries)} total")
        return samples
    
    def find_matching_page(self, pdf_path: str, entry: TOCEntry, 
                          search_range: int = 3) -> Optional[int]:
        """
        Find the PDF page index that matches the TOC entry.
        
        Tries the expected page first, then searches ±N pages.
        
        Args:
            pdf_path: Path to PDF file
            entry: TOC entry to find
            search_range: Number of pages to search in each direction
        
        Returns:
            PDF page index (0-based) or None if not found
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            
            # Try different offset values
            for offset in [0, -1, -2, -3, 1, 2]:
                pdf_index = entry.page_number + offset
                
                if 0 <= pdf_index < total_pages:
                    if self.verify_page_match(doc, pdf_index, entry.song_title):
                        doc.close()
                        return pdf_index
            
            # If no match found with common offsets, search nearby pages
            for offset in range(-search_range, search_range + 1):
                pdf_index = entry.page_number + offset
                
                if 0 <= pdf_index < total_pages:
                    if self.verify_page_match(doc, pdf_index, entry.song_title):
                        doc.close()
                        return pdf_index
            
            doc.close()
            return None
            
        except Exception as e:
            logger.error(f"Error finding matching page: {e}")
            return None
    
    def verify_page_match(self, doc: fitz.Document, pdf_index: int, 
                         expected_title: str, threshold: float = 0.6) -> bool:
        """
        Check if page contains expected song title.
        
        Uses fuzzy string matching to handle OCR errors and formatting differences.
        For image-based PDFs, uses vision-based verification.
        
        Args:
            doc: PyMuPDF document
            pdf_index: PDF page index to check
            expected_title: Expected song title
            threshold: Minimum similarity score (0.0-1.0)
        
        Returns:
            True if title found on page
        """
        try:
            page = doc[pdf_index]
            
            # Extract text from top 30% of page (title area)
            page_rect = page.rect
            title_rect = fitz.Rect(
                page_rect.x0,
                page_rect.y0,
                page_rect.x1,
                page_rect.y0 + page_rect.height * 0.3
            )
            
            text = page.get_text("text", clip=title_rect)
            
            # If no text found and vision is enabled, use vision-based verification
            if not text.strip() and self.use_vision:
                logger.info(f"No text found on page {pdf_index}, using vision verification")
                return self._verify_page_match_vision(page, expected_title)
            
            # Normalize both texts
            expected_normalized = self._normalize_text(expected_title)
            page_normalized = self._normalize_text(text)
            
            # Check for exact match first
            if expected_normalized in page_normalized:
                return True
            
            # Use fuzzy matching
            similarity = self._calculate_similarity(expected_normalized, page_normalized)
            
            return similarity >= threshold
            
        except Exception as e:
            logger.error(f"Error verifying page match: {e}")
            return False
    
    def _verify_page_match_vision(self, page: fitz.Page, expected_title: str) -> bool:
        """
        Use Bedrock vision to verify if song title appears on page.
        
        Args:
            page: PyMuPDF page object
            expected_title: Expected song title
        
        Returns:
            True if title found on page
        """
        try:
            import base64
            import io
            from PIL import Image
            
            # Render page as image
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            # Construct prompt
            prompt = f"""Look at this sheet music page. Does the song title "{expected_title}" appear anywhere on this page?

The title might be:
- At the top of the page
- In various fonts or styles
- Part of a header or footer
- Abbreviated or slightly different

Answer with ONLY "YES" or "NO" - nothing else.

If you see "{expected_title}" or something very similar to it on the page, answer YES.
If you don't see it at all, answer NO."""

            # Call Bedrock
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
            
            body_json = json.dumps(request_body)
            
            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=body_json
            )
            
            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text'].strip().upper()
            
            result = response_text == "YES"
            logger.info(f"Vision verification for '{expected_title}': {response_text} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in vision verification: {e}")
            return False
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Uses SequenceMatcher for fuzzy matching.
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity score 0.0-1.0
        """
        # Check if text1 is a substring of text2
        if text1 in text2:
            return 1.0
        
        # Use SequenceMatcher for fuzzy matching
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def calculate_offset(self, samples: List[Tuple[int, int]]) -> OffsetModel:
        """
        Fit linear offset model from samples.
        
        Calculates: PDF_index = printed_page + offset
        
        Args:
            samples: List of (printed_page, pdf_index) tuples
        
        Returns:
            OffsetModel with offset value and confidence
        """
        if not samples:
            return OffsetModel(offset=0, confidence=0.0, samples_verified=0)
        
        # Calculate offset for each sample
        offsets = [pdf_idx - printed_page for printed_page, pdf_idx in samples]
        
        # Use median offset (robust to outliers)
        offsets.sort()
        median_offset = offsets[len(offsets) // 2]
        
        # Calculate consistency (how many samples agree with median ±1)
        consistent_samples = sum(1 for o in offsets if abs(o - median_offset) <= 1)
        confidence = consistent_samples / len(samples)
        
        logger.info(f"Calculated offset: {median_offset}, confidence: {confidence:.2f}, samples: {len(samples)}")
        
        return OffsetModel(
            offset=median_offset,
            confidence=confidence,
            samples_verified=len(samples)
        )
    
    def apply_mapping(self, toc_entries: List[TOCEntry], offset: int) -> List[SongLocation]:
        """
        Apply offset to all TOC entries.
        
        Args:
            toc_entries: List of TOC entries
            offset: Calculated offset value
        
        Returns:
            List of SongLocation with PDF page indices
        """
        song_locations = []
        
        for entry in toc_entries:
            pdf_index = entry.page_number + offset
            
            song_locations.append(SongLocation(
                song_title=entry.song_title,
                printed_page=entry.page_number,
                pdf_index=pdf_index,
                artist=entry.artist
            ))
        
        logger.info(f"Applied offset {offset} to {len(toc_entries)} entries")
        return song_locations
