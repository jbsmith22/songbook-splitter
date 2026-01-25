#!/usr/bin/env python3
"""
Local Runner Script for SheetMusic Book Splitter

This script allows you to test the entire pipeline locally without AWS:
- Uses local filesystem instead of S3
- Uses mock AWS services (Textract, Bedrock, DynamoDB)
- Processes a single PDF for testing
- Supports dry-run mode

Usage:
    python local_runner.py --pdf path/to/book.pdf --artist "Artist Name" --book-name "Book Name"
    python local_runner.py --pdf path/to/book.pdf --artist "Artist Name" --book-name "Book Name" --dry-run
    python local_runner.py --pdf path/to/book.pdf --artist "Artist Name" --book-name "Book Name" --output ./output
"""

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import hashlib

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.toc_discovery import TOCDiscoveryService
from app.services.toc_parser import TOCParser
from app.services.page_mapper import PageMapperService
from app.services.song_verifier import SongVerifierService
from app.services.pdf_splitter import PDFSplitterService
from app.services.manifest_generator import ManifestGeneratorService
from app.services.quality_gates import (
    check_toc_quality_gate,
    check_verification_quality_gate,
    check_output_quality_gate,
    aggregate_quality_gates
)
from app.utils.error_handling import ErrorAggregator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_book_id(pdf_path: str) -> str:
    """Generate unique book ID from PDF path."""
    return hashlib.md5(pdf_path.encode()).hexdigest()[:16]


def run_pipeline(
    pdf_path: str,
    artist: str,
    book_name: str,
    output_path: str = "./output",
    dry_run: bool = False,
    max_toc_pages: int = 20,
    various_artists: bool = False
) -> bool:
    """
    Run the complete pipeline locally.
    
    Args:
        pdf_path: Path to input PDF file
        artist: Artist name
        book_name: Book name
        output_path: Output directory for results
        dry_run: If True, don't write output files
        max_toc_pages: Maximum pages to scan for TOC
        various_artists: If True, treat as Various Artists book
        
    Returns:
        True if pipeline succeeded, False otherwise
    """
    processing_start = datetime.now()
    book_id = generate_book_id(pdf_path)
    error_aggregator = ErrorAggregator()
    warnings = []
    
    logger.info("=" * 80)
    logger.info("SheetMusic Book Splitter - Local Runner")
    logger.info("=" * 80)
    logger.info(f"PDF: {pdf_path}")
    logger.info(f"Artist: {artist}")
    logger.info(f"Book: {book_name}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"Book ID: {book_id}")
    logger.info("=" * 80)
    
    # Validate input
    if not Path(pdf_path).exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return False
    
    # Create output directory
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # ===================================================================
        # PHASE 1: TOC Discovery
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: TOC Discovery")
        logger.info("=" * 80)
        
        toc_discovery_service = TOCDiscoveryService(local_mode=True)
        toc_discovery_result = toc_discovery_service.discover_toc(
            pdf_path=pdf_path,
            max_pages=max_toc_pages
        )
        
        logger.info(f"TOC pages identified: {toc_discovery_result.toc_pages}")
        logger.info(f"Confidence scores: {toc_discovery_result.confidence_scores}")
        
        if not toc_discovery_result.toc_pages:
            logger.error("No TOC pages found")
            return False
        
        # ===================================================================
        # PHASE 2: TOC Parsing
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: TOC Parsing")
        logger.info("=" * 80)
        
        # Combine text from all TOC pages
        toc_text = "\n".join(
            toc_discovery_result.extracted_text.get(page, "")
            for page in toc_discovery_result.toc_pages
        )
        
        toc_parser = TOCParser(use_bedrock_fallback=True, local_mode=True)
        toc_parse_result = toc_parser.parse_toc(
            toc_text=toc_text,
            book_metadata={
                "artist": artist,
                "book_name": book_name,
                "various_artists": various_artists
            }
        )
        
        logger.info(f"TOC entries extracted: {len(toc_parse_result.entries)}")
        logger.info(f"Extraction method: {toc_parse_result.extraction_method}")
        logger.info(f"Confidence: {toc_parse_result.confidence:.2f}")
        
        # Display first few entries
        for i, entry in enumerate(toc_parse_result.entries[:5]):
            artist_str = f" ({entry.artist})" if entry.artist else ""
            logger.info(f"  {i+1}. {entry.song_title}{artist_str} - Page {entry.page_number}")
        if len(toc_parse_result.entries) > 5:
            logger.info(f"  ... and {len(toc_parse_result.entries) - 5} more")
        
        # Quality Gate 1: TOC Entry Count
        toc_gate = check_toc_quality_gate(
            toc_entry_count=len(toc_parse_result.entries),
            min_entries=10
        )
        logger.info(f"\nQuality Gate 1: {toc_gate.message}")
        
        if not toc_gate.passed:
            logger.warning("TOC quality gate failed - would route to manual review in production")
            warnings.append(toc_gate.message)
        
        # ===================================================================
        # PHASE 3: Page Mapping
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: Page Mapping")
        logger.info("=" * 80)
        
        page_mapper = PageMapperService()
        page_mapping = page_mapper.build_page_mapping(
            pdf_path=pdf_path,
            toc_entries=toc_parse_result.entries,
            sample_size=min(3, len(toc_parse_result.entries))
        )
        
        logger.info(f"Page offset calculated: {page_mapping.offset}")
        logger.info(f"Confidence: {page_mapping.confidence:.2f}")
        logger.info(f"Samples verified: {page_mapping.samples_verified}")
        
        # ===================================================================
        # PHASE 4: Song Verification
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: Song Verification")
        logger.info("=" * 80)
        
        song_verifier = SongVerifierService()
        verified_songs = song_verifier.verify_song_starts(
            pdf_path=pdf_path,
            song_locations=page_mapping.song_locations,
            search_range=3
        )
        
        songs_verified = sum(1 for s in verified_songs if s.verified)
        songs_adjusted = sum(1 for s in verified_songs if s.adjustment != 0)
        
        logger.info(f"Songs verified: {songs_verified}/{len(verified_songs)}")
        logger.info(f"Songs adjusted: {songs_adjusted}")
        
        # Log adjustments
        for song in verified_songs:
            if song.adjustment != 0:
                msg = f"Song '{song.song_title}' adjusted by {song.adjustment} pages"
                logger.warning(msg)
                warnings.append(msg)
        
        # Quality Gate 2: Verification Success Rate
        verification_gate = check_verification_quality_gate(
            songs_verified=songs_verified,
            total_songs=len(verified_songs),
            min_success_rate=0.95
        )
        logger.info(f"\nQuality Gate 2: {verification_gate.message}")
        
        if not verification_gate.passed:
            logger.warning("Verification quality gate failed - would route to manual review in production")
            warnings.append(verification_gate.message)
        
        # Calculate page ranges
        # Get total pages from PDF
        import fitz
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        
        page_ranges = song_verifier.adjust_page_ranges(verified_songs, total_pages)
        
        # ===================================================================
        # PHASE 5: PDF Splitting
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 5: PDF Splitting")
        logger.info("=" * 80)
        
        if dry_run:
            logger.info("DRY RUN MODE: Skipping PDF splitting")
            output_files = []
            songs_extracted = len(page_ranges)
        else:
            pdf_splitter = PDFSplitterService(
                local_mode=True,
                local_output_path=str(output_dir)
            )
            
            output_files = pdf_splitter.split_pdf(
                pdf_path=pdf_path,
                page_ranges=page_ranges,
                book_artist=artist,
                book_name=book_name,
                various_artists=various_artists
            )
            
            songs_extracted = len(output_files)
            logger.info(f"Songs extracted: {songs_extracted}/{len(page_ranges)}")
            
            # Log failed extractions
            if songs_extracted < len(page_ranges):
                failed_count = len(page_ranges) - songs_extracted
                msg = f"{failed_count} songs failed to extract"
                logger.warning(msg)
                warnings.append(msg)
        
        # Quality Gate 3: Output Success Rate
        output_gate = check_output_quality_gate(
            songs_extracted=songs_extracted,
            total_songs=len(page_ranges),
            min_success_rate=0.90
        )
        logger.info(f"\nQuality Gate 3: {output_gate.message}")
        
        if not output_gate.passed:
            logger.warning("Output quality gate failed - would route to manual review in production")
            warnings.append(output_gate.message)
        
        # ===================================================================
        # PHASE 6: Manifest Generation
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 6: Manifest Generation")
        logger.info("=" * 80)
        
        processing_end = datetime.now()
        
        manifest_generator = ManifestGeneratorService(
            local_mode=True,
            local_output_path=str(output_dir)
        )
        
        manifest = manifest_generator.generate_manifest(
            book_id=book_id,
            source_pdf=pdf_path,
            artist=artist,
            book_name=book_name,
            toc_discovery=toc_discovery_result,
            toc_parse=toc_parse_result,
            page_mapping=page_mapping,
            verification_results={
                "songs_verified": songs_verified,
                "songs_adjusted": songs_adjusted,
                "total_songs": len(verified_songs)
            },
            output_files=output_files if not dry_run else [],
            processing_start=processing_start,
            processing_end=processing_end,
            warnings=warnings,
            errors=error_aggregator.get_errors()
        )
        
        # Write manifest
        manifest_path = output_dir / f"{book_name}_manifest.json"
        # For local mode, write directly to file
        import json
        with open(manifest_path, 'w') as f:
            json.dump(manifest.to_dict(), f, indent=2)
        logger.info(f"Manifest written to: {manifest_path}")
        
        # ===================================================================
        # SUMMARY
        # ===================================================================
        logger.info("\n" + "=" * 80)
        logger.info("PIPELINE SUMMARY")
        logger.info("=" * 80)
        
        # Aggregate quality gates
        gate_results = aggregate_quality_gates([toc_gate, verification_gate, output_gate])
        
        logger.info(f"Overall Status: {gate_results['overall_status'].upper()}")
        logger.info(f"Quality Gates: {gate_results['gates_passed']}/{gate_results['gates_checked']} passed")
        logger.info(f"TOC Entries: {len(toc_parse_result.entries)}")
        logger.info(f"Songs Verified: {songs_verified}/{len(verified_songs)} ({verification_gate.metric_value:.1%})")
        logger.info(f"Songs Extracted: {songs_extracted}/{len(page_ranges)} ({output_gate.metric_value:.1%})")
        logger.info(f"Processing Time: {(processing_end - processing_start).total_seconds():.1f}s")
        logger.info(f"Warnings: {len(warnings)}")
        logger.info(f"Errors: {len(error_aggregator.get_errors())}")
        
        if warnings:
            logger.info("\nWarnings:")
            for warning in warnings:
                logger.info(f"  - {warning}")
        
        if error_aggregator.get_errors():
            logger.info("\nErrors:")
            for error in error_aggregator.get_errors():
                logger.info(f"  - {error}")
        
        logger.info("=" * 80)
        
        # Determine success
        success = gate_results['overall_status'] in ['success', 'manual_review']
        
        if success:
            logger.info("✓ Pipeline completed successfully")
        else:
            logger.error("✗ Pipeline failed")
        
        return success
        
    except Exception as e:
        logger.exception(f"Pipeline failed with exception: {e}")
        error_aggregator.add_error(str(e), {"exception_type": type(e).__name__})
        return False


def main():
    """Main entry point for local runner."""
    parser = argparse.ArgumentParser(
        description="Run SheetMusic Book Splitter pipeline locally",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python local_runner.py --pdf book.pdf --artist "Artist Name" --book-name "Book Name"
  python local_runner.py --pdf book.pdf --artist "Artist Name" --book-name "Book Name" --dry-run
  python local_runner.py --pdf book.pdf --artist "Various Artists" --book-name "Compilation" --various-artists
        """
    )
    
    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to input PDF file"
    )
    
    parser.add_argument(
        "--artist",
        required=True,
        help="Artist name"
    )
    
    parser.add_argument(
        "--book-name",
        required=True,
        help="Book name"
    )
    
    parser.add_argument(
        "--output",
        default="./output",
        help="Output directory (default: ./output)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run pipeline without writing output files"
    )
    
    parser.add_argument(
        "--max-toc-pages",
        type=int,
        default=20,
        help="Maximum pages to scan for TOC (default: 20)"
    )
    
    parser.add_argument(
        "--various-artists",
        action="store_true",
        help="Treat as Various Artists book"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run pipeline
    success = run_pipeline(
        pdf_path=args.pdf,
        artist=args.artist,
        book_name=args.book_name,
        output_path=args.output,
        dry_run=args.dry_run,
        max_toc_pages=args.max_toc_pages,
        various_artists=args.various_artists
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
