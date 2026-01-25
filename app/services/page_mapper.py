"""
Page Mapper Service - Maps printed page numbers from TOC to actual PDF page indices.

This module provides functions for:
- Sampling TOC entries for verification
- Verifying page matches using fuzzy string matching
- Calculating offset between printed pages and PDF indices
- Applying mapping to all TOC entries
"""

import re
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
    
    def __init__(self):
        """Initialize page mapper service."""
        logger.info("PageMapperService initialized")
    
    def build_page_mapping(self, pdf_path: str, toc_entries: List[TOCEntry], 
                          sample_size: int = 3) -> PageMapping:
        """
        Calculate offset between printed pages and PDF indices.
        
        Args:
            pdf_path: Path to PDF file
            toc_entries: List of TOC entries with printed page numbers
            sample_size: Number of entries to sample for verification
        
        Returns:
            PageMapping with offset and song locations
        """
        logger.info(f"Building page mapping for {len(toc_entries)} TOC entries")
        
        # Sample entries for verification
        sampled_entries = self.sample_entries(toc_entries, sample_size)
        
        # Verify each sample and collect (printed_page, pdf_index) pairs
        verified_samples = []
        for entry in sampled_entries:
            pdf_index = self.find_matching_page(pdf_path, entry)
            if pdf_index is not None:
                verified_samples.append((entry.page_number, pdf_index))
                logger.info(f"Verified '{entry.song_title}': printed page {entry.page_number} -> PDF index {pdf_index}")
            else:
                logger.warning(f"Could not verify '{entry.song_title}' at printed page {entry.page_number}")
        
        if not verified_samples:
            logger.error("No samples could be verified")
            # Return default mapping with offset=0
            return PageMapping(
                offset=0,
                confidence=0.0,
                samples_verified=0,
                song_locations=self.apply_mapping(toc_entries, 0)
            )
        
        # Calculate offset
        offset_model = self.calculate_offset(verified_samples)
        
        # Apply mapping to all entries
        song_locations = self.apply_mapping(toc_entries, offset_model.offset)
        
        return PageMapping(
            offset=offset_model.offset,
            confidence=offset_model.confidence,
            samples_verified=offset_model.samples_verified,
            song_locations=song_locations
        )
    
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
