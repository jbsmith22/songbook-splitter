"""
Data models for the SheetMusic Book Splitter pipeline.

This module defines all data structures used throughout the pipeline,
including TOC entries, song locations, verification results, and manifests.
All models use Python dataclasses for clean serialization and validation.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple
import json
from datetime import datetime, timezone


@dataclass
class TOCEntry:
    """
    Represents a single entry from a Table of Contents.
    
    Attributes:
        song_title: The title of the song
        page_number: The printed page number from the TOC
        artist: Optional per-song artist (for Various Artists books)
        confidence: Confidence score for this entry (0.0-1.0)
    """
    song_title: str
    page_number: int
    artist: Optional[str] = None
    confidence: float = 1.0
    
    def validate(self) -> bool:
        """
        Validate that the TOC entry has required fields.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.song_title or not self.song_title.strip():
            return False
        if not isinstance(self.page_number, int) or self.page_number <= 0:
            return False
        if not (0.0 <= self.confidence <= 1.0):
            return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TOCEntry':
        """Create TOCEntry from dictionary."""
        return cls(**data)


@dataclass
class SongLocation:
    """
    Represents a song's location after page mapping.
    
    Attributes:
        song_title: The title of the song
        printed_page: The printed page number from TOC
        pdf_index: The actual PDF page index (0-based)
        artist: Optional per-song artist
    """
    song_title: str
    printed_page: int
    pdf_index: int
    artist: Optional[str] = None
    
    def validate(self) -> bool:
        """
        Validate that the song location has valid fields.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.song_title or not self.song_title.strip():
            return False
        if not isinstance(self.printed_page, int) or self.printed_page <= 0:
            return False
        if not isinstance(self.pdf_index, int) or self.pdf_index < 0:
            return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SongLocation':
        """Create SongLocation from dictionary."""
        return cls(**data)


@dataclass
class VerifiedSong:
    """
    Represents a song after start page verification.
    
    Attributes:
        song_title: The title of the song
        pdf_index: The verified PDF page index (0-based)
        verified: Whether the song start was successfully verified
        adjustment: Number of pages adjusted from original (can be negative)
        confidence: Confidence score for verification (0.0-1.0)
        artist: Optional per-song artist
    """
    song_title: str
    pdf_index: int
    verified: bool
    adjustment: int = 0
    confidence: float = 1.0
    artist: Optional[str] = None
    
    def validate(self) -> bool:
        """
        Validate that the verified song has valid fields.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.song_title or not self.song_title.strip():
            return False
        if not isinstance(self.pdf_index, int) or self.pdf_index < 0:
            return False
        if not isinstance(self.verified, bool):
            return False
        if not (0.0 <= self.confidence <= 1.0):
            return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'VerifiedSong':
        """Create VerifiedSong from dictionary."""
        return cls(**data)


@dataclass
class PageRange:
    """
    Represents a page range for a song in the PDF.
    
    Attributes:
        song_title: The title of the song
        start_page: Starting page index (inclusive, 0-based)
        end_page: Ending page index (exclusive, 0-based)
        artist: Optional per-song artist
    """
    song_title: str
    start_page: int
    end_page: int
    artist: Optional[str] = None
    
    def validate(self) -> bool:
        """
        Validate that the page range is valid.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.song_title or not self.song_title.strip():
            return False
        if not isinstance(self.start_page, int) or self.start_page < 0:
            return False
        if not isinstance(self.end_page, int) or self.end_page < 0:
            return False
        if self.end_page <= self.start_page:
            return False
        return True
    
    def page_count(self) -> int:
        """Return the number of pages in this range."""
        return self.end_page - self.start_page
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PageRange':
        """Create PageRange from dictionary."""
        return cls(**data)


@dataclass
class OutputFile:
    """
    Represents an output PDF file for a song.
    
    Attributes:
        song_title: The title of the song
        artist: The artist name used in the output path
        page_range: Tuple of (start_page, end_page)
        output_uri: S3 URI or local path to the output file
        file_size_bytes: Size of the output file in bytes
    """
    song_title: str
    artist: str
    page_range: Tuple[int, int]
    output_uri: str
    file_size_bytes: int
    
    def validate(self) -> bool:
        """
        Validate that the output file has valid fields.
        
        Returns:
            True if valid, False otherwise
        """
        if not self.song_title or not self.song_title.strip():
            return False
        if not self.artist or not self.artist.strip():
            return False
        if not isinstance(self.page_range, tuple) or len(self.page_range) != 2:
            return False
        if self.page_range[1] <= self.page_range[0]:
            return False
        if not self.output_uri or not self.output_uri.strip():
            return False
        if not isinstance(self.file_size_bytes, int) or self.file_size_bytes < 0:
            return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'OutputFile':
        """Create OutputFile from dictionary."""
        # Convert list to tuple for page_range if needed
        if isinstance(data.get('page_range'), list):
            data['page_range'] = tuple(data['page_range'])
        return cls(**data)


@dataclass
class TOCDiscoveryResult:
    """
    Result of TOC discovery phase.
    
    Attributes:
        toc_pages: List of page indices identified as TOC pages
        extracted_text: Dictionary mapping page number to extracted text
        confidence_scores: Dictionary mapping page number to confidence score
        textract_responses_s3_uri: S3 URI where Textract responses are saved
    """
    toc_pages: List[int]
    extracted_text: Dict[int, str]
    confidence_scores: Dict[int, float]
    textract_responses_s3_uri: str
    
    def validate(self) -> bool:
        """
        Validate that the discovery result is valid.
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(self.toc_pages, list):
            return False
        if not self.toc_pages:  # Must have at least one TOC page
            return False
        if not isinstance(self.extracted_text, dict):
            return False
        if not isinstance(self.confidence_scores, dict):
            return False
        # All TOC pages should have extracted text and scores
        for page in self.toc_pages:
            if page not in self.extracted_text:
                return False
            if page not in self.confidence_scores:
                return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TOCDiscoveryResult':
        """Create TOCDiscoveryResult from dictionary."""
        return cls(**data)


@dataclass
class TOCParseResult:
    """
    Result of TOC parsing phase.
    
    Attributes:
        entries: List of TOCEntry objects
        extraction_method: Method used ("deterministic" or "bedrock")
        confidence: Overall confidence score for the parsing
        artist_overrides: Dictionary mapping song title to artist name
    """
    entries: List[TOCEntry]
    extraction_method: str
    confidence: float
    artist_overrides: Dict[str, str] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """
        Validate that the parse result is valid.
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(self.entries, list):
            return False
        if not self.entries:  # Must have at least one entry
            return False
        if self.extraction_method not in ["deterministic", "bedrock"]:
            return False
        if not (0.0 <= self.confidence <= 1.0):
            return False
        # Validate all entries
        for entry in self.entries:
            if not entry.validate():
                return False
        return True
    
    def entry_count(self) -> int:
        """Return the number of TOC entries."""
        return len(self.entries)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert TOCEntry objects to dicts
        data['entries'] = [entry.to_dict() if hasattr(entry, 'to_dict') else entry 
                          for entry in self.entries]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TOCParseResult':
        """Create TOCParseResult from dictionary."""
        # Convert entry dicts to TOCEntry objects
        if 'entries' in data and isinstance(data['entries'], list):
            data['entries'] = [
                TOCEntry.from_dict(e) if isinstance(e, dict) else e 
                for e in data['entries']
            ]
        return cls(**data)


@dataclass
class PageMapping:
    """
    Result of page mapping phase.
    
    Attributes:
        offset: The calculated offset (pdf_index = printed_page + offset)
        confidence: Confidence score for the offset calculation
        samples_verified: Number of samples successfully verified
        song_locations: List of SongLocation objects with mapped pages
    """
    offset: int
    confidence: float
    samples_verified: int
    song_locations: List[SongLocation]
    
    def validate(self) -> bool:
        """
        Validate that the page mapping is valid.
        
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(self.offset, int):
            return False
        if not (0.0 <= self.confidence <= 1.0):
            return False
        if not isinstance(self.samples_verified, int) or self.samples_verified < 0:
            return False
        if not isinstance(self.song_locations, list):
            return False
        # Validate all song locations
        for location in self.song_locations:
            if not location.validate():
                return False
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert SongLocation objects to dicts
        data['song_locations'] = [loc.to_dict() if hasattr(loc, 'to_dict') else loc 
                                  for loc in self.song_locations]
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PageMapping':
        """Create PageMapping from dictionary."""
        # Convert location dicts to SongLocation objects
        if 'song_locations' in data and isinstance(data['song_locations'], list):
            data['song_locations'] = [
                SongLocation.from_dict(loc) if isinstance(loc, dict) else loc 
                for loc in data['song_locations']
            ]
        return cls(**data)


@dataclass
class Manifest:
    """
    Complete manifest for a processed book.
    
    Attributes:
        book_id: Unique identifier for the book
        source_pdf: S3 URI or path to source PDF
        artist: Book-level artist name
        book_name: Name of the book
        processing_timestamp: ISO 8601 timestamp of processing
        processing_duration_seconds: Total processing time
        toc_discovery: Dictionary with TOC discovery metadata
        page_mapping: Dictionary with page mapping metadata
        verification: Dictionary with verification metadata
        output: Dictionary with output file metadata
        warnings: List of warning messages
        errors: List of error messages
        cost_estimate: Dictionary with cost breakdown
    """
    book_id: str
    source_pdf: str
    artist: str
    book_name: str
    processing_timestamp: str
    processing_duration_seconds: float
    toc_discovery: dict
    page_mapping: dict
    verification: dict
    output: dict
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    cost_estimate: dict = field(default_factory=dict)
    
    def validate(self) -> bool:
        """
        Validate that the manifest has all required fields.
        
        Returns:
            True if valid, False otherwise
        """
        # Check required string fields
        required_strings = [
            self.book_id, self.source_pdf, self.artist, 
            self.book_name, self.processing_timestamp
        ]
        for field_value in required_strings:
            if not field_value or not field_value.strip():
                return False
        
        # Check processing duration
        if not isinstance(self.processing_duration_seconds, (int, float)):
            return False
        if self.processing_duration_seconds < 0:
            return False
        
        # Check required dict fields
        required_dicts = [
            self.toc_discovery, self.page_mapping, 
            self.verification, self.output
        ]
        for field_value in required_dicts:
            if not isinstance(field_value, dict):
                return False
        
        # Check list fields
        if not isinstance(self.warnings, list):
            return False
        if not isinstance(self.errors, list):
            return False
        
        # Check cost estimate
        if not isinstance(self.cost_estimate, dict):
            return False
        
        return True
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message to the manifest."""
        self.warnings.append(warning)
    
    def add_error(self, error: str) -> None:
        """Add an error message to the manifest."""
        self.errors.append(error)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Manifest':
        """Create Manifest from dictionary."""
        return cls(**data)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Manifest':
        """Create Manifest from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    @classmethod
    def create_empty(cls, book_id: str, source_pdf: str, artist: str, book_name: str) -> 'Manifest':
        """
        Create an empty manifest with minimal required fields.
        
        Args:
            book_id: Unique identifier for the book
            source_pdf: S3 URI or path to source PDF
            artist: Book-level artist name
            book_name: Name of the book
            
        Returns:
            A new Manifest instance with empty metadata
        """
        return cls(
            book_id=book_id,
            source_pdf=source_pdf,
            artist=artist,
            book_name=book_name,
            processing_timestamp=datetime.now(timezone.utc).isoformat(),
            processing_duration_seconds=0.0,
            toc_discovery={},
            page_mapping={},
            verification={},
            output={},
            warnings=[],
            errors=[],
            cost_estimate={}
        )
