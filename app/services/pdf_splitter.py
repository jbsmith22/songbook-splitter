"""
PDF Splitter Service - Extracts page ranges and creates individual song PDFs.

This module provides functions for:
- Extracting page ranges from PDFs without re-rendering
- Creating individual song PDF files
- Writing PDFs to S3 or local filesystem
- Preserving vector content and fonts
"""

from typing import List, Optional
from pathlib import Path
import logging
import fitz  # PyMuPDF
from app.models import PageRange, OutputFile
from app.utils.sanitization import generate_output_filename, generate_output_path
from app.utils.artist_resolution import resolve_artist
from app.utils.s3_utils import S3Utils

logger = logging.getLogger(__name__)


class PDFSplitterService:
    """Service for splitting PDFs into individual song files."""
    
    def __init__(self, output_bucket: str = 'output-bucket',
                 local_mode: bool = False, local_output_path: Optional[str] = None):
        """
        Initialize PDF splitter service.
        
        Args:
            output_bucket: S3 bucket for output files
            local_mode: If True, write to local filesystem
            local_output_path: Base path for local output
        """
        self.output_bucket = output_bucket
        self.local_mode = local_mode
        self.s3_utils = S3Utils(local_mode=local_mode, local_base_path=local_output_path)
        logger.info(f"PDFSplitterService initialized (local_mode={local_mode})")
    
    def split_pdf(self, pdf_path: str, page_ranges: List[PageRange],
                  book_artist: str, book_name: str,
                  various_artists: bool = False) -> List[OutputFile]:
        """
        Split PDF into individual song files.
        
        Args:
            pdf_path: Path to source PDF file
            page_ranges: List of page ranges for each song
            book_artist: Artist name from book metadata
            book_name: Book name
            various_artists: Whether this is a Various Artists compilation
        
        Returns:
            List of OutputFile with S3 URIs or local paths
        """
        logger.info(f"Splitting PDF into {len(page_ranges)} songs")
        
        output_files = []
        
        try:
            source_doc = fitz.open(pdf_path)
            
            for page_range in page_ranges:
                try:
                    output_file = self._extract_and_save_song(
                        source_doc, page_range, book_artist, book_name, various_artists
                    )
                    if output_file:
                        output_files.append(output_file)
                except Exception as e:
                    logger.error(f"Error extracting '{page_range.song_title}': {e}")
                    # Continue processing remaining songs
            
            source_doc.close()
            
        except Exception as e:
            logger.error(f"Error opening source PDF: {e}")
            return []
        
        logger.info(f"Successfully extracted {len(output_files)}/{len(page_ranges)} songs")
        return output_files
    
    def _extract_and_save_song(self, source_doc: fitz.Document, page_range: PageRange,
                               book_artist: str, book_name: str,
                               various_artists: bool) -> Optional[OutputFile]:
        """Extract a single song and save to output."""
        # Resolve artist (use song-level artist for Various Artists)
        resolved_artist = resolve_artist(
            book_artist=book_artist,
            song_artist=page_range.artist,
            various_artists=various_artists
        )
        
        # Extract pages
        song_doc = self.extract_page_range(
            source_doc, page_range.start_page, page_range.end_page
        )
        
        if not song_doc:
            return None
        
        # Generate output path
        output_path = generate_output_path(
            output_bucket=self.output_bucket,
            artist=resolved_artist,
            book_name=book_name,
            song_title=page_range.song_title,
            song_artist=page_range.artist
        )
        
        # Write to S3 or local filesystem
        output_uri = self.write_to_s3(song_doc, output_path)
        
        # Get file size
        file_size = len(song_doc.tobytes())
        
        song_doc.close()
        
        logger.info(f"Extracted '{page_range.song_title}' to {output_uri}")
        
        return OutputFile(
            song_title=page_range.song_title,
            artist=resolved_artist,
            page_range=(page_range.start_page, page_range.end_page),
            output_uri=output_uri,
            file_size_bytes=file_size
        )
    
    def extract_page_range(self, pdf: fitz.Document, start: int, end: int) -> Optional[fitz.Document]:
        """
        Extract pages from PDF without re-rendering.
        
        Preserves vector graphics, fonts, and formatting.
        
        Args:
            pdf: Source PDF document
            start: Start page index (inclusive)
            end: End page index (exclusive)
        
        Returns:
            New PDF document with specified pages
        """
        try:
            # Create new document
            new_doc = fitz.open()
            
            # Insert pages from source
            new_doc.insert_pdf(pdf, from_page=start, to_page=end-1)
            
            logger.debug(f"Extracted pages {start} to {end-1}")
            return new_doc
            
        except Exception as e:
            logger.error(f"Error extracting page range {start}-{end}: {e}")
            return None
    
    def write_to_s3(self, pdf_doc: fitz.Document, s3_key: str) -> str:
        """
        Write PDF to S3 or local filesystem.
        
        Args:
            pdf_doc: PDF document to write
            s3_key: S3 key or relative path
        
        Returns:
            S3 URI or local path
        """
        try:
            # Convert PDF to bytes
            pdf_bytes = pdf_doc.tobytes()
            
            # Write using S3Utils (handles local mode)
            output_uri = self.s3_utils.write_bytes(
                data=pdf_bytes,
                bucket=self.output_bucket,
                key=s3_key
            )
            
            return output_uri
            
        except Exception as e:
            logger.error(f"Error writing PDF: {e}")
            raise
