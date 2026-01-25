"""
Unit tests for data models.

Tests validation, serialization, and deserialization of all data model classes.
"""

import pytest
import json
from app.models import (
    TOCEntry, SongLocation, VerifiedSong, PageRange, OutputFile,
    TOCDiscoveryResult, TOCParseResult, PageMapping, Manifest
)


class TestTOCEntry:
    """Tests for TOCEntry data model."""
    
    def test_valid_toc_entry(self):
        """Test creating a valid TOC entry."""
        entry = TOCEntry(
            song_title="Amazing Grace",
            page_number=42,
            artist="Traditional",
            confidence=0.95
        )
        assert entry.validate()
        assert entry.song_title == "Amazing Grace"
        assert entry.page_number == 42
        assert entry.artist == "Traditional"
        assert entry.confidence == 0.95
    
    def test_toc_entry_without_artist(self):
        """Test TOC entry without artist (optional field)."""
        entry = TOCEntry(
            song_title="Amazing Grace",
            page_number=42
        )
        assert entry.validate()
        assert entry.artist is None
        assert entry.confidence == 1.0  # Default value
    
    def test_toc_entry_empty_title(self):
        """Test that empty title fails validation."""
        entry = TOCEntry(song_title="", page_number=42)
        assert not entry.validate()
        
        entry = TOCEntry(song_title="   ", page_number=42)
        assert not entry.validate()
    
    def test_toc_entry_invalid_page_number(self):
        """Test that invalid page numbers fail validation."""
        entry = TOCEntry(song_title="Song", page_number=0)
        assert not entry.validate()
        
        entry = TOCEntry(song_title="Song", page_number=-1)
        assert not entry.validate()
    
    def test_toc_entry_invalid_confidence(self):
        """Test that invalid confidence scores fail validation."""
        entry = TOCEntry(song_title="Song", page_number=42, confidence=-0.1)
        assert not entry.validate()
        
        entry = TOCEntry(song_title="Song", page_number=42, confidence=1.5)
        assert not entry.validate()
    
    def test_toc_entry_serialization(self):
        """Test serialization to dictionary."""
        entry = TOCEntry(
            song_title="Amazing Grace",
            page_number=42,
            artist="Traditional",
            confidence=0.95
        )
        data = entry.to_dict()
        assert data['song_title'] == "Amazing Grace"
        assert data['page_number'] == 42
        assert data['artist'] == "Traditional"
        assert data['confidence'] == 0.95
    
    def test_toc_entry_deserialization(self):
        """Test deserialization from dictionary."""
        data = {
            'song_title': "Amazing Grace",
            'page_number': 42,
            'artist': "Traditional",
            'confidence': 0.95
        }
        entry = TOCEntry.from_dict(data)
        assert entry.song_title == "Amazing Grace"
        assert entry.page_number == 42
        assert entry.artist == "Traditional"
        assert entry.confidence == 0.95


class TestSongLocation:
    """Tests for SongLocation data model."""
    
    def test_valid_song_location(self):
        """Test creating a valid song location."""
        location = SongLocation(
            song_title="Amazing Grace",
            printed_page=42,
            pdf_index=40,
            artist="Traditional"
        )
        assert location.validate()
        assert location.song_title == "Amazing Grace"
        assert location.printed_page == 42
        assert location.pdf_index == 40
    
    def test_song_location_without_artist(self):
        """Test song location without artist."""
        location = SongLocation(
            song_title="Amazing Grace",
            printed_page=42,
            pdf_index=40
        )
        assert location.validate()
        assert location.artist is None
    
    def test_song_location_invalid_fields(self):
        """Test that invalid fields fail validation."""
        # Empty title
        location = SongLocation(song_title="", printed_page=42, pdf_index=40)
        assert not location.validate()
        
        # Invalid printed page
        location = SongLocation(song_title="Song", printed_page=0, pdf_index=40)
        assert not location.validate()
        
        # Invalid PDF index
        location = SongLocation(song_title="Song", printed_page=42, pdf_index=-1)
        assert not location.validate()
    
    def test_song_location_serialization(self):
        """Test serialization and deserialization."""
        location = SongLocation(
            song_title="Amazing Grace",
            printed_page=42,
            pdf_index=40,
            artist="Traditional"
        )
        data = location.to_dict()
        restored = SongLocation.from_dict(data)
        assert restored.song_title == location.song_title
        assert restored.printed_page == location.printed_page
        assert restored.pdf_index == location.pdf_index
        assert restored.artist == location.artist


class TestVerifiedSong:
    """Tests for VerifiedSong data model."""
    
    def test_valid_verified_song(self):
        """Test creating a valid verified song."""
        song = VerifiedSong(
            song_title="Amazing Grace",
            pdf_index=40,
            verified=True,
            adjustment=2,
            confidence=0.98,
            artist="Traditional"
        )
        assert song.validate()
        assert song.verified
        assert song.adjustment == 2
    
    def test_verified_song_no_adjustment(self):
        """Test verified song with no adjustment."""
        song = VerifiedSong(
            song_title="Amazing Grace",
            pdf_index=40,
            verified=True
        )
        assert song.validate()
        assert song.adjustment == 0
        assert song.confidence == 1.0
    
    def test_verified_song_negative_adjustment(self):
        """Test verified song with negative adjustment."""
        song = VerifiedSong(
            song_title="Amazing Grace",
            pdf_index=40,
            verified=True,
            adjustment=-1
        )
        assert song.validate()
        assert song.adjustment == -1
    
    def test_verified_song_invalid_fields(self):
        """Test that invalid fields fail validation."""
        # Empty title
        song = VerifiedSong(song_title="", pdf_index=40, verified=True)
        assert not song.validate()
        
        # Invalid PDF index
        song = VerifiedSong(song_title="Song", pdf_index=-1, verified=True)
        assert not song.validate()
        
        # Invalid confidence
        song = VerifiedSong(song_title="Song", pdf_index=40, verified=True, confidence=1.5)
        assert not song.validate()
    
    def test_verified_song_serialization(self):
        """Test serialization and deserialization."""
        song = VerifiedSong(
            song_title="Amazing Grace",
            pdf_index=40,
            verified=True,
            adjustment=2,
            confidence=0.98
        )
        data = song.to_dict()
        restored = VerifiedSong.from_dict(data)
        assert restored.song_title == song.song_title
        assert restored.pdf_index == song.pdf_index
        assert restored.verified == song.verified
        assert restored.adjustment == song.adjustment


class TestPageRange:
    """Tests for PageRange data model."""
    
    def test_valid_page_range(self):
        """Test creating a valid page range."""
        page_range = PageRange(
            song_title="Amazing Grace",
            start_page=40,
            end_page=43,
            artist="Traditional"
        )
        assert page_range.validate()
        assert page_range.page_count() == 3
    
    def test_page_range_single_page(self):
        """Test page range with single page."""
        page_range = PageRange(
            song_title="Amazing Grace",
            start_page=40,
            end_page=41
        )
        assert page_range.validate()
        assert page_range.page_count() == 1
    
    def test_page_range_invalid_range(self):
        """Test that invalid ranges fail validation."""
        # End before start
        page_range = PageRange(song_title="Song", start_page=40, end_page=39)
        assert not page_range.validate()
        
        # End equals start
        page_range = PageRange(song_title="Song", start_page=40, end_page=40)
        assert not page_range.validate()
    
    def test_page_range_invalid_fields(self):
        """Test that invalid fields fail validation."""
        # Empty title
        page_range = PageRange(song_title="", start_page=40, end_page=43)
        assert not page_range.validate()
        
        # Negative start
        page_range = PageRange(song_title="Song", start_page=-1, end_page=43)
        assert not page_range.validate()
    
    def test_page_range_serialization(self):
        """Test serialization and deserialization."""
        page_range = PageRange(
            song_title="Amazing Grace",
            start_page=40,
            end_page=43,
            artist="Traditional"
        )
        data = page_range.to_dict()
        restored = PageRange.from_dict(data)
        assert restored.song_title == page_range.song_title
        assert restored.start_page == page_range.start_page
        assert restored.end_page == page_range.end_page


class TestOutputFile:
    """Tests for OutputFile data model."""
    
    def test_valid_output_file(self):
        """Test creating a valid output file."""
        output = OutputFile(
            song_title="Amazing Grace",
            artist="Traditional",
            page_range=(40, 43),
            output_uri="s3://bucket/output/Traditional-AmazingGrace.pdf",
            file_size_bytes=245678
        )
        assert output.validate()
    
    def test_output_file_invalid_page_range(self):
        """Test that invalid page ranges fail validation."""
        # End before start
        output = OutputFile(
            song_title="Song",
            artist="Artist",
            page_range=(40, 39),
            output_uri="s3://bucket/file.pdf",
            file_size_bytes=1000
        )
        assert not output.validate()
        
        # Not a tuple
        output = OutputFile(
            song_title="Song",
            artist="Artist",
            page_range=[40, 43],
            output_uri="s3://bucket/file.pdf",
            file_size_bytes=1000
        )
        assert not output.validate()
    
    def test_output_file_invalid_fields(self):
        """Test that invalid fields fail validation."""
        # Empty title
        output = OutputFile(
            song_title="",
            artist="Artist",
            page_range=(40, 43),
            output_uri="s3://bucket/file.pdf",
            file_size_bytes=1000
        )
        assert not output.validate()
        
        # Empty artist
        output = OutputFile(
            song_title="Song",
            artist="",
            page_range=(40, 43),
            output_uri="s3://bucket/file.pdf",
            file_size_bytes=1000
        )
        assert not output.validate()
        
        # Negative file size
        output = OutputFile(
            song_title="Song",
            artist="Artist",
            page_range=(40, 43),
            output_uri="s3://bucket/file.pdf",
            file_size_bytes=-1
        )
        assert not output.validate()
    
    def test_output_file_serialization(self):
        """Test serialization and deserialization."""
        output = OutputFile(
            song_title="Amazing Grace",
            artist="Traditional",
            page_range=(40, 43),
            output_uri="s3://bucket/output/Traditional-AmazingGrace.pdf",
            file_size_bytes=245678
        )
        data = output.to_dict()
        restored = OutputFile.from_dict(data)
        assert restored.song_title == output.song_title
        assert restored.artist == output.artist
        assert restored.page_range == output.page_range
        assert restored.output_uri == output.output_uri
        assert restored.file_size_bytes == output.file_size_bytes
    
    def test_output_file_deserialization_with_list(self):
        """Test deserialization converts list to tuple for page_range."""
        data = {
            'song_title': "Amazing Grace",
            'artist': "Traditional",
            'page_range': [40, 43],  # List instead of tuple
            'output_uri': "s3://bucket/output/Traditional-AmazingGrace.pdf",
            'file_size_bytes': 245678
        }
        output = OutputFile.from_dict(data)
        assert isinstance(output.page_range, tuple)
        assert output.page_range == (40, 43)


class TestTOCDiscoveryResult:
    """Tests for TOCDiscoveryResult data model."""
    
    def test_valid_toc_discovery_result(self):
        """Test creating a valid TOC discovery result."""
        result = TOCDiscoveryResult(
            toc_pages=[2, 3],
            extracted_text={2: "Contents page 1", 3: "Contents page 2"},
            confidence_scores={2: 0.95, 3: 0.92},
            textract_responses_s3_uri="s3://bucket/artifacts/textract.json"
        )
        assert result.validate()
    
    def test_toc_discovery_result_missing_text(self):
        """Test that missing extracted text fails validation."""
        result = TOCDiscoveryResult(
            toc_pages=[2, 3],
            extracted_text={2: "Contents page 1"},  # Missing page 3
            confidence_scores={2: 0.95, 3: 0.92},
            textract_responses_s3_uri="s3://bucket/artifacts/textract.json"
        )
        assert not result.validate()
    
    def test_toc_discovery_result_missing_scores(self):
        """Test that missing confidence scores fail validation."""
        result = TOCDiscoveryResult(
            toc_pages=[2, 3],
            extracted_text={2: "Contents page 1", 3: "Contents page 2"},
            confidence_scores={2: 0.95},  # Missing page 3
            textract_responses_s3_uri="s3://bucket/artifacts/textract.json"
        )
        assert not result.validate()
    
    def test_toc_discovery_result_empty_pages(self):
        """Test that empty TOC pages list fails validation."""
        result = TOCDiscoveryResult(
            toc_pages=[],
            extracted_text={},
            confidence_scores={},
            textract_responses_s3_uri="s3://bucket/artifacts/textract.json"
        )
        assert not result.validate()
    
    def test_toc_discovery_result_serialization(self):
        """Test serialization and deserialization."""
        result = TOCDiscoveryResult(
            toc_pages=[2, 3],
            extracted_text={2: "Contents page 1", 3: "Contents page 2"},
            confidence_scores={2: 0.95, 3: 0.92},
            textract_responses_s3_uri="s3://bucket/artifacts/textract.json"
        )
        data = result.to_dict()
        restored = TOCDiscoveryResult.from_dict(data)
        assert restored.toc_pages == result.toc_pages
        assert restored.extracted_text == result.extracted_text
        assert restored.confidence_scores == result.confidence_scores


class TestTOCParseResult:
    """Tests for TOCParseResult data model."""
    
    def test_valid_toc_parse_result(self):
        """Test creating a valid TOC parse result."""
        entries = [
            TOCEntry("Song 1", 10),
            TOCEntry("Song 2", 15),
            TOCEntry("Song 3", 20)
        ]
        result = TOCParseResult(
            entries=entries,
            extraction_method="deterministic",
            confidence=0.95,
            artist_overrides={"Song 2": "Different Artist"}
        )
        assert result.validate()
        assert result.entry_count() == 3
    
    def test_toc_parse_result_bedrock_method(self):
        """Test TOC parse result with Bedrock method."""
        entries = [TOCEntry("Song 1", 10)]
        result = TOCParseResult(
            entries=entries,
            extraction_method="bedrock",
            confidence=0.85
        )
        assert result.validate()
    
    def test_toc_parse_result_invalid_method(self):
        """Test that invalid extraction method fails validation."""
        entries = [TOCEntry("Song 1", 10)]
        result = TOCParseResult(
            entries=entries,
            extraction_method="unknown",
            confidence=0.95
        )
        assert not result.validate()
    
    def test_toc_parse_result_empty_entries(self):
        """Test that empty entries list fails validation."""
        result = TOCParseResult(
            entries=[],
            extraction_method="deterministic",
            confidence=0.95
        )
        assert not result.validate()
    
    def test_toc_parse_result_invalid_entry(self):
        """Test that invalid entries fail validation."""
        entries = [
            TOCEntry("Song 1", 10),
            TOCEntry("", 15)  # Invalid entry
        ]
        result = TOCParseResult(
            entries=entries,
            extraction_method="deterministic",
            confidence=0.95
        )
        assert not result.validate()
    
    def test_toc_parse_result_serialization(self):
        """Test serialization and deserialization."""
        entries = [
            TOCEntry("Song 1", 10),
            TOCEntry("Song 2", 15, artist="Artist 2")
        ]
        result = TOCParseResult(
            entries=entries,
            extraction_method="deterministic",
            confidence=0.95,
            artist_overrides={"Song 2": "Artist 2"}
        )
        data = result.to_dict()
        restored = TOCParseResult.from_dict(data)
        assert restored.entry_count() == result.entry_count()
        assert restored.extraction_method == result.extraction_method
        assert restored.confidence == result.confidence
        assert restored.artist_overrides == result.artist_overrides
        assert restored.entries[0].song_title == "Song 1"
        assert restored.entries[1].artist == "Artist 2"


class TestPageMapping:
    """Tests for PageMapping data model."""
    
    def test_valid_page_mapping(self):
        """Test creating a valid page mapping."""
        locations = [
            SongLocation("Song 1", 10, 8),
            SongLocation("Song 2", 15, 13)
        ]
        mapping = PageMapping(
            offset=-2,
            confidence=0.98,
            samples_verified=3,
            song_locations=locations
        )
        assert mapping.validate()
    
    def test_page_mapping_zero_offset(self):
        """Test page mapping with zero offset."""
        locations = [SongLocation("Song 1", 10, 10)]
        mapping = PageMapping(
            offset=0,
            confidence=0.95,
            samples_verified=1,
            song_locations=locations
        )
        assert mapping.validate()
    
    def test_page_mapping_invalid_confidence(self):
        """Test that invalid confidence fails validation."""
        locations = [SongLocation("Song 1", 10, 8)]
        mapping = PageMapping(
            offset=-2,
            confidence=1.5,
            samples_verified=3,
            song_locations=locations
        )
        assert not mapping.validate()
    
    def test_page_mapping_invalid_samples(self):
        """Test that negative samples fails validation."""
        locations = [SongLocation("Song 1", 10, 8)]
        mapping = PageMapping(
            offset=-2,
            confidence=0.98,
            samples_verified=-1,
            song_locations=locations
        )
        assert not mapping.validate()
    
    def test_page_mapping_invalid_location(self):
        """Test that invalid locations fail validation."""
        locations = [
            SongLocation("Song 1", 10, 8),
            SongLocation("", 15, 13)  # Invalid location
        ]
        mapping = PageMapping(
            offset=-2,
            confidence=0.98,
            samples_verified=3,
            song_locations=locations
        )
        assert not mapping.validate()
    
    def test_page_mapping_serialization(self):
        """Test serialization and deserialization."""
        locations = [
            SongLocation("Song 1", 10, 8),
            SongLocation("Song 2", 15, 13)
        ]
        mapping = PageMapping(
            offset=-2,
            confidence=0.98,
            samples_verified=3,
            song_locations=locations
        )
        data = mapping.to_dict()
        restored = PageMapping.from_dict(data)
        assert restored.offset == mapping.offset
        assert restored.confidence == mapping.confidence
        assert restored.samples_verified == mapping.samples_verified
        assert len(restored.song_locations) == len(mapping.song_locations)
        assert restored.song_locations[0].song_title == "Song 1"


class TestManifest:
    """Tests for Manifest data model."""
    
    def test_valid_manifest(self):
        """Test creating a valid manifest."""
        manifest = Manifest(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=245.5,
            toc_discovery={"toc_pages": [2, 3]},
            page_mapping={"offset": -2},
            verification={"success_rate": 0.95},
            output={"songs_extracted": 42},
            warnings=["Warning 1"],
            errors=[],
            cost_estimate={"total_usd": 0.15}
        )
        assert manifest.validate()
    
    def test_manifest_empty_metadata(self):
        """Test manifest with empty metadata dictionaries."""
        manifest = Manifest(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=245.5,
            toc_discovery={},
            page_mapping={},
            verification={},
            output={}
        )
        assert manifest.validate()
    
    def test_manifest_invalid_fields(self):
        """Test that invalid fields fail validation."""
        # Empty book_id
        manifest = Manifest(
            book_id="",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=245.5,
            toc_discovery={},
            page_mapping={},
            verification={},
            output={}
        )
        assert not manifest.validate()
        
        # Negative duration
        manifest = Manifest(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=-10,
            toc_discovery={},
            page_mapping={},
            verification={},
            output={}
        )
        assert not manifest.validate()
    
    def test_manifest_add_warning(self):
        """Test adding warnings to manifest."""
        manifest = Manifest.create_empty(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name"
        )
        manifest.add_warning("Warning 1")
        manifest.add_warning("Warning 2")
        assert len(manifest.warnings) == 2
        assert "Warning 1" in manifest.warnings
    
    def test_manifest_add_error(self):
        """Test adding errors to manifest."""
        manifest = Manifest.create_empty(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name"
        )
        manifest.add_error("Error 1")
        assert len(manifest.errors) == 1
        assert "Error 1" in manifest.errors
    
    def test_manifest_json_serialization(self):
        """Test JSON serialization and deserialization."""
        manifest = Manifest(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=245.5,
            toc_discovery={"toc_pages": [2, 3]},
            page_mapping={"offset": -2},
            verification={"success_rate": 0.95},
            output={"songs_extracted": 42},
            warnings=["Warning 1"],
            errors=[],
            cost_estimate={"total_usd": 0.15}
        )
        
        # Serialize to JSON
        json_str = manifest.to_json()
        assert isinstance(json_str, str)
        
        # Deserialize from JSON
        restored = Manifest.from_json(json_str)
        assert restored.book_id == manifest.book_id
        assert restored.artist == manifest.artist
        assert restored.processing_duration_seconds == manifest.processing_duration_seconds
        assert restored.warnings == manifest.warnings
    
    def test_manifest_create_empty(self):
        """Test creating an empty manifest."""
        manifest = Manifest.create_empty(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name"
        )
        assert manifest.validate()
        assert manifest.book_id == "book-123"
        assert manifest.processing_duration_seconds == 0.0
        assert len(manifest.warnings) == 0
        assert len(manifest.errors) == 0
        assert manifest.toc_discovery == {}
    
    def test_manifest_dict_serialization(self):
        """Test dictionary serialization and deserialization."""
        manifest = Manifest(
            book_id="book-123",
            source_pdf="s3://bucket/input/book.pdf",
            artist="Artist Name",
            book_name="Book Name",
            processing_timestamp="2024-01-15T10:30:00Z",
            processing_duration_seconds=245.5,
            toc_discovery={"toc_pages": [2, 3]},
            page_mapping={"offset": -2},
            verification={"success_rate": 0.95},
            output={"songs_extracted": 42}
        )
        
        # Serialize to dict
        data = manifest.to_dict()
        assert isinstance(data, dict)
        assert data['book_id'] == "book-123"
        
        # Deserialize from dict
        restored = Manifest.from_dict(data)
        assert restored.book_id == manifest.book_id
        assert restored.toc_discovery == manifest.toc_discovery
