"""
TOC Parser Service - Parses TOC text into structured song entries.

This module provides functions for:
- Deterministic regex-based parsing of TOC text
- Extracting per-song artist information for Various Artists books
- Validating TOC entries
"""

import re
from typing import List, Optional, Dict
import logging
from app.models import TOCEntry, TOCParseResult
from app.utils.artist_resolution import extract_artist_from_toc_entry

logger = logging.getLogger(__name__)


class TOCParser:
    """Service for parsing TOC text into structured entries."""
    
    def __init__(self, use_bedrock_fallback: bool = True, local_mode: bool = False):
        """
        Initialize TOC parser with regex patterns.
        
        Args:
            use_bedrock_fallback: Whether to use Bedrock as fallback
            local_mode: Whether to use mock Bedrock
        """
        self.use_bedrock_fallback = use_bedrock_fallback
        self.local_mode = local_mode
        # Pattern 1: "Song Title ... 42" or "Song Title .... 42"
        self.pattern1 = re.compile(r'^(.+?)\s*\.{2,}\s*(\d+)\s*$', re.MULTILINE)
        
        # Pattern 2: "42. Song Title" or "42 Song Title"
        self.pattern2 = re.compile(r'^(\d+)[\.\s]+([^\d].+?)\s*$', re.MULTILINE)
        
        # Pattern 3: "Song Title (Artist) ... 42"
        self.pattern3 = re.compile(r'^(.+?)\s*\(([^)]+)\)\s*\.{2,}\s*(\d+)\s*$', re.MULTILINE)
        
        # Pattern 4: "Song Title - Artist ... 42"
        self.pattern4 = re.compile(r'^(.+?)\s*-\s*([^-]+?)\s*\.{2,}\s*(\d+)\s*$', re.MULTILINE)
        
        # Pattern 5: "Song Title    42" (multiple spaces/tabs)
        self.pattern5 = re.compile(r'^(.+?)\s{3,}(\d+)\s*$', re.MULTILINE)
        
        logger.info("TOCParser initialized with 5 regex patterns")
    
    def parse_toc(self, toc_text: str, book_metadata: Optional[Dict] = None) -> TOCParseResult:
        """
        Parse TOC text into structured entries.
        
        Args:
            toc_text: Extracted text from TOC pages
            book_metadata: Optional metadata about the book (artist, name, etc.)
        
        Returns:
            TOCParseResult with parsed entries and metadata
        """
        logger.info("Starting TOC parsing")
        
        # Try deterministic parsing first
        entries = self.deterministic_parse(toc_text)
        
        if entries and len(entries) >= 10:
            # Deterministic parsing succeeded
            logger.info(f"Deterministic parsing succeeded with {len(entries)} entries")
            artist_overrides = self.extract_artist_overrides(entries)
            return TOCParseResult(
                entries=entries,
                extraction_method='deterministic',
                confidence=0.95,
                artist_overrides=artist_overrides
            )
        
        # Deterministic parsing failed or insufficient entries
        if entries:
            logger.warning(f"Deterministic parsing produced only {len(entries)} entries")
        else:
            logger.warning("Deterministic parsing produced no entries")
        
        # Try Bedrock fallback if enabled
        if self.use_bedrock_fallback:
            logger.info("Attempting Bedrock fallback parsing")
            from app.services.bedrock_parser import BedrockParserService
            
            bedrock_service = BedrockParserService(local_mode=self.local_mode)
            bedrock_result = bedrock_service.bedrock_fallback_parse(toc_text, book_metadata)
            
            # If Bedrock succeeded, return its result
            if bedrock_result.entries and len(bedrock_result.entries) >= 10:
                return bedrock_result
            
            # If Bedrock also failed, return best available result
            if bedrock_result.entries and len(bedrock_result.entries) > len(entries or []):
                return bedrock_result
        
        # Return deterministic result (even if insufficient)
        if entries:
            artist_overrides = self.extract_artist_overrides(entries)
            return TOCParseResult(
                entries=entries,
                extraction_method='deterministic',
                confidence=0.5,
                artist_overrides=artist_overrides
            )
        
        # Complete failure
        return TOCParseResult(
            entries=[],
            extraction_method='failed',
            confidence=0.0,
            artist_overrides={}
        )
    
    def deterministic_parse(self, text: str) -> Optional[List[TOCEntry]]:
        """
        Attempt regex-based parsing of TOC.
        
        Tries multiple patterns and returns the one with most matches.
        
        Args:
            text: TOC text to parse
        
        Returns:
            List of TOCEntry or None if parsing fails
        """
        if not text or len(text.strip()) < 10:
            return None
        
        all_results = []
        
        # Try Pattern 3 first (with artist in parentheses)
        results3 = self._try_pattern3(text)
        if results3:
            all_results.append(('pattern3', results3))
        
        # Try Pattern 4 (with artist after hyphen)
        results4 = self._try_pattern4(text)
        if results4:
            all_results.append(('pattern4', results4))
        
        # Try Pattern 1 (dots)
        results1 = self._try_pattern1(text)
        if results1:
            all_results.append(('pattern1', results1))
        
        # Try Pattern 5 (multiple spaces)
        results5 = self._try_pattern5(text)
        if results5:
            all_results.append(('pattern5', results5))
        
        # Try Pattern 2 (page number first)
        results2 = self._try_pattern2(text)
        if results2:
            all_results.append(('pattern2', results2))
        
        if not all_results:
            logger.warning("No patterns matched the TOC text")
            return None
        
        # Select the pattern with most matches
        best_pattern, best_results = max(all_results, key=lambda x: len(x[1]))
        logger.info(f"Selected {best_pattern} with {len(best_results)} matches")
        
        return best_results
    
    def _try_pattern1(self, text: str) -> List[TOCEntry]:
        """Try Pattern 1: 'Song Title ... 42'"""
        entries = []
        matches = self.pattern1.findall(text)
        
        for title, page_num in matches:
            title = title.strip()
            if self._is_valid_title(title):
                entries.append(TOCEntry(
                    song_title=title,
                    page_number=int(page_num),
                    confidence=0.95
                ))
        
        return entries
    
    def _try_pattern2(self, text: str) -> List[TOCEntry]:
        """Try Pattern 2: '42. Song Title'"""
        entries = []
        matches = self.pattern2.findall(text)
        
        for page_num, title in matches:
            title = title.strip()
            if self._is_valid_title(title):
                entries.append(TOCEntry(
                    song_title=title,
                    page_number=int(page_num),
                    confidence=0.90
                ))
        
        return entries
    
    def _try_pattern3(self, text: str) -> List[TOCEntry]:
        """Try Pattern 3: 'Song Title (Artist) ... 42'"""
        entries = []
        matches = self.pattern3.findall(text)
        
        for title, artist, page_num in matches:
            title = title.strip()
            artist = artist.strip()
            if self._is_valid_title(title):
                entries.append(TOCEntry(
                    song_title=title,
                    page_number=int(page_num),
                    artist=artist,
                    confidence=0.95
                ))
        
        return entries
    
    def _try_pattern4(self, text: str) -> List[TOCEntry]:
        """Try Pattern 4: 'Song Title - Artist ... 42'"""
        entries = []
        matches = self.pattern4.findall(text)
        
        for title, artist, page_num in matches:
            title = title.strip()
            artist = artist.strip()
            if self._is_valid_title(title) and self._is_valid_artist(artist):
                entries.append(TOCEntry(
                    song_title=title,
                    page_number=int(page_num),
                    artist=artist,
                    confidence=0.90
                ))
        
        return entries
    
    def _try_pattern5(self, text: str) -> List[TOCEntry]:
        """Try Pattern 5: 'Song Title    42' (multiple spaces)"""
        entries = []
        matches = self.pattern5.findall(text)
        
        for title, page_num in matches:
            title = title.strip()
            if self._is_valid_title(title):
                entries.append(TOCEntry(
                    song_title=title,
                    page_number=int(page_num),
                    confidence=0.85
                ))
        
        return entries
    
    def _is_valid_title(self, title: str) -> bool:
        """
        Check if a title looks valid.
        
        Args:
            title: Song title to validate
        
        Returns:
            True if title appears valid
        """
        if not title or len(title) < 1:  # Changed from < 2 to < 1
            return False
        
        # Filter out common TOC headers/footers
        title_lower = title.lower()
        invalid_keywords = [
            'contents', 'table of contents', 'index', 'page',
            'continued', 'chapter', 'section'
        ]
        
        if any(keyword in title_lower for keyword in invalid_keywords):
            return False
        
        # Title should have at least one letter
        if not re.search(r'[a-zA-Z]', title):
            return False
        
        return True
    
    def _is_valid_artist(self, artist: str) -> bool:
        """
        Check if an artist name looks valid.
        
        Args:
            artist: Artist name to validate
        
        Returns:
            True if artist appears valid
        """
        if not artist or len(artist) < 2:
            return False
        
        # Artist should have at least one letter
        if not re.search(r'[a-zA-Z]', artist):
            return False
        
        return True
    
    def extract_artist_overrides(self, entries: List[TOCEntry]) -> Dict[str, str]:
        """
        Extract per-song artist information for Various Artists books.
        
        Args:
            entries: List of TOC entries
        
        Returns:
            Dictionary mapping song_title to artist_name
        """
        artist_overrides = {}
        
        for entry in entries:
            if entry.artist:
                artist_overrides[entry.song_title] = entry.artist
            else:
                # Try to extract artist from title
                extracted_artist = extract_artist_from_toc_entry(entry.song_title)
                if extracted_artist:
                    artist_overrides[entry.song_title] = extracted_artist
        
        if artist_overrides:
            logger.info(f"Extracted {len(artist_overrides)} artist overrides")
        
        return artist_overrides



def validate_toc_entries(entries: List[TOCEntry], min_entries: int = 10) -> bool:
    """
    Validate TOC entries meet quality thresholds.
    
    Args:
        entries: List of TOC entries to validate
        min_entries: Minimum number of entries required
    
    Returns:
        True if entries are valid
    """
    if not entries:
        logger.warning("No TOC entries to validate")
        return False
    
    if len(entries) < min_entries:
        logger.warning(f"Only {len(entries)} entries found, minimum is {min_entries}")
        return False
    
    # Check that all entries have required fields
    for i, entry in enumerate(entries):
        if not entry.song_title or not entry.song_title.strip():
            logger.warning(f"Entry {i} has empty song title")
            return False
        
        if entry.page_number <= 0:
            logger.warning(f"Entry {i} has invalid page number: {entry.page_number}")
            return False
    
    # Check for duplicate page numbers (suspicious)
    page_numbers = [e.page_number for e in entries]
    if len(page_numbers) != len(set(page_numbers)):
        logger.warning("Duplicate page numbers found in TOC entries")
        # Don't fail, but log warning
    
    # Check that page numbers are generally increasing
    non_increasing = 0
    for i in range(1, len(entries)):
        if entries[i].page_number <= entries[i-1].page_number:
            non_increasing += 1
    
    if non_increasing > len(entries) * 0.3:  # More than 30% out of order
        logger.warning(f"{non_increasing} entries have non-increasing page numbers")
        return False
    
    logger.info(f"Validated {len(entries)} TOC entries successfully")
    return True
