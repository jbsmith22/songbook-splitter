"""
Page Analyzer Service - Comprehensive page-by-page analysis of songbook PDFs.

This module provides:
- Bedrock Claude vision analysis of each page
- Song title detection with position information
- Printed page number detection
- Page offset calculation and consistency checking
- Content type classification (cover, TOC, song_start, song_continuation, etc.)

The output is stored as page_analysis.json artifact for use by the manual split editor.
"""

import io
import json
import base64
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import fitz  # PyMuPDF
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class PageAnalysis:
    """Analysis results for a single PDF page."""
    pdf_page: int  # 1-indexed PDF page number
    printed_page: Optional[int]  # Printed page number if detected, None otherwise
    content_type: str  # 'cover', 'toc', 'song_start', 'song_continuation', 'blank', 'other'
    has_music_notation: bool
    song_titles: List[str]  # Song titles found on this page (usually 0 or 1)
    confidence: float
    raw_response: Optional[str] = None  # For debugging


@dataclass
class CalibrationPoint:
    """A single calibration point for page offset calculation."""
    pdf_page: int
    printed_page: int
    song_title: str
    method: str  # 'title_match', 'page_number_detection'


@dataclass
class PageOffset:
    """Page offset calculation results."""
    calculated_offset: int  # printed_page = pdf_page + offset
    is_consistent: bool  # True if offset is constant throughout book
    confidence: float
    calibration_points: List[CalibrationPoint]


@dataclass
class SongBoundary:
    """Calculated song boundaries."""
    title: str
    toc_printed_page: int  # From TOC
    actual_pdf_start: int  # Calculated PDF page
    actual_pdf_end: int  # Calculated PDF page
    page_count: int
    verified: bool


@dataclass
class PageAnalysisResult:
    """Complete page analysis for a songbook."""
    book_id: str
    analysis_timestamp: str
    source_pdf_uri: str
    total_pdf_pages: int
    page_offset: PageOffset
    pages: List[PageAnalysis]
    songs: List[SongBoundary]


class PageAnalyzerService:
    """Service for comprehensive page-by-page analysis using Bedrock vision."""

    # Use Claude 3.5 Sonnet for vision - update model ID as needed
    # Note: AWS may require an inference profile ARN instead of direct model ID
    DEFAULT_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'  # Fallback to 3 Sonnet
    VISION_MODEL_ID = 'us.anthropic.claude-3-5-sonnet-20241022-v2:0'  # Cross-region inference profile

    def __init__(self, local_mode: bool = False, model_id: Optional[str] = None):
        """
        Initialize page analyzer service.

        Args:
            local_mode: If True, use mock responses
            model_id: Override model ID (can be inference profile ARN)
        """
        self.local_mode = local_mode
        self.model_id = model_id or self.VISION_MODEL_ID

        if not local_mode:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        logger.info(f"PageAnalyzerService initialized (local_mode={local_mode}, model={self.model_id})")

    def analyze_book(self, pdf_path: str, book_id: str, source_pdf_uri: str,
                     toc_entries: List[Dict], max_pages: Optional[int] = None) -> PageAnalysisResult:
        """
        Perform comprehensive page analysis on a songbook PDF.

        Args:
            pdf_path: Local path to PDF file
            book_id: Book identifier
            source_pdf_uri: S3 URI of source PDF
            toc_entries: List of TOC entries with song_title and page_number
            max_pages: Maximum pages to analyze (None for all)

        Returns:
            PageAnalysisResult with complete analysis
        """
        logger.info(f"Starting page analysis for {book_id}")

        doc = fitz.open(pdf_path)
        total_pages = len(doc)

        if max_pages:
            pages_to_analyze = min(max_pages, total_pages)
        else:
            pages_to_analyze = total_pages

        logger.info(f"Analyzing {pages_to_analyze} of {total_pages} pages")

        # Sort TOC entries by page number
        sorted_toc = sorted(toc_entries, key=lambda x: x.get('page_number', 999))

        # Phase 1: Analyze pages to find song titles and page numbers
        page_analyses = []
        calibration_points = []

        for pdf_page in range(1, pages_to_analyze + 1):
            try:
                analysis = self._analyze_single_page(doc, pdf_page, sorted_toc)
                page_analyses.append(analysis)

                # Collect calibration points
                if analysis.song_titles and analysis.printed_page:
                    for title in analysis.song_titles:
                        # Find matching TOC entry
                        toc_match = next(
                            (t for t in sorted_toc if self._titles_match(t['song_title'], title)),
                            None
                        )
                        if toc_match:
                            calibration_points.append(CalibrationPoint(
                                pdf_page=pdf_page,
                                printed_page=analysis.printed_page,
                                song_title=title,
                                method='title_match'
                            ))

                if pdf_page % 10 == 0:
                    logger.info(f"  Analyzed page {pdf_page}/{pages_to_analyze}")

            except Exception as e:
                logger.error(f"Error analyzing page {pdf_page}: {e}")
                page_analyses.append(PageAnalysis(
                    pdf_page=pdf_page,
                    printed_page=None,
                    content_type='error',
                    has_music_notation=False,
                    song_titles=[],
                    confidence=0.0
                ))

        doc.close()

        # Phase 2: Calculate page offset
        page_offset = self._calculate_page_offset(calibration_points, sorted_toc, page_analyses)

        # Phase 3: Calculate song boundaries using offset
        song_boundaries = self._calculate_song_boundaries(sorted_toc, page_offset, total_pages)

        result = PageAnalysisResult(
            book_id=book_id,
            analysis_timestamp=datetime.utcnow().isoformat() + 'Z',
            source_pdf_uri=source_pdf_uri,
            total_pdf_pages=total_pages,
            page_offset=page_offset,
            pages=page_analyses,
            songs=song_boundaries
        )

        logger.info(f"Page analysis complete: {len(page_analyses)} pages, {len(song_boundaries)} songs, offset={page_offset.calculated_offset}")

        return result

    def _analyze_single_page(self, doc: fitz.Document, pdf_page: int,
                             toc_entries: List[Dict]) -> PageAnalysis:
        """Analyze a single page using Bedrock vision."""

        # Render page as image
        page = doc[pdf_page - 1]  # fitz is 0-indexed
        zoom = 150 / 72  # 150 DPI
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")

        if self.local_mode:
            # Return mock analysis
            return self._mock_analyze_page(pdf_page)

        # Encode image
        image_b64 = base64.b64encode(png_bytes).decode('utf-8')

        # Build list of song titles to look for (from TOC)
        toc_titles = [t['song_title'] for t in toc_entries[:20]]  # First 20 songs
        titles_hint = ', '.join(toc_titles[:10])

        # Construct prompt for Claude vision
        prompt = f"""Analyze this sheet music page and provide the following information in JSON format:

1. "printed_page": The printed page number shown on this page (usually in a corner). Return null if not visible.
2. "content_type": One of: "cover", "toc", "song_start", "song_continuation", "blank", "credits", "other"
3. "has_music_notation": true if this page contains musical staff/notation
4. "song_titles": Array of song title(s) that START on this page (empty if no new song starts)

Context: This is from a songbook. Songs in this book include: {titles_hint}...

IMPORTANT:
- A "song_start" page has a prominent song title at the top AND is the FIRST page of that song
- "song_continuation" pages have music but no new song title header
- Only include song titles that appear as HEADERS/TITLES, not in lyrics

Return ONLY valid JSON, no other text:
{{"printed_page": <int or null>, "content_type": "<string>", "has_music_notation": <bool>, "song_titles": [<strings>]}}"""

        try:
            response = self._invoke_bedrock_vision(image_b64, prompt)
            return self._parse_page_analysis(pdf_page, response)
        except Exception as e:
            logger.error(f"Bedrock vision error on page {pdf_page}: {e}")
            # Fall back to basic analysis
            return self._fallback_analyze_page(page, pdf_page)

    def _invoke_bedrock_vision(self, image_b64: str, prompt: str) -> str:
        """Invoke Bedrock Claude with vision."""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
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
            modelId=self.model_id,
            body=json.dumps(request_body)
        )

        response_body = json.loads(response['body'].read())
        return response_body['content'][0]['text']

    def _parse_page_analysis(self, pdf_page: int, response: str) -> PageAnalysis:
        """Parse Bedrock response into PageAnalysis."""
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response.strip()
            if json_str.startswith('```'):
                json_str = json_str.split('```')[1]
                if json_str.startswith('json'):
                    json_str = json_str[4:]

            data = json.loads(json_str)

            return PageAnalysis(
                pdf_page=pdf_page,
                printed_page=data.get('printed_page'),
                content_type=data.get('content_type', 'other'),
                has_music_notation=data.get('has_music_notation', False),
                song_titles=data.get('song_titles', []),
                confidence=0.9,
                raw_response=response
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse response for page {pdf_page}: {e}")
            return PageAnalysis(
                pdf_page=pdf_page,
                printed_page=None,
                content_type='other',
                has_music_notation=False,
                song_titles=[],
                confidence=0.3,
                raw_response=response
            )

    def _fallback_analyze_page(self, page: fitz.Page, pdf_page: int) -> PageAnalysis:
        """Basic analysis without Bedrock (text extraction only)."""
        text = page.get_text("text")
        has_text = len(text.strip()) > 50

        return PageAnalysis(
            pdf_page=pdf_page,
            printed_page=None,
            content_type='other' if has_text else 'blank',
            has_music_notation=has_text,  # Assume pages with text have music
            song_titles=[],
            confidence=0.3
        )

    def _mock_analyze_page(self, pdf_page: int) -> PageAnalysis:
        """Mock analysis for local testing."""
        # Simulate: first 3 pages are front matter, then songs every 4-5 pages
        if pdf_page <= 3:
            return PageAnalysis(
                pdf_page=pdf_page,
                printed_page=None,
                content_type='front_matter',
                has_music_notation=False,
                song_titles=[],
                confidence=0.8
            )
        elif (pdf_page - 4) % 5 == 0:
            song_num = (pdf_page - 4) // 5 + 1
            return PageAnalysis(
                pdf_page=pdf_page,
                printed_page=pdf_page + 5,  # Mock offset of 5
                content_type='song_start',
                has_music_notation=True,
                song_titles=[f'Mock Song {song_num}'],
                confidence=0.8
            )
        else:
            return PageAnalysis(
                pdf_page=pdf_page,
                printed_page=pdf_page + 5,
                content_type='song_continuation',
                has_music_notation=True,
                song_titles=[],
                confidence=0.8
            )

    def _titles_match(self, title1: str, title2: str) -> bool:
        """Check if two song titles match (fuzzy)."""
        import re

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

        # Word overlap
        words1 = set(n1.split())
        words2 = set(n2.split())
        significant1 = {w for w in words1 if len(w) > 2}
        significant2 = {w for w in words2 if len(w) > 2}

        if significant1 and significant2:
            overlap = len(significant1 & significant2) / max(len(significant1), len(significant2))
            return overlap >= 0.7

        return False

    def _calculate_page_offset(self, calibration_points: List[CalibrationPoint],
                               toc_entries: List[Dict],
                               page_analyses: List[PageAnalysis]) -> PageOffset:
        """Calculate page offset from calibration points."""

        if not calibration_points:
            # Try to infer from song title matches in page analyses
            for analysis in page_analyses:
                if analysis.song_titles and analysis.content_type == 'song_start':
                    for title in analysis.song_titles:
                        toc_match = next(
                            (t for t in toc_entries if self._titles_match(t['song_title'], title)),
                            None
                        )
                        if toc_match:
                            offset = toc_match['page_number'] - analysis.pdf_page
                            calibration_points.append(CalibrationPoint(
                                pdf_page=analysis.pdf_page,
                                printed_page=toc_match['page_number'],
                                song_title=title,
                                method='toc_title_match'
                            ))

        if not calibration_points:
            logger.warning("No calibration points found, using offset 0")
            return PageOffset(
                calculated_offset=0,
                is_consistent=False,
                confidence=0.0,
                calibration_points=[]
            )

        # Calculate offsets from each calibration point
        offsets = [cp.printed_page - cp.pdf_page for cp in calibration_points]

        # Find most common offset
        from collections import Counter
        offset_counts = Counter(offsets)
        most_common_offset, count = offset_counts.most_common(1)[0]

        # Check consistency
        is_consistent = len(set(offsets)) == 1
        if not is_consistent:
            logger.warning(f"Offset varies: {offset_counts}")

        confidence = count / len(calibration_points)

        return PageOffset(
            calculated_offset=most_common_offset,
            is_consistent=is_consistent,
            confidence=confidence,
            calibration_points=calibration_points
        )

    def _calculate_song_boundaries(self, toc_entries: List[Dict],
                                   page_offset: PageOffset,
                                   total_pages: int) -> List[SongBoundary]:
        """Calculate song boundaries using TOC and offset."""

        boundaries = []
        sorted_toc = sorted(toc_entries, key=lambda x: x.get('page_number', 999))

        for i, entry in enumerate(sorted_toc):
            toc_page = entry['page_number']
            pdf_start = toc_page - page_offset.calculated_offset

            # End page is start of next song - 1
            if i < len(sorted_toc) - 1:
                next_toc_page = sorted_toc[i + 1]['page_number']
                pdf_end = (next_toc_page - page_offset.calculated_offset) - 1
            else:
                # Last song goes to end of document
                pdf_end = total_pages

            # Sanity checks
            pdf_start = max(1, min(pdf_start, total_pages))
            pdf_end = max(pdf_start, min(pdf_end, total_pages))

            boundaries.append(SongBoundary(
                title=entry['song_title'],
                toc_printed_page=toc_page,
                actual_pdf_start=pdf_start,
                actual_pdf_end=pdf_end,
                page_count=pdf_end - pdf_start + 1,
                verified=page_offset.confidence >= 0.7
            ))

        return boundaries

    def to_dict(self, result: PageAnalysisResult) -> Dict[str, Any]:
        """Convert PageAnalysisResult to dictionary for JSON serialization."""
        return {
            'book_id': result.book_id,
            'analysis_timestamp': result.analysis_timestamp,
            'source_pdf_uri': result.source_pdf_uri,
            'total_pdf_pages': result.total_pdf_pages,
            'page_offset': {
                'calculated_offset': result.page_offset.calculated_offset,
                'is_consistent': result.page_offset.is_consistent,
                'confidence': result.page_offset.confidence,
                'calibration_points': [asdict(cp) for cp in result.page_offset.calibration_points]
            },
            'pages': [asdict(p) for p in result.pages],
            'songs': [asdict(s) for s in result.songs]
        }


# Lambda handler for Step Functions integration
def page_analysis_handler(event, context):
    """
    Lambda handler for page analysis step.

    Input event:
        - book_id: Book identifier
        - source_pdf_uri: S3 URI of source PDF
        - toc_entries: List of TOC entries from toc_parse.json

    Output:
        - page_analysis_uri: S3 URI of page_analysis.json
        - page_offset: Calculated offset
        - songs_found: Number of songs with calculated boundaries
    """
    import tempfile
    import os

    book_id = event.get('book_id')
    source_pdf_uri = event.get('source_pdf_uri')
    toc_entries = event.get('toc_entries', [])

    logger.info(f"Page analysis handler started for {book_id}")

    # Download PDF from S3
    s3 = boto3.client('s3')
    bucket, key = source_pdf_uri.replace('s3://', '').split('/', 1)

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        s3.download_file(bucket, key, tmp.name)
        pdf_path = tmp.name

    try:
        # Run analysis
        analyzer = PageAnalyzerService(local_mode=False)
        result = analyzer.analyze_book(
            pdf_path=pdf_path,
            book_id=book_id,
            source_pdf_uri=source_pdf_uri,
            toc_entries=toc_entries
        )

        # Save to S3
        output_bucket = os.environ.get('OUTPUT_BUCKET', 'jsmith-output')
        output_key = f'artifacts/{book_id}/page_analysis.json'

        result_dict = analyzer.to_dict(result)

        s3.put_object(
            Bucket=output_bucket,
            Key=output_key,
            Body=json.dumps(result_dict, indent=2),
            ContentType='application/json'
        )

        logger.info(f"Page analysis saved to s3://{output_bucket}/{output_key}")

        return {
            'status': 'success',
            'book_id': book_id,
            'page_analysis_uri': f's3://{output_bucket}/{output_key}',
            'page_offset': result.page_offset.calculated_offset,
            'offset_consistent': result.page_offset.is_consistent,
            'songs_found': len(result.songs),
            'pages_analyzed': len(result.pages)
        }

    finally:
        # Clean up temp file
        os.unlink(pdf_path)
