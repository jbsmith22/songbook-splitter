"""
Holistic Page Analyzer - Improved page analysis with multi-phase approach.

Strategy:
1. Phase 1: Full Page Scan - Analyze EVERY page for content type and titles
2. Phase 2: TOC Matching - Match TOC entries to detected song starts
3. Phase 3: Offset Fallback - Use calculated offset for unmatched songs
4. Phase 4: Boundary Assignment - Assign all pages to songs sequentially

This approach gathers all data first, then makes decisions holistically,
rather than making per-song pass/fail decisions that lose context.
"""

import io
import json
import base64
import re
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from collections import Counter
import logging

logger = logging.getLogger(__name__)


@dataclass
class PageInfo:
    """Information about a single PDF page."""
    pdf_page: int  # 1-indexed
    printed_page: Optional[int] = None
    content_type: str = 'unknown'  # song_start, song_continuation, toc, cover, blank, photo, lyrics, credits, other
    detected_title: Optional[str] = None
    has_music_notation: bool = False
    confidence: float = 0.0
    raw_response: Optional[str] = None


@dataclass
class SongBoundary:
    """A song with its page boundaries."""
    title: str
    toc_page: Optional[int]  # From TOC (printed page number)
    start_pdf_page: int  # Actual PDF page (1-indexed)
    end_pdf_page: int  # Actual PDF page (1-indexed)
    page_count: int
    match_method: str  # 'direct_match', 'offset_fallback', 'toc_only'
    confidence: float
    artist: str = ''


@dataclass
class AnalysisResult:
    """Complete analysis result for a songbook."""
    book_id: str
    source_pdf_uri: str
    total_pages: int
    toc_song_count: int
    detected_song_count: int
    matched_song_count: int
    calculated_offset: int
    offset_confidence: float
    pages: List[PageInfo]
    songs: List[SongBoundary]
    analysis_timestamp: str
    warnings: List[str] = field(default_factory=list)


class HolisticPageAnalyzer:
    """
    Improved page analyzer that scans all pages first, then matches holistically.
    """

    # Model for vision analysis
    VISION_MODEL_ID = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'

    def __init__(self, bedrock_client=None):
        """
        Initialize analyzer.

        Args:
            bedrock_client: Boto3 Bedrock runtime client (optional, will create if not provided)
        """
        self.bedrock = bedrock_client
        if not self.bedrock:
            import boto3
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        logger.info("HolisticPageAnalyzer initialized")

    def analyze_book(self, pdf_path: str, book_id: str, source_pdf_uri: str,
                     toc_entries: List[Dict], artist: str = '') -> AnalysisResult:
        """
        Perform holistic page analysis on a songbook.

        Args:
            pdf_path: Local path to PDF file
            book_id: Book identifier
            source_pdf_uri: S3 URI of source
            toc_entries: List of TOC entries with song_title and page_number
            artist: Book-level artist name

        Returns:
            AnalysisResult with complete analysis
        """
        import fitz

        logger.info(f"Starting holistic analysis for {book_id}")
        logger.info(f"  TOC entries: {len(toc_entries)}")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        warnings = []

        # Sort TOC by page number
        sorted_toc = sorted(toc_entries, key=lambda x: x.get('page_number', 999))
        toc_titles = [t['song_title'] for t in sorted_toc]

        # ============================================
        # PHASE 1: Full Page Scan
        # ============================================
        logger.info(f"Phase 1: Scanning all {total_pages} pages...")
        pages = self._scan_all_pages(doc, toc_titles)

        # Count detected song starts
        song_starts = [p for p in pages if p.content_type == 'song_start']
        logger.info(f"  Detected {len(song_starts)} song_start pages")

        # ============================================
        # PHASE 2: Match TOC to Detected Song Starts
        # ============================================
        logger.info("Phase 2: Matching TOC entries to detected song starts...")
        matches, unmatched_toc, unmatched_starts = self._match_toc_to_pages(
            sorted_toc, song_starts
        )
        logger.info(f"  Direct matches: {len(matches)}")
        logger.info(f"  Unmatched TOC: {len(unmatched_toc)}")
        logger.info(f"  Unmatched starts: {len(unmatched_starts)}")

        # ============================================
        # PHASE 3: Calculate Offset & Fallback Matching
        # ============================================
        logger.info("Phase 3: Calculating offset and doing fallback matching...")
        offset, offset_confidence = self._calculate_offset(matches)
        logger.info(f"  Calculated offset: {offset} (confidence: {offset_confidence:.2f})")

        # Try to match remaining TOC entries using offset
        if unmatched_toc and offset_confidence > 0:
            fallback_matches = self._offset_fallback_matching(
                doc, pages, unmatched_toc, offset, toc_titles
            )
            matches.extend(fallback_matches)
            logger.info(f"  Fallback matches: {len(fallback_matches)}")

        # If still have unmatched TOC, add them with offset-calculated positions
        for toc_entry in unmatched_toc:
            toc_page = toc_entry['page_number']
            expected_pdf = toc_page + offset

            # Clamp to valid range
            expected_pdf = max(1, min(expected_pdf, total_pages))

            # Check if already matched
            already_matched = any(
                self._titles_match(m['toc_entry']['song_title'], toc_entry['song_title'])
                for m in matches
            )

            if not already_matched:
                matches.append({
                    'toc_entry': toc_entry,
                    'pdf_page': expected_pdf,
                    'method': 'toc_only',
                    'confidence': offset_confidence * 0.5  # Lower confidence
                })
                warnings.append(f"Song '{toc_entry['song_title']}' not directly verified, using offset calculation")

        # ============================================
        # PHASE 3b: Include Unmatched Detected Starts
        # ============================================
        # If we detected song starts that don't match any TOC entry,
        # include them as songs (handles incomplete/missing TOC)
        # BUT: Skip if a song with the same title already exists (prevents duplicates)
        if unmatched_starts:
            logger.info(f"Phase 3b: Including {len(unmatched_starts)} unmatched detected song starts...")
            for page_info in unmatched_starts:
                # Check if this page is already covered by a match
                already_covered = any(
                    m['pdf_page'] == page_info.pdf_page
                    for m in matches
                )

                # Check if a song with this title already exists (prevents duplicates!)
                title = page_info.detected_title or f"Song at Page {page_info.pdf_page}"
                title_already_exists = any(
                    self._titles_match(m['toc_entry']['song_title'], title)
                    for m in matches
                )

                if already_covered:
                    logger.debug(f"  Skipping page {page_info.pdf_page}: already covered")
                    continue

                if title_already_exists:
                    logger.info(f"  Skipping '{title}' at page {page_info.pdf_page}: title already exists in matches")
                    continue

                matches.append({
                    'toc_entry': {
                        'song_title': title,
                        'page_number': page_info.pdf_page  # Use PDF page as "TOC" page
                    },
                    'pdf_page': page_info.pdf_page,
                    'method': 'detected_only',
                    'confidence': page_info.confidence
                })
                warnings.append(f"Song '{title}' detected but not in TOC - included from page scan")

        # Sort matches by PDF page
        matches.sort(key=lambda m: m['pdf_page'])

        # ============================================
        # PHASE 4: Assign All Pages to Songs
        # ============================================
        logger.info("Phase 4: Assigning page boundaries...")
        songs = self._assign_page_boundaries(matches, total_pages, artist)
        logger.info(f"  Created {len(songs)} song boundaries")

        # ============================================
        # PHASE 5: Update Page Content Types
        # ============================================
        logger.info("Phase 5: Finalizing page classifications...")
        self._finalize_page_classifications(pages, songs)

        doc.close()

        result = AnalysisResult(
            book_id=book_id,
            source_pdf_uri=source_pdf_uri,
            total_pages=total_pages,
            toc_song_count=len(sorted_toc),
            detected_song_count=len(song_starts),
            matched_song_count=len(matches),
            calculated_offset=offset,
            offset_confidence=offset_confidence,
            pages=pages,
            songs=songs,
            analysis_timestamp=datetime.utcnow().isoformat() + 'Z',
            warnings=warnings
        )

        logger.info(f"Analysis complete: {len(songs)} songs, offset={offset}")
        return result

    def _scan_all_pages(self, doc, toc_titles: List[str]) -> List[PageInfo]:
        """
        Phase 1: Scan every page to detect content type and titles.
        """
        pages = []
        total = len(doc)

        # Build hint string for vision model
        titles_hint = ', '.join(toc_titles[:15])
        if len(toc_titles) > 15:
            titles_hint += '...'

        for i in range(total):
            pdf_page = i + 1  # 1-indexed

            try:
                page_info = self._analyze_single_page(doc, i, titles_hint)
                page_info.pdf_page = pdf_page
                pages.append(page_info)

                if pdf_page % 10 == 0:
                    logger.info(f"    Scanned page {pdf_page}/{total}")

            except Exception as e:
                logger.error(f"Error scanning page {pdf_page}: {e}")
                pages.append(PageInfo(
                    pdf_page=pdf_page,
                    content_type='error',
                    confidence=0.0
                ))

        return pages

    def _analyze_single_page(self, doc, page_idx: int, titles_hint: str) -> PageInfo:
        """
        Analyze a single page using vision.
        """
        page = doc[page_idx]

        # Render page as image (72 DPI to stay under size limits)
        pix = page.get_pixmap(dpi=72)
        img_bytes = pix.tobytes("png")

        # Check image size - reduce DPI if too large
        if len(img_bytes) > 4 * 1024 * 1024:  # 4MB
            pix = page.get_pixmap(dpi=50)
            img_bytes = pix.tobytes("png")

        image_b64 = base64.b64encode(img_bytes).decode('utf-8')

        prompt = f"""Analyze this sheet music page and respond with JSON only.

Songs in this book include: {titles_hint}

Determine:
1. "printed_page": The printed page number visible on this page (integer or null if not visible)
2. "content_type": One of:
   - "song_start" - FIRST page of a NEW song (see strict criteria below)
   - "song_continuation" - Continuation of a song (music notation continues from previous page)
   - "toc" - Table of contents
   - "cover" - Cover or title page
   - "blank" - Blank or nearly blank page
   - "photo" - Photo page with no music
   - "lyrics" - Lyrics only (no music notation)
   - "credits" - Credits, copyright, or info page
   - "other" - Anything else
3. "song_title": If this is a song_start page, the song title (string or null)
4. "has_music": true if page has music notation (staff lines with notes)

STRICT CRITERIA for "song_start":
- MUST have a LARGE, PROMINENT title at the TOP of the page (not small header text)
- MUST have music notation that BEGINS on this page (not continuing from previous)
- The music should start with measure 1 or a clear beginning
- If the title appears as small text in a header/footer, that's NOT song_start
- If the music continues mid-measure from the previous page, that's "song_continuation"
- When in doubt, prefer "song_continuation" over "song_start"

Respond with ONLY valid JSON:
{{"printed_page": <int|null>, "content_type": "<string>", "song_title": <string|null>, "has_music": <bool>}}"""

        try:
            response = self._call_vision(image_b64, prompt)
            return self._parse_page_response(response)
        except Exception as e:
            logger.warning(f"Vision error on page {page_idx + 1}: {e}")
            # Fallback: check if page has text
            text = page.get_text("text")
            has_content = len(text.strip()) > 50
            return PageInfo(
                content_type='other' if has_content else 'blank',
                has_music_notation=has_content,
                confidence=0.3
            )

    def _call_vision(self, image_b64: str, prompt: str) -> str:
        """Call Bedrock vision API."""
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0,
            "messages": [{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_b64
                        }
                    },
                    {"type": "text", "text": prompt}
                ]
            }]
        }

        response = self.bedrock.invoke_model(
            modelId=self.VISION_MODEL_ID,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

    def _parse_page_response(self, response: str) -> PageInfo:
        """Parse vision response into PageInfo."""
        try:
            # Extract JSON from response
            json_str = response.strip()
            if json_str.startswith('```'):
                json_str = json_str.split('```')[1]
                if json_str.startswith('json'):
                    json_str = json_str[4:]

            data = json.loads(json_str)

            return PageInfo(
                pdf_page=0,  # Will be set by caller
                printed_page=data.get('printed_page'),
                content_type=data.get('content_type', 'other'),
                detected_title=data.get('song_title'),
                has_music_notation=data.get('has_music', False),
                confidence=0.9,
                raw_response=response
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse response: {e}")
            return PageInfo(
                content_type='other',
                confidence=0.3,
                raw_response=response
            )

    def _match_toc_to_pages(self, toc_entries: List[Dict],
                           song_starts: List[PageInfo]) -> Tuple[List[Dict], List[Dict], List[PageInfo]]:
        """
        Phase 2: Match TOC entries to detected song_start pages.

        Returns:
            (matches, unmatched_toc, unmatched_starts)
        """
        matches = []
        unmatched_toc = list(toc_entries)
        unmatched_starts = list(song_starts)

        # First pass: exact title matches
        for toc_entry in list(unmatched_toc):
            toc_title = toc_entry['song_title']

            for page in list(unmatched_starts):
                if page.detected_title and self._titles_match(toc_title, page.detected_title):
                    matches.append({
                        'toc_entry': toc_entry,
                        'pdf_page': page.pdf_page,
                        'detected_title': page.detected_title,
                        'method': 'direct_match',
                        'confidence': 0.95
                    })
                    unmatched_toc.remove(toc_entry)
                    unmatched_starts.remove(page)
                    break

        return matches, unmatched_toc, unmatched_starts

    def _calculate_offset(self, matches: List[Dict]) -> Tuple[int, float]:
        """
        Calculate page offset from matches.

        offset = pdf_page - printed_page (from TOC)

        Returns:
            (offset, confidence)
        """
        if not matches:
            return 0, 0.0

        offsets = []
        for m in matches:
            toc_page = m['toc_entry']['page_number']
            pdf_page = m['pdf_page']
            offsets.append(pdf_page - toc_page)

        # Find most common offset
        offset_counts = Counter(offsets)
        most_common, count = offset_counts.most_common(1)[0]

        confidence = count / len(offsets)

        return most_common, confidence

    def _offset_fallback_matching(self, doc, pages: List[PageInfo],
                                  unmatched_toc: List[Dict], offset: int,
                                  all_toc_titles: List[str]) -> List[Dict]:
        """
        Phase 3: Try to match remaining TOC entries using calculated offset.

        For each unmatched TOC entry, look at the expected PDF page and do
        a focused check to see if it could be that song.
        """
        fallback_matches = []
        total_pages = len(doc)

        titles_hint = ', '.join(all_toc_titles[:10])

        for toc_entry in list(unmatched_toc):
            toc_page = toc_entry['page_number']
            expected_pdf = toc_page + offset

            # Clamp to valid range
            if expected_pdf < 1 or expected_pdf > total_pages:
                continue

            # Check pages around expected location
            for check_offset in [0, -1, 1, -2, 2]:
                check_pdf = expected_pdf + check_offset
                if check_pdf < 1 or check_pdf > total_pages:
                    continue

                page_idx = check_pdf - 1

                # Do a focused verification
                is_match = self._verify_song_at_page(
                    doc, page_idx, toc_entry['song_title'], titles_hint
                )

                if is_match:
                    fallback_matches.append({
                        'toc_entry': toc_entry,
                        'pdf_page': check_pdf,
                        'detected_title': toc_entry['song_title'],
                        'method': 'offset_fallback',
                        'confidence': 0.8 if check_offset == 0 else 0.7
                    })
                    unmatched_toc.remove(toc_entry)

                    # Update the page info
                    pages[page_idx].content_type = 'song_start'
                    pages[page_idx].detected_title = toc_entry['song_title']
                    break

        return fallback_matches

    def _verify_song_at_page(self, doc, page_idx: int, expected_title: str,
                             titles_hint: str) -> bool:
        """
        Focused verification: is this page plausibly the start of the expected song?

        More lenient than Phase 1 - we're checking if it COULD be this song,
        not requiring high confidence.
        """
        page = doc[page_idx]

        # Render page
        pix = page.get_pixmap(dpi=72)
        img_bytes = pix.tobytes("png")
        image_b64 = base64.b64encode(img_bytes).decode('utf-8')

        prompt = f"""Look at this sheet music page. Could this be the first page of the song "{expected_title}"?

This is from a songbook with songs: {titles_hint}

Consider:
1. Does it have a title that matches or is similar to "{expected_title}"?
2. Does it have music notation (staff lines with notes)?
3. Does it look like the START of a song (not a continuation)?

Answer YES if this could plausibly be the first page of "{expected_title}".
Answer NO if it's clearly NOT the start of this song.

When in doubt, answer YES - we'll verify later.

Answer with ONLY "YES" or "NO"."""

        try:
            response = self._call_vision(image_b64, prompt)
            answer = response.strip().upper()
            return answer.startswith('YES')
        except Exception as e:
            logger.warning(f"Verification error: {e}")
            return False

    def _assign_page_boundaries(self, matches: List[Dict], total_pages: int,
                                artist: str) -> List[SongBoundary]:
        """
        Phase 4: Assign page boundaries to each song.

        Each song runs from its start page to the page before the next song starts.
        The last song runs to the end of the document.

        Also merges consecutive matches with the same title (duplicate detection cleanup).
        """
        if not matches:
            return []

        # First, deduplicate consecutive matches with same title
        deduped_matches = []
        for match in matches:
            title = match['toc_entry']['song_title']

            # Check if previous match has the same title
            if deduped_matches:
                prev_title = deduped_matches[-1]['toc_entry']['song_title']
                if self._titles_match(title, prev_title):
                    # Skip this duplicate - the previous entry will extend to cover it
                    logger.info(f"Merging duplicate '{title}' at page {match['pdf_page']} with previous entry")
                    continue

            deduped_matches.append(match)

        songs = []

        for i, match in enumerate(deduped_matches):
            start_page = match['pdf_page']

            # End page is one before next song, or end of document
            if i < len(deduped_matches) - 1:
                end_page = deduped_matches[i + 1]['pdf_page'] - 1
            else:
                end_page = total_pages

            # Sanity check
            end_page = max(start_page, end_page)

            songs.append(SongBoundary(
                title=match['toc_entry']['song_title'],
                toc_page=match['toc_entry']['page_number'],
                start_pdf_page=start_page,
                end_pdf_page=end_page,
                page_count=end_page - start_page + 1,
                match_method=match['method'],
                confidence=match['confidence'],
                artist=artist
            ))

        return songs

    def _finalize_page_classifications(self, pages: List[PageInfo],
                                       songs: List[SongBoundary]) -> None:
        """
        Phase 5: Update page content types based on final song assignments.

        Pages that are part of a song but not song_start should be song_continuation.
        """
        for song in songs:
            for pdf_page in range(song.start_pdf_page, song.end_pdf_page + 1):
                page_idx = pdf_page - 1
                if page_idx < 0 or page_idx >= len(pages):
                    continue

                page = pages[page_idx]

                if pdf_page == song.start_pdf_page:
                    # First page should be song_start
                    if page.content_type != 'song_start':
                        page.content_type = 'song_start'
                        page.detected_title = song.title
                else:
                    # Other pages in song
                    if page.content_type in ('unknown', 'other', 'blank'):
                        page.content_type = 'song_continuation'
                    # Keep photo, lyrics, etc. as-is - they're part of the song

    def _titles_match(self, title1: str, title2: str) -> bool:
        """Check if two song titles match (fuzzy)."""
        def normalize(s):
            s = s.lower()
            s = re.sub(r'[^\w\s]', '', s)
            s = ' '.join(s.split())
            return s

        n1, n2 = normalize(title1), normalize(title2)

        # Exact match
        if n1 == n2:
            return True

        # One contains the other
        if n1 in n2 or n2 in n1:
            return True

        # Word overlap (for longer titles)
        words1 = set(n1.split())
        words2 = set(n2.split())
        significant1 = {w for w in words1 if len(w) > 2}
        significant2 = {w for w in words2 if len(w) > 2}

        if significant1 and significant2:
            overlap = len(significant1 & significant2) / max(len(significant1), len(significant2))
            if overlap >= 0.7:
                return True

        return False

    def to_dict(self, result: AnalysisResult) -> Dict[str, Any]:
        """Convert AnalysisResult to dictionary for JSON serialization."""
        return {
            'book_id': result.book_id,
            'source_pdf_uri': result.source_pdf_uri,
            'total_pages': result.total_pages,
            'total_pdf_pages': result.total_pages,  # Alias for viewer compatibility
            'toc_song_count': result.toc_song_count,
            'detected_song_count': result.detected_song_count,
            'matched_song_count': result.matched_song_count,
            'calculated_offset': result.calculated_offset,
            'offset_confidence': result.offset_confidence,
            'page_offset': {  # Viewer-compatible format
                'calculated_offset': result.calculated_offset,
                'is_consistent': result.offset_confidence > 0.8
            },
            'analysis_timestamp': result.analysis_timestamp,
            'warnings': result.warnings,
            'pages': [asdict(p) for p in result.pages],
            'songs': [
                {
                    'title': s.title,
                    'start_pdf_page': s.start_pdf_page,
                    'end_pdf_page': s.end_pdf_page,
                    'actual_pdf_start': s.start_pdf_page,  # Viewer-compatible alias
                    'actual_pdf_end': s.end_pdf_page,  # Viewer-compatible alias
                    'toc_page': s.toc_page,
                    'toc_printed_page': s.toc_page,  # Viewer-compatible alias
                    'page_count': s.page_count,
                    'match_method': s.match_method,
                    'confidence': s.confidence,
                    'artist': s.artist,
                    'verified': s.match_method in ('direct_match', 'detected_only')
                }
                for s in result.songs
            ]
        }
