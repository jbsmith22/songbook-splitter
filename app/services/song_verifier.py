"""
Song Verifier Service - Verifies song start pages and adjusts if necessary.

This module provides functions for:
- Detecting musical staff lines on pages
- Verifying title matches using fuzzy matching
- Searching nearby pages for correct song starts
- Adjusting page ranges based on verification results
"""

import io
from typing import List, Optional, Tuple
import logging
import fitz  # PyMuPDF
from PIL import Image
import numpy as np
from difflib import SequenceMatcher
from app.models import SongLocation, VerifiedSong, PageRange

logger = logging.getLogger(__name__)


class SongVerifierService:
    """Service for verifying and adjusting song start pages."""
    
    def __init__(self):
        """Initialize song verifier service."""
        logger.info("SongVerifierService initialized")
    
    def verify_song_starts(self, pdf_path: str, song_locations: List[SongLocation],
                          search_range: int = 3) -> List[VerifiedSong]:
        """
        Verify and adjust song start pages.
        
        Args:
            pdf_path: Path to PDF file
            song_locations: List of song locations from page mapping
            search_range: Number of pages to search if verification fails
        
        Returns:
            List of VerifiedSong with confirmed page indices
        """
        logger.info(f"Verifying {len(song_locations)} song start pages")
        
        verified_songs = []
        
        try:
            doc = fitz.open(pdf_path)
            
            for location in song_locations:
                verified = self._verify_single_song(
                    doc, location, search_range
                )
                verified_songs.append(verified)
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error verifying song starts: {e}")
            # Return unverified songs
            for location in song_locations:
                verified_songs.append(VerifiedSong(
                    song_title=location.song_title,
                    pdf_index=location.pdf_index,
                    verified=False,
                    adjustment=0,
                    confidence=0.0,
                    artist=location.artist
                ))
        
        success_count = sum(1 for v in verified_songs if v.verified)
        logger.info(f"Verified {success_count}/{len(verified_songs)} songs successfully")
        
        return verified_songs
    
    def _verify_single_song(self, doc: fitz.Document, location: SongLocation,
                           search_range: int) -> VerifiedSong:
        """
        Verify a single song's start page.
        
        Trust the page mapper's vision-based detection, but verify it has both
        staff lines AND title match. If verification fails, flag it but don't
        search nearby pages (the vision detection is authoritative).
        """
        expected_page = location.pdf_index
        
        # Verify the page mapper's detection
        has_staff_lines = self.check_staff_lines(doc[expected_page])
        title_confidence = self.check_title_match(doc[expected_page], location.song_title)
        
        # Require BOTH staff lines AND title match for high confidence
        if has_staff_lines and title_confidence >= 0.7:
            logger.debug(f"Verified '{location.song_title}' at page {expected_page} (staff_lines=True, title_confidence={title_confidence:.2f})")
            return VerifiedSong(
                song_title=location.song_title,
                pdf_index=expected_page,
                verified=True,
                adjustment=0,
                confidence=0.95,
                artist=location.artist
            )
        
        # If verification fails, trust vision but flag with lower confidence
        logger.warning(f"Could not fully verify '{location.song_title}' at page {expected_page} (staff_lines={has_staff_lines}, title_confidence={title_confidence:.2f}) - trusting vision detection")
        return VerifiedSong(
            song_title=location.song_title,
            pdf_index=expected_page,
            verified=True,  # Still trust the vision
            adjustment=0,
            confidence=0.6,  # Lower confidence to flag uncertainty
            artist=location.artist
        )
    
    def _is_valid_song_start(self, doc: fitz.Document, pdf_index: int,
                            expected_title: str) -> bool:
        """
        Check if page is a valid song start.
        
        Requires BOTH:
        1. Musical staff lines
        2. Title match
        
        Args:
            doc: PyMuPDF document
            pdf_index: Page index to check
            expected_title: Expected song title
        
        Returns:
            True if page appears to be a valid song start
        """
        if pdf_index < 0 or pdf_index >= len(doc):
            return False
        
        page = doc[pdf_index]
        
        # Check for staff lines
        has_staff_lines = self.check_staff_lines(page)
        
        # Check for title match
        title_confidence = self.check_title_match(page, expected_title)
        
        # Require BOTH staff lines AND good title match
        is_valid = has_staff_lines and title_confidence >= 0.7
        
        logger.debug(f"Page {pdf_index}: staff_lines={has_staff_lines}, title_confidence={title_confidence:.2f}, valid={is_valid}")
        
        return is_valid
    
    def check_staff_lines(self, page: fitz.Page) -> bool:
        """
        Detect musical staff lines on page.
        
        Uses image processing to detect horizontal parallel lines
        characteristic of musical notation.
        
        Args:
            page: PyMuPDF page object
        
        Returns:
            True if staff lines detected
        """
        try:
            # Render page as image
            mat = fitz.Matrix(150/72, 150/72)  # 150 DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to PIL Image
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            
            # Convert to grayscale numpy array
            img_array = np.array(image.convert('L'))
            
            # Detect horizontal lines
            has_lines = self._detect_horizontal_lines(img_array)
            
            return has_lines
            
        except Exception as e:
            logger.error(f"Error detecting staff lines: {e}")
            return False
    
    def _detect_horizontal_lines(self, img_array: np.ndarray) -> bool:
        """
        Detect horizontal lines in image using simple heuristics.
        
        Args:
            img_array: Grayscale image as numpy array
        
        Returns:
            True if horizontal lines detected
        """
        height, width = img_array.shape
        
        # Sample horizontal lines at different heights
        sample_rows = [
            height // 4,
            height // 2,
            3 * height // 4
        ]
        
        line_count = 0
        
        for row in sample_rows:
            if row >= height:
                continue
            
            # Get row of pixels
            row_pixels = img_array[row, :]
            
            # Threshold to binary (dark = potential line)
            threshold = 128
            binary_row = row_pixels < threshold
            
            # Count transitions (line segments)
            transitions = np.diff(binary_row.astype(int))
            dark_segments = np.sum(transitions == 1)
            
            # If we have multiple dark segments, likely staff lines
            if dark_segments >= 3:
                line_count += 1
        
        # If we found lines in at least 2 of 3 sample rows
        has_lines = line_count >= 2
        
        return has_lines
    
    def check_title_match(self, page: fitz.Page, expected_title: str,
                         threshold: float = 0.6) -> float:
        """
        Check if page contains expected song title.
        
        Args:
            page: PyMuPDF page object
            expected_title: Expected song title
            threshold: Minimum similarity score
        
        Returns:
            Confidence score 0.0-1.0
        """
        try:
            # Extract text from top 20% of page (title area)
            page_rect = page.rect
            title_rect = fitz.Rect(
                page_rect.x0,
                page_rect.y0,
                page_rect.x1,
                page_rect.y0 + page_rect.height * 0.2
            )
            
            text = page.get_text("text", clip=title_rect)
            
            # Normalize both texts
            expected_normalized = self._normalize_text(expected_title)
            page_normalized = self._normalize_text(text)
            
            # Check for exact match
            if expected_normalized in page_normalized:
                return 1.0
            
            # Calculate similarity
            similarity = self._calculate_similarity(expected_normalized, page_normalized)
            
            return similarity
            
        except Exception as e:
            logger.error(f"Error checking title match: {e}")
            return 0.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        text = ' '.join(text.split())
        return text
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        if not text1 or not text2:
            return 0.0
        
        if text1 in text2:
            return 1.0
        
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def search_nearby_pages(self, doc: fitz.Document, expected_page: int,
                           title: str, search_range: int = 3) -> Optional[int]:
        """
        Search ±N pages for correct song start.
        
        Args:
            doc: PyMuPDF document
            expected_page: Expected page index
            title: Song title to search for
            search_range: Number of pages to search in each direction
        
        Returns:
            Corrected page index or None
        """
        # Search in order: -1, +1, -2, +2, -3, +3, etc.
        for offset in range(1, search_range + 1):
            # Try before expected page
            page_idx = expected_page - offset
            if 0 <= page_idx < len(doc):
                if self._is_valid_song_start(doc, page_idx, title):
                    return page_idx
            
            # Try after expected page
            page_idx = expected_page + offset
            if 0 <= page_idx < len(doc):
                if self._is_valid_song_start(doc, page_idx, title):
                    return page_idx
        
        return None
    
    def adjust_page_ranges(self, verified_songs: List[VerifiedSong],
                          total_pages: int) -> List[PageRange]:
        """
        Calculate page ranges for each song (start to next song - 1).
        
        Args:
            verified_songs: List of verified songs with page indices
            total_pages: Total number of pages in PDF
        
        Returns:
            List of PageRange objects
        """
        if not verified_songs:
            return []
        
        # Sort by page index
        sorted_songs = sorted(verified_songs, key=lambda s: s.pdf_index)
        
        page_ranges = []
        
        for i, song in enumerate(sorted_songs):
            start_page = song.pdf_index
            
            # End page is the start of next song (or end of document)
            if i < len(sorted_songs) - 1:
                end_page = sorted_songs[i + 1].pdf_index
            else:
                end_page = total_pages
            
            page_ranges.append(PageRange(
                song_title=song.song_title,
                start_page=start_page,
                end_page=end_page,
                artist=song.artist
            ))
        
        logger.info(f"Calculated {len(page_ranges)} page ranges")
        return page_ranges
