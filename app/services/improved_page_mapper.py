"""
Improved Page Mapper Service - Uses all available data sources for accurate mapping.

This improved mapper:
1. Uses page_analysis.json detected song starts as PRIMARY source
2. Cross-references with TOC entries for metadata
3. Verifies each expected song start with strict vision prompts
4. Searches nearby pages if song not found at expected location
5. Never gives false positives - prefers "not found" over wrong match
"""

import re
import json
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
import logging
import fitz  # PyMuPDF
from difflib import SequenceMatcher
from app.models import TOCEntry, SongLocation, PageMapping

logger = logging.getLogger(__name__)


@dataclass
class DetectedSong:
    """A song detected from page_analysis.json."""
    song_title: str
    pdf_page: int
    printed_page: Optional[int]
    confidence: float


class ImprovedPageMapperService:
    """
    Improved service for mapping songs to PDF pages.

    Uses multiple data sources in priority order:
    1. page_analysis.json - detected song starts from vision scan
    2. TOC entries - for metadata and fallback
    3. Vision verification - to confirm each mapping
    """

    def __init__(self):
        """Initialize the improved page mapper."""
        self.bedrock_runtime = None
        try:
            import boto3
            self.bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
            logger.info("ImprovedPageMapperService initialized with Bedrock")
        except Exception as e:
            logger.error(f"Could not initialize Bedrock: {e}")
            raise

    def build_page_mapping_from_analysis(
        self,
        pdf_path: str,
        page_analysis: Dict,
        toc_entries: List[TOCEntry],
        book_artist: str = "",
        book_name: str = "",
        verify_each: bool = True
    ) -> PageMapping:
        """
        Build page mapping using page_analysis data as primary source.

        Args:
            pdf_path: Path to PDF file
            page_analysis: Loaded page_analysis.json data
            toc_entries: TOC entries (for metadata)
            book_artist: Book-level artist
            book_name: Book name
            verify_each: If True, verify each song start with vision

        Returns:
            PageMapping with verified song locations
        """
        logger.info("=== IMPROVED PAGE MAPPING ===")
        logger.info(f"Using page_analysis with {len(page_analysis.get('pages', []))} pages")
        logger.info(f"TOC entries: {len(toc_entries)}")
        logger.info(f"Book artist: '{book_artist}'")

        # Step 1: Extract detected songs from page_analysis
        detected_songs = self._extract_detected_songs(page_analysis)
        logger.info(f"Detected {len(detected_songs)} song starts from page_analysis")

        # Step 2: Build TOC lookup for metadata
        toc_lookup = self._build_toc_lookup(toc_entries)
        logger.info(f"Built TOC lookup with {len(toc_lookup)} entries")

        # Step 3: Open PDF for verification
        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        # Step 4: Build song locations from detected songs
        song_locations = []
        verified_count = 0

        for detected in detected_songs:
            # Get metadata from TOC if available
            toc_entry = self._find_matching_toc_entry(detected.song_title, toc_lookup)

            printed_page = detected.printed_page
            if toc_entry and not printed_page:
                printed_page = toc_entry.page_number

            artist = book_artist
            if toc_entry and toc_entry.artist:
                artist = toc_entry.artist

            # Verify the song start if requested
            verified = True
            actual_pdf_page = detected.pdf_page

            if verify_each:
                logger.info(f"Verifying '{detected.song_title}' at PDF page {detected.pdf_page}...")

                # Strict verification
                is_correct = self._strict_verify_song_start(
                    doc, detected.pdf_page, detected.song_title
                )

                if is_correct:
                    logger.info(f"  ✓ Verified '{detected.song_title}' at page {detected.pdf_page}")
                    verified_count += 1
                else:
                    # Search nearby pages
                    logger.warning(f"  ✗ Song not verified at expected page, searching nearby...")
                    found_page = self._search_for_song(
                        doc, detected.song_title, detected.pdf_page, search_range=5
                    )

                    if found_page is not None:
                        logger.info(f"  ✓ Found '{detected.song_title}' at page {found_page} (was {detected.pdf_page})")
                        actual_pdf_page = found_page
                        verified_count += 1
                    else:
                        logger.error(f"  ✗ Could not verify '{detected.song_title}' - skipping")
                        verified = False

            if verified:
                song_locations.append(SongLocation(
                    song_title=detected.song_title,
                    printed_page=printed_page or actual_pdf_page,
                    pdf_index=actual_pdf_page,
                    artist=artist
                ))

        doc.close()

        # Step 5: Check for TOC entries not found in page_analysis
        detected_titles = {self._normalize_title(d.song_title) for d in detected_songs}
        missing_from_analysis = []

        for toc_entry in toc_entries:
            norm_title = self._normalize_title(toc_entry.song_title)
            if norm_title not in detected_titles:
                missing_from_analysis.append(toc_entry)

        if missing_from_analysis:
            logger.warning(f"TOC entries not found in page_analysis: {[e.song_title for e in missing_from_analysis]}")

        # Calculate confidence
        total_expected = len(detected_songs)
        confidence = verified_count / total_expected if total_expected > 0 else 0.0

        logger.info(f"=== PAGE MAPPING COMPLETE ===")
        logger.info(f"Verified: {verified_count}/{total_expected} songs")
        logger.info(f"Confidence: {confidence:.2%}")

        # Sort by PDF page
        song_locations.sort(key=lambda x: x.pdf_index)

        return PageMapping(
            offset=0,  # Not using simple offset model
            confidence=confidence,
            samples_verified=verified_count,
            song_locations=song_locations
        )

    def _extract_detected_songs(self, page_analysis: Dict) -> List[DetectedSong]:
        """Extract detected song starts from page_analysis data.

        NOTE: page_analysis uses 1-based page numbers.
        We convert to 0-based index for PyMuPDF compatibility.
        """
        songs = []

        for page in page_analysis.get('pages', []):
            if page.get('content_type') == 'song_start':
                song_titles = page.get('song_titles', [])
                if song_titles:
                    # Convert from 1-based (page_analysis) to 0-based (PyMuPDF)
                    pdf_index = page['pdf_page'] - 1
                    songs.append(DetectedSong(
                        song_title=song_titles[0],
                        pdf_page=pdf_index,  # Now 0-based
                        printed_page=page.get('printed_page'),
                        confidence=page.get('confidence', 0.9)
                    ))

        return songs

    def _build_toc_lookup(self, toc_entries: List[TOCEntry]) -> Dict[str, TOCEntry]:
        """Build a lookup dictionary from TOC entries."""
        lookup = {}
        for entry in toc_entries:
            norm_title = self._normalize_title(entry.song_title)
            lookup[norm_title] = entry
        return lookup

    def _find_matching_toc_entry(self, song_title: str, toc_lookup: Dict[str, TOCEntry]) -> Optional[TOCEntry]:
        """Find matching TOC entry for a song title."""
        norm_title = self._normalize_title(song_title)

        # Exact match
        if norm_title in toc_lookup:
            return toc_lookup[norm_title]

        # Fuzzy match
        best_match = None
        best_score = 0.0

        for toc_title, entry in toc_lookup.items():
            score = SequenceMatcher(None, norm_title, toc_title).ratio()
            if score > best_score and score > 0.8:
                best_score = score
                best_match = entry

        return best_match

    def _normalize_title(self, title: str) -> str:
        """Normalize song title for comparison."""
        title = title.lower()
        title = re.sub(r'[^\w\s]', '', title)
        title = ' '.join(title.split())
        return title

    def _strict_verify_song_start(self, doc: fitz.Document, pdf_page: int, expected_title: str) -> bool:
        """
        Strictly verify that a page is the first page of a specific song.

        Uses a strict prompt that requires:
        - Exact title match at top of page
        - Music notation present
        - This being the FIRST page (not a continuation)

        Returns False if uncertain - prefers false negatives over false positives.
        """
        if pdf_page < 0 or pdf_page >= len(doc):
            return False

        try:
            import base64
            import io
            from PIL import Image

            # Render page
            page = doc[pdf_page]
            pix = page.get_pixmap(dpi=100)
            img_bytes = pix.tobytes("png")

            # Convert to base64
            image_base64 = base64.b64encode(img_bytes).decode('utf-8')

            # STRICT verification prompt
            prompt = f"""Look at this sheet music page carefully. I need you to verify if this is the FIRST PAGE of the song "{expected_title}".

REQUIREMENTS for a YES answer (ALL must be true):
1. The song title "{expected_title}" must appear prominently at the TOP of the page
2. The page must contain actual sheet music (musical staffs with notes)
3. This must be the BEGINNING of the song, not a continuation page

IMPORTANT:
- The title must be a close match to "{expected_title}" (minor spelling differences OK)
- If you see a different song title, answer NO
- If this is a table of contents, cover page, or photo page, answer NO
- If this appears to be a middle or end page of a song (no title at top), answer NO
- When in doubt, answer NO

Answer ONLY "YES" or "NO" - nothing else."""

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

            response = self.bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps(request_body)
            )

            response_body = json.loads(response['body'].read())
            response_text = response_body['content'][0]['text'].strip().upper()

            result = response_text == "YES"
            logger.debug(f"Strict verify '{expected_title}' at page {pdf_page}: {response_text}")
            return result

        except Exception as e:
            logger.error(f"Error in strict verification: {e}")
            return False

    def _search_for_song(
        self,
        doc: fitz.Document,
        song_title: str,
        expected_page: int,
        search_range: int = 5
    ) -> Optional[int]:
        """
        Search for a song within a range of pages around the expected location.

        Args:
            doc: PyMuPDF document
            song_title: Song title to find
            expected_page: Expected PDF page
            search_range: Pages to search in each direction

        Returns:
            PDF page number if found, None otherwise
        """
        # Search in order: expected, +1, -1, +2, -2, etc.
        search_order = [expected_page]
        for offset in range(1, search_range + 1):
            if expected_page + offset < len(doc):
                search_order.append(expected_page + offset)
            if expected_page - offset >= 0:
                search_order.append(expected_page - offset)

        for page_num in search_order:
            if page_num == expected_page:
                continue  # Already checked

            if self._strict_verify_song_start(doc, page_num, song_title):
                return page_num

        return None

    def build_page_mapping_fallback(
        self,
        pdf_path: str,
        toc_entries: List[TOCEntry],
        book_artist: str = "",
        book_name: str = ""
    ) -> PageMapping:
        """
        Fallback page mapping when page_analysis is not available.

        Scans the PDF to find each TOC entry using vision verification.

        Args:
            pdf_path: Path to PDF file
            toc_entries: TOC entries to locate
            book_artist: Book-level artist
            book_name: Book name

        Returns:
            PageMapping with located songs
        """
        logger.info("=== FALLBACK PAGE MAPPING (no page_analysis) ===")
        logger.info(f"Searching for {len(toc_entries)} TOC entries")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        song_locations = []
        verified_count = 0

        # Sort TOC entries by page number
        sorted_entries = sorted(toc_entries, key=lambda e: e.page_number)

        # Search for each song
        last_found_page = 0

        for entry in sorted_entries:
            # Start search from last found page
            search_start = max(0, last_found_page)

            found_page = None

            # Search forward from last position
            for page_num in range(search_start, min(search_start + 30, total_pages)):
                if self._strict_verify_song_start(doc, page_num, entry.song_title):
                    found_page = page_num
                    break

            if found_page is not None:
                logger.info(f"Found '{entry.song_title}' at page {found_page}")
                last_found_page = found_page + 1
                verified_count += 1

                artist = entry.artist if entry.artist else book_artist

                song_locations.append(SongLocation(
                    song_title=entry.song_title,
                    printed_page=entry.page_number,
                    pdf_index=found_page,
                    artist=artist
                ))
            else:
                logger.warning(f"Could not find '{entry.song_title}'")

        doc.close()

        confidence = verified_count / len(toc_entries) if toc_entries else 0.0

        logger.info(f"Fallback mapping complete: {verified_count}/{len(toc_entries)} songs found")

        return PageMapping(
            offset=0,
            confidence=confidence,
            samples_verified=verified_count,
            song_locations=song_locations
        )
