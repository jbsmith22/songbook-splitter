#!/usr/bin/env python3
"""
PDF Split Verification System

Verifies that individual split PDF files are cleanly split with proper song boundaries.
Uses Ollama vision model (llava:7b) with GPU acceleration.

Usage:
    py verify_pdf_splits.py --pilot              # Run on 50 random PDFs
    py verify_pdf_splits.py --batch 500          # Run on 500 PDFs
    py verify_pdf_splits.py --full               # Run on all 11,976 PDFs
    py verify_pdf_splits.py --resume             # Resume from checkpoint
"""

import argparse
import json
import logging
import random
import sys
import time
import base64
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm

import requests
import fitz  # PyMuPDF
from PIL import Image

# Configuration
PROCESSED_SONGS_PATH = Path("C:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("D:/ImageCache/pdf_verification")
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llava:7b"
RENDER_DPI = 300
JPG_QUALITY = 90  # JPG quality for rendering
MAX_WORKERS = 12
OLLAMA_WORKERS = 6  # Increase from 3 to 6 to reduce queue
OLLAMA_TIMEOUT = 90  # Increase timeout to 90 seconds
CHECKPOINT_FILE = "verification_checkpoint.json"
RESULTS_DIR = Path("verification_results")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pdf_verification.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PageAnalysis:
    """Analysis result for a single page."""
    page_num: int
    has_title: bool
    title_text: Optional[str]
    is_first_page: bool
    is_continuation: bool
    has_new_song: bool
    has_end_bars: bool
    has_excessive_text: bool
    raw_response: str
    

@dataclass
class PDFVerificationResult:
    """Verification result for a single PDF."""
    pdf_path: str
    artist: str
    book: str
    song_title: str
    page_count: int
    file_size_bytes: int
    
    # Heuristic checks
    heuristic_flags: List[str]
    
    # Vision analysis results
    first_page_analysis: Optional[PageAnalysis]
    middle_pages_analysis: List[PageAnalysis]
    last_page_analysis: Optional[PageAnalysis]
    
    # Overall assessment
    issues: List[str]
    warnings: List[str]
    passed: bool
    
    # Metadata
    processing_time_seconds: float
    timestamp: str


class OllamaVisionClient:
    """Client for Ollama vision API with rate limiting."""
    
    def __init__(self, endpoint: str = OLLAMA_ENDPOINT, model: str = OLLAMA_MODEL, max_concurrent: int = OLLAMA_WORKERS):
        self.endpoint = endpoint
        self.model = model
        self.session = requests.Session()
        self.semaphore = None  # Will be set when used in async context
        self.max_concurrent = max_concurrent
        
    def analyze_image(self, image_path: Path, prompt: str, timeout: int = OLLAMA_TIMEOUT) -> Dict:
        """Call Ollama vision API with image."""
        try:
            # Read and encode image
            with open(image_path, 'rb') as f:
                image_base64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Call Ollama API
            response = self.session.post(
                self.endpoint,
                json={
                    'model': self.model,
                    'prompt': prompt,
                    'images': [image_base64],
                    'stream': False
                },
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout analyzing {image_path}")
            return {'error': 'timeout'}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error analyzing {image_path}: {e}")
            return {'error': str(e)}
    
    def check_availability(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = self.session.get("http://localhost:11434/api/tags", timeout=5)
            response.raise_for_status()
            tags = response.json()
            models = [m['name'] for m in tags.get('models', [])]
            return self.model in models
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False


class PDFRenderer:
    """Renders PDF pages to PNG images."""
    
    def __init__(self, cache_path: Path = CACHE_PATH, dpi: int = RENDER_DPI):
        self.cache_path = cache_path
        self.dpi = dpi
        self.cache_path.mkdir(parents=True, exist_ok=True)
    
    def get_cache_key(self, pdf_path: Path, page_num: int) -> str:
        """Generate cache key for a PDF page."""
        pdf_hash = hashlib.md5(str(pdf_path).encode()).hexdigest()[:16]
        return f"{pdf_hash}_page_{page_num:04d}.jpg"
    
    def get_cached_image_path(self, pdf_path: Path, page_num: int) -> Path:
        """Get path to cached image."""
        # Organize by artist/book for easier management
        rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
        
        cache_dir = self.cache_path / artist / book
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        cache_key = self.get_cache_key(pdf_path, page_num)
        return cache_dir / cache_key
    
    def render_page(self, pdf_path: Path, page_num: int, force: bool = False) -> Optional[Path]:
        """Render a PDF page to JPG. Returns path to cached image."""
        cache_image_path = self.get_cached_image_path(pdf_path, page_num)
        
        # Use cached version if available
        if cache_image_path.exists() and not force:
            return cache_image_path
        
        try:
            doc = fitz.open(pdf_path)
            if page_num >= len(doc):
                logger.error(f"Page {page_num} out of range for {pdf_path}")
                doc.close()
                return None
            
            page = doc[page_num]
            
            # Render at specified DPI
            zoom = self.dpi / 72  # 72 DPI is default
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # Save as JPG
            pix.save(str(cache_image_path), "jpeg", jpg_quality=JPG_QUALITY)
            doc.close()
            
            return cache_image_path
            
        except Exception as e:
            logger.error(f"Error rendering {pdf_path} page {page_num}: {e}")
            return None
    
    def render_all_pages(self, pdf_path: Path) -> List[Path]:
        """Render all pages of a PDF. Returns list of cached image paths."""
        try:
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            rendered_pages = []
            for page_num in range(page_count):
                image_path = self.render_page(pdf_path, page_num)
                if image_path:
                    rendered_pages.append(image_path)
            
            return rendered_pages
            
        except Exception as e:
            logger.error(f"Error rendering {pdf_path}: {e}")
            return []


class PDFVerifier:
    """Main PDF verification logic."""
    
    def __init__(self, ollama_client: OllamaVisionClient, renderer: PDFRenderer):
        self.ollama = ollama_client
        self.renderer = renderer
        # Create a semaphore to limit concurrent Ollama requests
        from threading import Semaphore
        self.ollama_semaphore = Semaphore(OLLAMA_WORKERS)
    
    def _call_ollama_with_limit(self, image_path: Path, prompt: str) -> Dict:
        """Call Ollama with semaphore to limit concurrency."""
        with self.ollama_semaphore:
            return self.ollama.analyze_image(image_path, prompt)
    
    def run_heuristic_checks(self, pdf_path: Path) -> Tuple[List[str], int, int]:
        """Run quick heuristic checks. Returns (flags, page_count, file_size)."""
        flags = []
        
        try:
            # Check file size
            file_size = pdf_path.stat().st_size
            if file_size < 10 * 1024:  # < 10KB
                flags.append("VERY_SMALL_FILE")
            elif file_size > 5 * 1024 * 1024:  # > 5MB
                flags.append("VERY_LARGE_FILE")
            
            # Check page count
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            if page_count == 1:
                flags.append("SINGLE_PAGE")
            elif page_count > 15:
                flags.append("VERY_LONG_SONG")
            
            return flags, page_count, file_size
            
        except Exception as e:
            logger.error(f"Error in heuristic checks for {pdf_path}: {e}")
            return ["ERROR_OPENING_PDF"], 0, 0
    
    def parse_vision_response(self, response: Dict) -> str:
        """Extract text from Ollama response."""
        if 'error' in response:
            return f"ERROR: {response['error']}"
        text = response.get('response', '').strip()
        # If empty or error, return a default that won't match
        if not text or text.startswith('ERROR'):
            return "TIMEOUT_OR_ERROR"
        return text
    
    def analyze_first_page(self, image_path: Path) -> PageAnalysis:
        """Analyze first page of song."""
        prompt = """Look at this sheet music page carefully. This could be standard notation, guitar tabs, or text-based tabs.

Answer these questions:
1. Is there a song title visible ANYWHERE on the page? (YES/NO)
2. What is the song title if visible? (write title or NONE)
3. Does this page show the START of a song (first measures/bars)? (YES/NO)
4. Does this page look like it starts MID-SONG (continuation from previous page)? (YES/NO)

Note: It's OK if another song appears before this one on the same page. Focus on whether THIS song starts properly.

Answer with just YES/NO or the title text, one answer per line."""
        
        response = self._call_ollama_with_limit(image_path, prompt)
        raw_text = self.parse_vision_response(response)
        
        # Parse numbered response format: "1. Yes\n2. Title\n3. No\n4. No"
        lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
        
        # Handle timeout/error case
        if raw_text == "TIMEOUT_OR_ERROR" or not lines:
            return PageAnalysis(
                page_num=0,
                has_title=False,
                title_text=None,
                is_first_page=False,
                is_continuation=False,
                has_new_song=False,
                has_end_bars=False,
                has_excessive_text=False,
                raw_response="TIMEOUT"
            )
        
        # Extract answers (handle both "1. Yes" and "Yes" formats)
        answers = []
        for line in lines:
            # Remove leading numbers and dots
            answer = line.split('.', 1)[-1].strip() if '.' in line else line.strip()
            answers.append(answer)
        
        # Ensure we have at least 4 answers
        while len(answers) < 4:
            answers.append("UNKNOWN")
        
        has_title = answers[0].upper() in ['YES', 'Y', 'TRUE']
        title_text = answers[1] if answers[1].upper() not in ['NO', 'N', 'NONE', 'FALSE', 'UNKNOWN'] else None
        is_first = answers[2].upper() in ['YES', 'Y', 'TRUE']
        is_continuation = answers[3].upper() in ['YES', 'Y', 'TRUE']
        
        return PageAnalysis(
            page_num=0,
            has_title=has_title,
            title_text=title_text,
            is_first_page=is_first,
            is_continuation=is_continuation,
            has_new_song=False,
            has_end_bars=False,
            has_excessive_text=False,
            raw_response=raw_text
        )
    
    def analyze_middle_page(self, image_path: Path, page_num: int) -> PageAnalysis:
        """Analyze middle page of song."""
        prompt = """Look at this sheet music page very carefully.

This is a CRITICAL question: Does this page show the CLEAR BEGINNING of a COMPLETELY NEW AND DIFFERENT SONG?

To answer YES, you must see:
- A prominent song title that is DIFFERENT from the previous song
- The very first measures/bars of that new song
- Clear visual break indicating a new song starts here

Answer YES ONLY if you are CERTAIN a new song starts on this page.
Answer NO if this is just a continuation of the current song, even if there are section markers, tempo changes, or other musical notation.

Answer with just YES or NO."""
        
        response = self._call_ollama_with_limit(image_path, prompt)
        raw_text = self.parse_vision_response(response)
        
        # Parse simple YES/NO response
        has_new_song = raw_text.strip().upper() in ['YES', 'Y', 'TRUE', '1. YES', 'YES.']
        
        return PageAnalysis(
            page_num=page_num,
            has_title=has_new_song,  # If new song, assume it has title
            title_text=None,
            is_first_page=False,
            is_continuation=not has_new_song,
            has_new_song=has_new_song,
            has_end_bars=False,
            has_excessive_text=False,
            raw_response=raw_text
        )
    
    def analyze_last_page(self, image_path: Path, page_num: int) -> PageAnalysis:
        """Analyze last page of song."""
        prompt = """Look at this sheet music page very carefully.

This is a CRITICAL question: Does this page show the CLEAR BEGINNING of a COMPLETELY NEW AND DIFFERENT SONG?

To answer YES, you must see:
- A prominent song title that is DIFFERENT from the current song
- The very first measures/bars of that new song starting on this page

Answer YES ONLY if you are CERTAIN a new song starts on this page.
Answer NO if this is just the end of the current song, even if there are photos, text, or other content.

Answer with just YES or NO."""
        
        response = self._call_ollama_with_limit(image_path, prompt)
        raw_text = self.parse_vision_response(response)
        
        # Parse simple YES/NO response
        has_new_song = raw_text.strip().upper() in ['YES', 'Y', 'TRUE', '1. YES', 'YES.']
        
        return PageAnalysis(
            page_num=page_num,
            has_title=has_new_song,
            title_text=None,
            is_first_page=False,
            is_continuation=False,
            has_new_song=has_new_song,
            has_end_bars=False,
            has_excessive_text=False,
            raw_response=raw_text
        )
    
    def verify_pdf(self, pdf_path: Path) -> PDFVerificationResult:
        """Verify a single PDF file."""
        start_time = time.time()
        
        # Extract metadata from path
        rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
        song_title = pdf_path.stem
        
        logger.info(f"Verifying: {artist}/{book}/{song_title}")
        
        # Stage 1: Heuristic checks
        heuristic_flags, page_count, file_size = self.run_heuristic_checks(pdf_path)
        
        if "ERROR_OPENING_PDF" in heuristic_flags:
            return PDFVerificationResult(
                pdf_path=str(pdf_path),
                artist=artist,
                book=book,
                song_title=song_title,
                page_count=0,
                file_size_bytes=0,
                heuristic_flags=heuristic_flags,
                first_page_analysis=None,
                middle_pages_analysis=[],
                last_page_analysis=None,
                issues=["Cannot open PDF"],
                warnings=[],
                passed=False,
                processing_time_seconds=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )
        
        # Stage 2: Render all pages
        rendered_pages = self.renderer.render_all_pages(pdf_path)
        if not rendered_pages:
            return PDFVerificationResult(
                pdf_path=str(pdf_path),
                artist=artist,
                book=book,
                song_title=song_title,
                page_count=page_count,
                file_size_bytes=file_size,
                heuristic_flags=heuristic_flags,
                first_page_analysis=None,
                middle_pages_analysis=[],
                last_page_analysis=None,
                issues=["Failed to render pages"],
                warnings=[],
                passed=False,
                processing_time_seconds=time.time() - start_time,
                timestamp=datetime.now().isoformat()
            )
        
        # Stage 3: Vision analysis
        issues = []
        warnings = []
        
        # Analyze first page - Be VERY conservative
        # We should almost NEVER flag the first page unless it's obviously wrong
        first_page_analysis = self.analyze_first_page(rendered_pages[0])
        
        # Don't flag first page issues - too many false positives
        # The user's split rules allow songs to start mid-page
        
        # Analyze middle pages - Flag if NEW song detected
        middle_pages_analysis = []
        for i in range(1, len(rendered_pages) - 1):
            analysis = self.analyze_middle_page(rendered_pages[i], i)
            middle_pages_analysis.append(analysis)
            
            # Flag if we detect a new song starting
            # Either: has title AND new song, OR just new song with high confidence
            if analysis.has_new_song:
                issues.append(f"Page {i+1} has new song starting (missed split)")
        
        # Analyze last page - Flag if NEW song detected
        last_page_analysis = None
        if len(rendered_pages) > 1:
            last_page_analysis = self.analyze_last_page(rendered_pages[-1], len(rendered_pages) - 1)
            
            # Flag if we detect a new song starting
            if last_page_analysis.has_new_song:
                issues.append("Last page has new song starting (missed split)")
        
        # Combine with heuristic flags (only the serious ones)
        if "VERY_LONG_SONG" in heuristic_flags:
            warnings.append("Very long song (>15 pages) - may contain multiple songs")
        if "ERROR_OPENING_PDF" in heuristic_flags:
            issues.append("Cannot open PDF")
        
        # Determine if passed
        passed = len(issues) == 0
        
        processing_time = time.time() - start_time
        
        return PDFVerificationResult(
            pdf_path=str(pdf_path),
            artist=artist,
            book=book,
            song_title=song_title,
            page_count=page_count,
            file_size_bytes=file_size,
            heuristic_flags=heuristic_flags,
            first_page_analysis=first_page_analysis,
            middle_pages_analysis=middle_pages_analysis,
            last_page_analysis=last_page_analysis,
            issues=issues,
            warnings=warnings,
            passed=passed,
            processing_time_seconds=processing_time,
            timestamp=datetime.now().isoformat()
        )


def scan_all_pdfs() -> List[Path]:
    """Scan ProcessedSongs directory for all PDFs."""
    logger.info(f"Scanning {PROCESSED_SONGS_PATH} for PDFs...")
    pdfs = list(PROCESSED_SONGS_PATH.rglob("*.pdf"))
    logger.info(f"Found {len(pdfs)} PDFs")
    return pdfs


def save_checkpoint(processed_pdfs: List[str], results: List[PDFVerificationResult]):
    """Save progress checkpoint."""
    checkpoint = {
        'processed_pdfs': processed_pdfs,
        'results': [asdict(r) for r in results],
        'timestamp': datetime.now().isoformat()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def load_checkpoint() -> Tuple[List[str], List[PDFVerificationResult]]:
    """Load progress checkpoint."""
    if not Path(CHECKPOINT_FILE).exists():
        return [], []
    
    with open(CHECKPOINT_FILE, 'r') as f:
        checkpoint = json.load(f)
    
    processed_pdfs = checkpoint.get('processed_pdfs', [])
    results_data = checkpoint.get('results', [])
    
    # Reconstruct results (simplified - just keep as dicts for now)
    results = results_data
    
    logger.info(f"Loaded checkpoint: {len(processed_pdfs)} PDFs already processed")
    return processed_pdfs, results


def generate_reports(results: List[PDFVerificationResult]):
    """Generate CSV reports and summary."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Flagged PDFs report with image links
    flagged_path = RESULTS_DIR / f"verification_flagged_{timestamp}.csv"
    with open(flagged_path, 'w', encoding='utf-8') as f:
        f.write("pdf_path,artist,book,song_title,page_count,issues,warnings,first_page_image,flagged_page_images,processing_time_sec\n")
        for r in results:
            if not r.passed or r.warnings:
                issues_str = "; ".join(r.issues) if r.issues else ""
                warnings_str = "; ".join(r.warnings) if r.warnings else ""
                
                # Generate image links
                pdf_path = Path(r.pdf_path)
                renderer = PDFRenderer()
                
                # First page image link
                first_page_path = renderer.get_cached_image_path(pdf_path, 0)
                first_page_link = f"file:///{first_page_path.as_posix()}" if first_page_path.exists() else ""
                
                # Flagged page image links (extract page numbers from issues)
                flagged_pages = set()
                for issue in r.issues:
                    # Extract page numbers from issues like "Page 3 has title"
                    import re
                    matches = re.findall(r'Page (\d+)', issue)
                    for match in matches:
                        flagged_pages.add(int(match) - 1)  # Convert to 0-indexed
                
                # Add last page if it has issues
                if any('Last page' in issue for issue in r.issues):
                    flagged_pages.add(r.page_count - 1)
                
                # Generate links for flagged pages
                flagged_links = []
                for page_num in sorted(flagged_pages):
                    page_path = renderer.get_cached_image_path(pdf_path, page_num)
                    if page_path.exists():
                        flagged_links.append(f"file:///{page_path.as_posix()}")
                
                flagged_images_str = " | ".join(flagged_links) if flagged_links else ""
                
                f.write(f'"{r.pdf_path}","{r.artist}","{r.book}","{r.song_title}",{r.page_count},"{issues_str}","{warnings_str}","{first_page_link}","{flagged_images_str}",{r.processing_time_seconds:.2f}\n')
    
    logger.info(f"Flagged PDFs report: {flagged_path}")
    
    # Generate HTML report for easier review
    html_path = RESULTS_DIR / f"verification_flagged_{timestamp}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>PDF Verification Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #4CAF50; color: white; position: sticky; top: 0; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        tr:hover { background-color: #ddd; }
        .error { color: red; font-weight: bold; }
        .warning { color: orange; }
        .image-link { color: blue; text-decoration: underline; cursor: pointer; margin-right: 10px; }
        .pdf-path { font-size: 0.9em; color: #666; }
        img { max-width: 800px; margin: 10px 0; border: 2px solid #ddd; }
        .collapsible { cursor: pointer; padding: 10px; background-color: #eee; margin: 5px 0; }
        .content { display: none; padding: 10px; border: 1px solid #ddd; }
    </style>
    <script>
        function toggleImages(id) {
            var content = document.getElementById(id);
            if (content.style.display === "block") {
                content.style.display = "none";
            } else {
                content.style.display = "block";
            }
        }
    </script>
</head>
<body>
    <h1>PDF Split Verification Results</h1>
    <p><strong>Generated:</strong> """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    <p><strong>Total PDFs analyzed:</strong> """ + str(len(results)) + """</p>
    <p><strong>Passed:</strong> """ + str(sum(1 for r in results if r.passed)) + """</p>
    <p><strong>Flagged:</strong> """ + str(sum(1 for r in results if not r.passed)) + """</p>
    <table>
        <tr>
            <th>Artist</th>
            <th>Book</th>
            <th>Song</th>
            <th>Pages</th>
            <th>Issues</th>
            <th>Warnings</th>
            <th>View Images</th>
        </tr>
""")
        
        row_id = 0
        for r in results:
            if not r.passed or r.warnings:
                row_id += 1
                pdf_path = Path(r.pdf_path)
                renderer = PDFRenderer()
                
                # Collect all page images
                all_images = []
                for page_num in range(r.page_count):
                    page_path = renderer.get_cached_image_path(pdf_path, page_num)
                    if page_path.exists():
                        all_images.append((page_num + 1, page_path))
                
                issues_html = "<br>".join([f'<span class="error">• {issue}</span>' for issue in r.issues]) if r.issues else ""
                warnings_html = "<br>".join([f'<span class="warning">• {warn}</span>' for warn in r.warnings]) if r.warnings else ""
                
                f.write(f"""
        <tr>
            <td>{r.artist}</td>
            <td>{r.book}</td>
            <td>{r.song_title}</td>
            <td>{r.page_count}</td>
            <td>{issues_html}</td>
            <td>{warnings_html}</td>
            <td>
                <button class="collapsible" onclick="toggleImages('images_{row_id}')">Show/Hide All Pages</button>
                <div id="images_{row_id}" class="content">
                    <p class="pdf-path">{r.pdf_path}</p>
""")
                
                for page_num, page_path in all_images:
                    f.write(f'                    <p><strong>Page {page_num}:</strong></p>\n')
                    f.write(f'                    <img src="file:///{page_path.as_posix()}" alt="Page {page_num}">\n')
                
                f.write("""                </div>
            </td>
        </tr>
""")
        
        f.write("""    </table>
</body>
</html>
""")
    
    logger.info(f"HTML report: {html_path}")
    
    # Summary report
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    flagged = sum(1 for r in results if not r.passed)
    warnings_only = sum(1 for r in results if r.passed and r.warnings)
    
    summary_path = RESULTS_DIR / f"verification_summary_{timestamp}.txt"
    with open(summary_path, 'w') as f:
        f.write("PDF Split Verification Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total PDFs analyzed: {total}\n")
        f.write(f"Passed: {passed} ({passed/total*100:.1f}%)\n")
        f.write(f"Flagged (issues): {flagged} ({flagged/total*100:.1f}%)\n")
        f.write(f"Warnings only: {warnings_only} ({warnings_only/total*100:.1f}%)\n")
        f.write(f"\nTimestamp: {datetime.now().isoformat()}\n")
    
    logger.info(f"Summary report: {summary_path}")
    logger.info(f"Results: {passed}/{total} passed, {flagged} flagged, {warnings_only} warnings")


def main():
    parser = argparse.ArgumentParser(description="PDF Split Verification System")
    parser.add_argument('--pilot', action='store_true', help="Run on 50 random PDFs")
    parser.add_argument('--batch', type=int, help="Run on N random PDFs")
    parser.add_argument('--test', action='store_true', help="Run on 5 random PDFs (quick test)")
    parser.add_argument('--full', action='store_true', help="Run on all PDFs")
    parser.add_argument('--resume', action='store_true', help="Resume from checkpoint")
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f"Number of workers (default: {MAX_WORKERS})")
    
    args = parser.parse_args()
    
    # Initialize components
    ollama = OllamaVisionClient()
    renderer = PDFRenderer()
    verifier = PDFVerifier(ollama, renderer)
    
    # Check Ollama availability
    if not ollama.check_availability():
        logger.error("Ollama is not available or model not found. Please start Ollama and ensure llava:7b is installed.")
        sys.exit(1)
    
    logger.info("Ollama is available and ready")
    
    # Scan for PDFs
    all_pdfs = scan_all_pdfs()
    
    # Determine which PDFs to process
    if args.resume:
        processed_pdfs, previous_results = load_checkpoint()
        pdfs_to_process = [p for p in all_pdfs if str(p) not in processed_pdfs]
        logger.info(f"Resuming: {len(pdfs_to_process)} PDFs remaining")
    elif args.test:
        pdfs_to_process = random.sample(all_pdfs, min(5, len(all_pdfs)))
        previous_results = []
        logger.info("Test mode: Processing 5 random PDFs")
    elif args.pilot:
        pdfs_to_process = random.sample(all_pdfs, min(50, len(all_pdfs)))
        previous_results = []
        logger.info("Pilot mode: Processing 50 random PDFs")
    elif args.batch:
        pdfs_to_process = random.sample(all_pdfs, min(args.batch, len(all_pdfs)))
        previous_results = []
        logger.info(f"Batch mode: Processing {len(pdfs_to_process)} random PDFs")
    elif args.full:
        pdfs_to_process = all_pdfs
        previous_results = []
        logger.info(f"Full mode: Processing all {len(pdfs_to_process)} PDFs")
    else:
        logger.error("Please specify --test, --pilot, --batch N, --full, or --resume")
        sys.exit(1)
    
    # Process PDFs with progress bar
    results = list(previous_results)
    processed_paths = [r['pdf_path'] if isinstance(r, dict) else r.pdf_path for r in previous_results]
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(verifier.verify_pdf, pdf): pdf for pdf in pdfs_to_process}
        
        with tqdm(total=len(pdfs_to_process), desc="Verifying PDFs") as pbar:
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    processed_paths.append(result.pdf_path)
                    
                    # Save checkpoint every 10 PDFs
                    if len(results) % 10 == 0:
                        save_checkpoint(processed_paths, results)
                    
                    pbar.update(1)
                    
                except Exception as e:
                    pdf = futures[future]
                    logger.error(f"Error processing {pdf}: {e}")
                    pbar.update(1)
    
    # Final checkpoint
    save_checkpoint(processed_paths, results)
    
    # Generate reports
    generate_reports(results)
    
    logger.info("Verification complete!")


if __name__ == "__main__":
    main()
