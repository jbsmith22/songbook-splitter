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
        self.bedrock_runtime = None
        
        if use_vision:
            try:
                import boto3
                self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
                logger.info("PageMapperService initialized with vision support")
            except Exception as e:
                logger.error(f"CRITICAL: Could not initialize Bedrock client: {e}")
                raise RuntimeError(f"Vision support required but Bedrock initialization failed: {e}")
        else:
            logger.info("PageMapperService initialized without vision support")
    
    def build_page_mapping(self, pdf_path: str, toc_entries: List[TOCEntry], 
                          sample_size: int = 3, book_artist: str = "", book_name: str = "") -> PageMapping:
        """
        Calculate page mapping by pre-rendering all pages and finding songs using vision.
        
        This approach:
        1. Pre-renders ALL pages to PNG upfront (one-time cost)
        2. Stores them in memory for efficient access
        3. Uses vision to find each song's actual start page
        4. No on-demand rendering - everything is prepared first
        
        If no TOC entries provided, falls back to scanning entire PDF for song starts.
        
        Args:
            pdf_path: Path to PDF file
            toc_entries: List of TOC entries with printed page numbers (sorted)
            sample_size: Number of entries to sample for verification (unused, kept for compatibility)
            book_artist: Book-level artist (performer) - used as default for single-artist books
            book_name: Book name - used to determine if this is a Various Artists collection
        
        Returns:
            PageMapping with song locations
        """
        logger.info(f"=== BUILD_PAGE_MAPPING CALLED ===")
        logger.info(f"PDF path: {pdf_path}")
        logger.info(f"TOC entries count: {len(toc_entries)}")
        logger.info(f"Book artist: '{book_artist}'")
        logger.info(f"Book name: '{book_name}'")
        logger.info(f"Vision enabled: {self.use_vision}")
        logger.info(f"Building page mapping for {len(toc_entries)} TOC entries using vision verification")
        
        # Determine if this is a Various Artists or special collection book
        is_various_artists = self._is_various_artists_book(book_artist, book_name)
        logger.info(f"Is Various Artists book: {is_various_artists}")
        
        if not toc_entries:
            logger.warning("=== NO TOC ENTRIES - TRIGGERING FALLBACK TO FULL PDF SCAN ===")
            return self._scan_pdf_for_songs(pdf_path, toc_entries_for_reference=[], 
                                           book_artist=book_artist, is_various_artists=is_various_artists)
        
        # Sort entries by page number to ensure correct order
        sorted_entries = sorted(toc_entries, key=lambda e: e.page_number)
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # STEP 1: Pre-render ALL pages to PNG
        logger.info(f"Pre-rendering all {total_pages} pages to PNG...")
        page_images = self._render_all_pages(doc)
        logger.info(f"Pre-rendering complete. {len(page_images)} pages ready.")
        
        # STEP 2: Find each song using pre-rendered images
        song_locations = []
        verified_count = 0
        search_start = 0  # Start searching from beginning
        
        for i, entry in enumerate(sorted_entries):
            logger.info(f"Finding '{entry.song_title}' (TOC page {entry.page_number})...")
            
            # Calculate expected PDF index based on initial offset (if we have one)
            if i > 0 and song_locations:  # Only use previous location if we have one
                # For subsequent songs, start from expected position
                prev_location = song_locations[-1]
                toc_page_diff = entry.page_number - sorted_entries[i-1].page_number
                expected_pdf_index = prev_location.pdf_index + toc_page_diff
                # Start search a bit before expected position to account for offset variations
                search_start = max(0, expected_pdf_index - 2)
            else:
                # For first song or if no previous songs found, search from beginning
                search_start = 0
            
            # Find the song using pre-rendered images
            actual_pdf_index = self._find_song_in_images(
                page_images, 
                entry.song_title, 
                search_start, 
                total_pages
            )
            
            if actual_pdf_index is None:
                logger.warning(f"Could not find '{entry.song_title}' - skipping")
                continue
            
            # Determine artist based on book type
            if is_various_artists:
                # For Various Artists books, use TOC artist or extract from page
                artist = entry.artist
                if not artist:
                    logger.info(f"TOC artist missing for '{entry.song_title}', extracting from page {actual_pdf_index}")
                    if actual_pdf_index < len(page_images):
                        song_info = self._detect_song_start(page_images[actual_pdf_index])
                        if song_info:
                            _, vision_artist = song_info
                            artist = vision_artist if vision_artist else "Unknown Artist"
                            logger.info(f"Extracted artist from page: '{artist}'")
                        else:
                            artist = "Unknown Artist"
                            logger.warning(f"Could not extract artist from page for '{entry.song_title}'")
                    else:
                        artist = "Unknown Artist"
            else:
                # For single-artist books, ALWAYS use the book-level artist
                artist = book_artist if book_artist else "Unknown Artist"
                logger.info(f"Using book-level artist '{artist}' for '{entry.song_title}'")
            
            song_locations.append(SongLocation(
                song_title=entry.song_title,
                printed_page=entry.page_number,
                pdf_index=actual_pdf_index,
                artist=artist
            ))
            
            verified_count += 1
            
            if i == 0:
                offset = actual_pdf_index - entry.page_number
                logger.info(f"Found first song '{entry.song_title}' at PDF index {actual_pdf_index} (TOC page {entry.page_number}, offset={offset})")
            else:
                offset_from_expected = actual_pdf_index - expected_pdf_index
                logger.info(f"Found '{entry.song_title}' at PDF index {actual_pdf_index} (expected {expected_pdf_index}, offset={offset_from_expected:+d})")
            
            # Next search starts after this song
            search_start = actual_pdf_index + 1
        
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
    
    def _render_all_pages(self, doc: fitz.Document, save_to_disk: bool = True, output_dir: str = "/tmp/page_images") -> List[bytes]:
        """
        Pre-render all pages of the PDF to PNG images.
        
        This is done upfront as a one-time cost, allowing efficient
        searching through the document without re-rendering pages.
        
        Ensures images stay under Bedrock's 5MB limit by:
        - Starting at 72 DPI
        - Reducing DPI if image exceeds 5MB
        - Compressing with PIL if still too large
        
        Args:
            doc: PyMuPDF document
            save_to_disk: If True, save PNG files to disk for debugging
            output_dir: Directory to save PNG files
        
        Returns:
            List of PNG image bytes, one per page
        """
        import os
        from PIL import Image
        import io
        
        page_images = []
        total_pages = len(doc)
        MAX_SIZE = 5 * 1024 * 1024  # 5MB in bytes
        
        # Create output directory if saving to disk
        if save_to_disk:
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"Saving PNG files to {output_dir}")
        
        for i in range(total_pages):
            try:
                page = doc[i]
                
                # Try rendering at different DPIs until we get under 5MB
                for dpi in [72, 60, 50, 40]:
                    pix = page.get_pixmap(dpi=dpi)
                    img_bytes = pix.tobytes("png")
                    
                    if len(img_bytes) < MAX_SIZE:
                        # Image is under limit, use it
                        break
                    
                    if dpi == 40:
                        # Even at lowest DPI, still too large - compress with PIL
                        logger.warning(f"Page {i} still {len(img_bytes)} bytes at 40 DPI, compressing...")
                        img = Image.open(io.BytesIO(img_bytes))
                        
                        # Convert to RGB if needed (remove alpha channel)
                        if img.mode in ('RGBA', 'LA', 'P'):
                            img = img.convert('RGB')
                        
                        # Compress with quality reduction
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=85, optimize=True)
                        img_bytes = output.getvalue()
                        
                        if len(img_bytes) >= MAX_SIZE:
                            logger.error(f"Page {i} still {len(img_bytes)} bytes after compression, using anyway")
                
                page_images.append(img_bytes)
                
                # Save to disk if requested
                if save_to_disk:
                    png_path = os.path.join(output_dir, f"page_{i:03d}.png")
                    with open(png_path, 'wb') as f:
                        f.write(img_bytes)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Rendered {i + 1}/{total_pages} pages...")
            except Exception as e:
                logger.error(f"Error rendering page {i}: {e}")
                # Add empty bytes as placeholder
                page_images.append(b'')
        
        if save_to_disk:
            logger.info(f"All {total_pages} PNG files saved to {output_dir}")
        
        return page_images
    
    def _find_song_in_images(self, page_images: List[bytes], song_title: str, 
                            start_index: int, total_pages: int) -> Optional[int]:
        """
        Search through pre-rendered images to find a page with the given song title.
        
        Args:
            page_images: List of pre-rendered PNG image bytes
            song_title: Song title to find
            start_index: PDF index to start searching from
            total_pages: Total pages in document
        
        Returns:
            PDF index where song starts, or None if not found
        """
        for pdf_index in range(start_index, total_pages):
            if pdf_index >= len(page_images):
                break
            
            img_bytes = page_images[pdf_index]
            if not img_bytes:
                continue
            
            # Check if this page has the song title using vision
            if self._verify_image_match(img_bytes, song_title):
                return pdf_index
        
        return None
    
    def _verify_image_match(self, img_bytes: bytes, expected_title: str) -> bool:
        """
        Use Bedrock vision to verify if this is the first page of a song.
        
        Args:
            img_bytes: PNG image bytes
            expected_title: Expected song title
        
        Returns:
            True if this is the first page of the song
        """
        if not self.use_vision:
            return False
        
        try:
            import base64
            import io
            from PIL import Image
            
            # Load image from bytes
            img = Image.open(io.BytesIO(img_bytes))
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            # Construct prompt
            prompt = f"""Look at this sheet music page. Is this the FIRST PAGE of the song "{expected_title}"?

A song's first page has:
- The song title "{expected_title}" prominently displayed at the top
- Music staffs with notes (actual sheet music)
- Usually has the artist name

This is NOT a song start if:
- It's just a title page with no music
- The text appears as lyrics within the music (not as a title)
- It's a continuation page of another song

Answer with ONLY "YES" or "NO" - nothing else.

If this is the first page of the song "{expected_title}" with music, answer YES.
Otherwise, answer NO."""

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
            logger.debug(f"Vision verification for '{expected_title}': {response_text} -> {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error in vision verification: {e}")
            return False
    
    def _is_various_artists_book(self, book_artist: str, book_name: str) -> bool:
        """
        Determine if this is a Various Artists or special collection book.
        
        Args:
            book_artist: Book-level artist name
            book_name: Book name
        
        Returns:
            True if this is a Various Artists or special collection
        """
        # Normalize for comparison
        artist_lower = book_artist.lower() if book_artist else ""
        name_lower = book_name.lower() if book_name else ""
        
        # Check for Various Artists indicators
        various_indicators = [
            "various artists",
            "various",
            "compilation",
            "fake book",
            "fakebook",
            "broadway",
            "movie",
            "tv",
            "television",
            "soundtrack",
            "collection"
        ]
        
        for indicator in various_indicators:
            if indicator in artist_lower or indicator in name_lower:
                return True
        
        return False
    
    def _scan_pdf_for_songs(self, pdf_path: str, toc_entries_for_reference: List[TOCEntry] = None,
                           book_artist: str = "", is_various_artists: bool = False) -> PageMapping:
        """
        Scan entire PDF to find song starts when no TOC is available.
        
        Uses vision to detect pages that are the first page of a song.
        If TOC entries are provided (even if incomplete), uses them to get artist names.
        
        Args:
            pdf_path: Path to PDF file
            toc_entries_for_reference: Optional TOC entries to use for artist name lookup
            book_artist: Book-level artist (performer) - used as default for single-artist books
            is_various_artists: Whether this is a Various Artists or special collection book
        
        Returns:
            PageMapping with detected song locations
        """
        logger.info("=== _SCAN_PDF_FOR_SONGS CALLED ===")
        logger.info(f"PDF path: {pdf_path}")
        logger.info(f"Vision enabled: {self.use_vision}")
        logger.info(f"Book artist: '{book_artist}'")
        logger.info(f"Is Various Artists: {is_various_artists}")
        logger.info(f"TOC entries for reference: {len(toc_entries_for_reference) if toc_entries_for_reference else 0}")
        logger.info("Scanning entire PDF for song starts (no TOC available)")
        
        if not self.use_vision:
            logger.error("CRITICAL: Vision is disabled but _scan_pdf_for_songs requires vision!")
            return PageMapping(offset=0, confidence=0.0, samples_verified=0, song_locations=[])
        
        # Build a lookup map from song title to artist from TOC entries
        toc_artist_map = {}
        if toc_entries_for_reference:
            for entry in toc_entries_for_reference:
                # Normalize song title for matching
                normalized_title = self._normalize_text(entry.song_title)
                toc_artist_map[normalized_title] = entry.artist
            logger.info(f"Built TOC artist lookup map with {len(toc_artist_map)} entries")
        
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        
        # Pre-render all pages
        logger.info(f"Pre-rendering all {total_pages} pages to PNG...")
        page_images = self._render_all_pages(doc)
        logger.info(f"Pre-rendering complete. {len(page_images)} pages ready.")
        
        # Scan each page to detect song starts
        song_locations = []
        
        for pdf_index in range(total_pages):
            if pdf_index >= len(page_images):
                break
            
            img_bytes = page_images[pdf_index]
            if not img_bytes:
                continue
            
            # Check if this is a song start page
            song_info = self._detect_song_start(img_bytes)
            
            if song_info:
                song_title, vision_artist = song_info
                
                # Determine artist based on book type
                if is_various_artists:
                    # For Various Artists books, try TOC first, then vision, then Unknown
                    normalized_title = self._normalize_text(song_title)
                    toc_artist = toc_artist_map.get(normalized_title)
                    
                    if toc_artist:
                        artist = toc_artist
                        logger.info(f"Found song start at PDF index {pdf_index}: '{song_title}' by {artist} (from TOC)")
                    else:
                        artist = vision_artist if vision_artist else "Unknown Artist"
                        logger.info(f"Found song start at PDF index {pdf_index}: '{song_title}' by {artist} (from vision)")
                else:
                    # For single-artist books, ALWAYS use the book-level artist
                    artist = book_artist if book_artist else "Unknown Artist"
                    logger.info(f"Found song start at PDF index {pdf_index}: '{song_title}' by {artist} (book-level artist)")
                
                song_locations.append(SongLocation(
                    song_title=song_title,
                    printed_page=pdf_index,  # Use PDF index as printed page when no TOC
                    pdf_index=pdf_index,
                    artist=artist
                ))
        
        doc.close()
        
        confidence = 1.0 if song_locations else 0.0
        
        logger.info(f"PDF scan complete: found {len(song_locations)} songs")
        
        return PageMapping(
            offset=0,  # No offset when scanning directly
            confidence=confidence,
            samples_verified=len(song_locations),
            song_locations=song_locations
        )
    
    def _detect_song_start(self, img_bytes: bytes) -> Optional[Tuple[str, str]]:
        """
        Use Bedrock vision to detect if this is a song start page and extract title/artist.
        
        Args:
            img_bytes: PNG image bytes
        
        Returns:
            Tuple of (song_title, artist) if this is a song start, None otherwise
        """
        if not self.use_vision:
            return None
        
        try:
            import base64
            import io
            from PIL import Image
            
            # Load image from bytes
            img = Image.open(io.BytesIO(img_bytes))
            
            # Convert to base64
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            image_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
            
            # Construct prompt
            prompt = """Look at this sheet music page. Is this the FIRST PAGE of a song?

A song's first page has:
- A song title prominently displayed at the top
- Music staffs with notes (actual sheet music)
- Usually has the artist name

This is NOT a song start if:
- It's just a title page with no music
- It's a table of contents
- The text appears as lyrics within the music (not as a title)
- It's a continuation page of another song

If this IS the first page of a song, respond with:
SONG: <song title>
ARTIST: <artist name>

If this is NOT the first page of a song, respond with:
NO

Examples:
- If you see "ALONE" at the top with music and "Heart" as artist: "SONG: Alone\nARTIST: Heart"
- If you see a table of contents: "NO"
- If you see a title page with no music: "NO"
- If you see music but no clear title at top: "NO"
"""

            # Call Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 100,
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
            response_text = response_body['content'][0]['text'].strip()
            
            # Parse response
            if response_text.upper() == "NO":
                return None
            
            # Extract song title and artist
            song_title = None
            artist = None
            
            for line in response_text.split('\n'):
                line = line.strip()
                if line.startswith('SONG:'):
                    song_title = line[5:].strip()
                elif line.startswith('ARTIST:'):
                    artist = line[7:].strip()
            
            if song_title:
                artist = artist or "Unknown Artist"
                logger.debug(f"Detected song start: '{song_title}' by {artist}")
                return (song_title, artist)
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting song start: {e}")
            return None
    
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
            prompt = f"""Look at this sheet music page. Is this the FIRST PAGE of the song "{expected_title}"?

A song's first page has:
- The song title "{expected_title}" prominently displayed at the top
- Music staffs with notes (actual sheet music)
- Usually has the artist name

This is NOT a song start if:
- It's just a title page with no music
- The text appears as lyrics within the music (not as a title)
- It's a continuation page of another song

Answer with ONLY "YES" or "NO" - nothing else.

If this is the first page of the song "{expected_title}" with music, answer YES.
Otherwise, answer NO."""

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
