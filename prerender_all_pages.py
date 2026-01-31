#!/usr/bin/env python3
"""
Pre-render all PDF pages to JPG for faster verification.

This separates the CPU-intensive rendering from GPU-intensive inference,
allowing better resource utilization.

Usage:
    py prerender_all_pages.py --test      # Test with 5 PDFs
    py prerender_all_pages.py --pilot     # Render 50 PDFs
    py prerender_all_pages.py --batch N   # Render N PDFs
    py prerender_all_pages.py --full      # Render all 11,976 PDFs
"""

import argparse
import logging
import random
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from tqdm import tqdm
import fitz

# Configuration
PROCESSED_SONGS_PATH = Path("C:/Work/AWSMusic/ProcessedSongs")
CACHE_PATH = Path("D:/ImageCache/pdf_verification")
RENDER_DPI = 300
JPG_QUALITY = 90
MAX_WORKERS = 16  # More workers for CPU-bound rendering

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prerender.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def get_cache_path(pdf_path: Path, page_num: int) -> Path:
    """Get cache path for a rendered page."""
    rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
    artist = rel_path.parts[0]
    book = rel_path.parts[1] if len(rel_path.parts) > 1 else "unknown"
    
    # Use PDF hash for unique filename
    import hashlib
    pdf_hash = hashlib.md5(str(pdf_path).encode()).hexdigest()[:16]
    
    cache_dir = CACHE_PATH / artist / book
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir / f"{pdf_hash}_page_{page_num:04d}.jpg"


def render_pdf_pages(pdf_path: Path) -> tuple[int, int, float]:
    """
    Render all pages of a PDF to JPG.
    Returns (pages_rendered, pages_cached, time_seconds).
    """
    start_time = time.time()
    pages_rendered = 0
    pages_cached = 0
    
    try:
        doc = fitz.open(pdf_path)
        page_count = len(doc)
        
        zoom = RENDER_DPI / 72
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in range(page_count):
            cache_path = get_cache_path(pdf_path, page_num)
            
            # Skip if already cached
            if cache_path.exists():
                pages_cached += 1
                continue
            
            # Render page
            page = doc[page_num]
            pix = page.get_pixmap(matrix=mat)
            pix.save(str(cache_path), "jpeg", jpg_quality=JPG_QUALITY)
            pages_rendered += 1
        
        doc.close()
        
    except Exception as e:
        logger.error(f"Error rendering {pdf_path}: {e}")
        return 0, 0, time.time() - start_time
    
    return pages_rendered, pages_cached, time.time() - start_time


def scan_all_pdfs() -> list[Path]:
    """Scan ProcessedSongs directory for all PDFs."""
    logger.info(f"Scanning {PROCESSED_SONGS_PATH} for PDFs...")
    pdfs = list(PROCESSED_SONGS_PATH.rglob("*.pdf"))
    logger.info(f"Found {len(pdfs)} PDFs")
    return pdfs


def main():
    parser = argparse.ArgumentParser(description="Pre-render PDF pages to JPG")
    parser.add_argument('--test', action='store_true', help="Test with 5 PDFs")
    parser.add_argument('--pilot', action='store_true', help="Render 50 PDFs")
    parser.add_argument('--batch', type=int, help="Render N PDFs")
    parser.add_argument('--full', action='store_true', help="Render all PDFs")
    parser.add_argument('--workers', type=int, default=MAX_WORKERS, help=f"Number of workers (default: {MAX_WORKERS})")
    
    args = parser.parse_args()
    
    # Scan for PDFs
    all_pdfs = scan_all_pdfs()
    
    # Determine which PDFs to process
    if args.test:
        pdfs_to_process = random.sample(all_pdfs, min(5, len(all_pdfs)))
        logger.info("Test mode: Rendering 5 random PDFs")
    elif args.pilot:
        pdfs_to_process = random.sample(all_pdfs, min(50, len(all_pdfs)))
        logger.info("Pilot mode: Rendering 50 random PDFs")
    elif args.batch:
        pdfs_to_process = random.sample(all_pdfs, min(args.batch, len(all_pdfs)))
        logger.info(f"Batch mode: Rendering {len(pdfs_to_process)} random PDFs")
    elif args.full:
        pdfs_to_process = all_pdfs
        logger.info(f"Full mode: Rendering all {len(pdfs_to_process)} PDFs")
    else:
        logger.error("Please specify --test, --pilot, --batch N, or --full")
        return
    
    # Render PDFs with progress bar
    total_rendered = 0
    total_cached = 0
    total_time = 0
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(render_pdf_pages, pdf): pdf for pdf in pdfs_to_process}
        
        with tqdm(total=len(pdfs_to_process), desc="Rendering PDFs") as pbar:
            for future in as_completed(futures):
                try:
                    rendered, cached, elapsed = future.result()
                    total_rendered += rendered
                    total_cached += cached
                    total_time += elapsed
                    pbar.update(1)
                    
                except Exception as e:
                    pdf = futures[future]
                    logger.error(f"Error processing {pdf}: {e}")
                    pbar.update(1)
    
    # Summary
    logger.info("=" * 80)
    logger.info("Pre-rendering complete!")
    logger.info(f"PDFs processed: {len(pdfs_to_process)}")
    logger.info(f"Pages rendered: {total_rendered}")
    logger.info(f"Pages cached (skipped): {total_cached}")
    logger.info(f"Total pages: {total_rendered + total_cached}")
    logger.info(f"Total time: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    if total_rendered > 0:
        logger.info(f"Average per page: {total_time/total_rendered:.3f}s")


if __name__ == "__main__":
    main()
