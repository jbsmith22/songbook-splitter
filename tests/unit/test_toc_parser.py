"""
Unit tests for TOC parser service.
"""

import pytest
from app.services.toc_parser import TOCParser, validate_toc_entries
from app.models import TOCEntry


class TestTOCParser:
    """Test TOC parser."""
    
    @pytest.fixture
    def parser(self):
        """Create TOC parser instance."""
        return TOCParser()
    
    def test_pattern1_dots(self, parser):
        """Test Pattern 1: 'Song Title ... 42'"""
        text = """
        Amazing Grace .................. 5
        Ave Maria ...................... 12
        Canon in D ..................... 18
        """
        
        entries = parser._try_pattern1(text)
        
        assert len(entries) == 3
        assert entries[0].song_title == "Amazing Grace"
        assert entries[0].page_number == 5
        assert entries[1].song_title == "Ave Maria"
        assert entries[1].page_number == 12
    
    def test_pattern2_page_first(self, parser):
        """Test Pattern 2: '42. Song Title'"""
        text = """5. Amazing Grace
12. Ave Maria
18. Canon in D"""
        
        entries = parser._try_pattern2(text)
        
        assert len(entries) == 3
        assert entries[0].song_title == "Amazing Grace"
        assert entries[0].page_number == 5
    
    def test_pattern3_artist_in_parentheses(self, parser):
        """Test Pattern 3: 'Song Title (Artist) ... 42'"""
        text = """
        Amazing Grace (John Newton) ........ 5
        Ave Maria (Franz Schubert) ......... 12
        Canon in D (Johann Pachelbel) ...... 18
        """
        
        entries = parser._try_pattern3(text)
        
        assert len(entries) == 3
        assert entries[0].song_title == "Amazing Grace"
        assert entries[0].artist == "John Newton"
        assert entries[0].page_number == 5
    
    def test_pattern4_artist_after_hyphen(self, parser):
        """Test Pattern 4: 'Song Title - Artist ... 42'"""
        text = """
        Amazing Grace - John Newton ........ 5
        Ave Maria - Franz Schubert ......... 12
        Canon in D - Johann Pachelbel ...... 18
        """
        
        entries = parser._try_pattern4(text)
        
        assert len(entries) == 3
        assert entries[0].song_title == "Amazing Grace"
        assert entries[0].artist == "John Newton"
        assert entries[0].page_number == 5
    
    def test_pattern5_multiple_spaces(self, parser):
        """Test Pattern 5: 'Song Title    42'"""
        text = """
        Amazing Grace      5
        Ave Maria          12
        Canon in D         18
        """
        
        entries = parser._try_pattern5(text)
        
        assert len(entries) == 3
        assert entries[0].song_title == "Amazing Grace"
        assert entries[0].page_number == 5
    
    def test_deterministic_parse_selects_best_pattern(self, parser):
        """Test that deterministic parse selects pattern with most matches."""
        text = """
        Amazing Grace .................. 5
        Ave Maria ...................... 12
        Canon in D ..................... 18
        Danny Boy ...................... 24
        """
        
        entries = parser.deterministic_parse(text)
        
        assert entries is not None
        assert len(entries) == 4
        # Should use pattern 1 (dots)
        assert all(e.confidence == 0.95 for e in entries)
    
    def test_deterministic_parse_empty_text(self, parser):
        """Test parsing empty text."""
        entries = parser.deterministic_parse("")
        assert entries is None
        
        entries = parser.deterministic_parse("   ")
        assert entries is None
    
    def test_deterministic_parse_no_matches(self, parser):
        """Test parsing text with no matches."""
        text = "This is just regular text with no TOC structure."
        entries = parser.deterministic_parse(text)
        assert entries is None or len(entries) == 0
    
    def test_is_valid_title(self, parser):
        """Test title validation."""
        # Valid titles
        assert parser._is_valid_title("Amazing Grace")
        assert parser._is_valid_title("Song Title 123")
        assert parser._is_valid_title("A")  # Short but valid
        
        # Invalid titles
        assert not parser._is_valid_title("")
        assert not parser._is_valid_title("   ")
        assert not parser._is_valid_title("Contents")
        assert not parser._is_valid_title("Table of Contents")
        assert not parser._is_valid_title("123")  # No letters
    
    def test_is_valid_artist(self, parser):
        """Test artist validation."""
        # Valid artists
        assert parser._is_valid_artist("John Newton")
        assert parser._is_valid_artist("Bach")
        
        # Invalid artists
        assert not parser._is_valid_artist("")
        assert not parser._is_valid_artist("   ")
        assert not parser._is_valid_artist("123")
    
    def test_extract_artist_overrides(self, parser):
        """Test extracting artist overrides."""
        entries = [
            TOCEntry(song_title="Song 1", page_number=5, artist="Artist A"),
            TOCEntry(song_title="Song 2", page_number=10, artist="Artist B"),
            TOCEntry(song_title="Song 3", page_number=15)  # No artist
        ]
        
        overrides = parser.extract_artist_overrides(entries)
        
        assert len(overrides) == 2
        assert overrides["Song 1"] == "Artist A"
        assert overrides["Song 2"] == "Artist B"
        assert "Song 3" not in overrides
    
    def test_parse_toc_success(self, parser):
        """Test full TOC parsing with success."""
        text = """
        Table of Contents
        
        Amazing Grace .................. 5
        Ave Maria ...................... 12
        Canon in D ..................... 18
        Danny Boy ...................... 24
        Edelweiss ...................... 30
        Greensleeves ................... 36
        Hallelujah ..................... 42
        Imagine ........................ 48
        Let It Be ...................... 54
        Yesterday ...................... 60
        """
        
        result = parser.parse_toc(text)
        
        assert result.extraction_method == 'deterministic'
        assert len(result.entries) == 10
        assert result.confidence == 0.95
    
    def test_parse_toc_insufficient_entries(self, parser):
        """Test TOC parsing with too few entries."""
        text = """
        Song 1 ........ 5
        Song 2 ........ 10
        """
        
        result = parser.parse_toc(text)
        
        # Should still return result but with lower confidence
        assert len(result.entries) == 2
        assert result.confidence < 0.95


class TestValidateTOCEntries:
    """Test TOC entry validation."""
    
    def test_validate_sufficient_entries(self):
        """Test validation with sufficient entries."""
        entries = [
            TOCEntry(song_title=f"Song {i}", page_number=i*5)
            for i in range(1, 11)
        ]
        
        assert validate_toc_entries(entries, min_entries=10) is True
    
    def test_validate_insufficient_entries(self):
        """Test validation with insufficient entries."""
        entries = [
            TOCEntry(song_title=f"Song {i}", page_number=i*5)
            for i in range(1, 6)
        ]
        
        assert validate_toc_entries(entries, min_entries=10) is False
    
    def test_validate_empty_list(self):
        """Test validation with empty list."""
        assert validate_toc_entries([], min_entries=10) is False
    
    def test_validate_empty_title(self):
        """Test validation with empty title."""
        entries = [
            TOCEntry(song_title="Song 1", page_number=5),
            TOCEntry(song_title="", page_number=10),  # Empty title
            TOCEntry(song_title="Song 3", page_number=15)
        ]
        
        assert validate_toc_entries(entries, min_entries=3) is False
    
    def test_validate_invalid_page_number(self):
        """Test validation with invalid page number."""
        entries = [
            TOCEntry(song_title="Song 1", page_number=5),
            TOCEntry(song_title="Song 2", page_number=0),  # Invalid
            TOCEntry(song_title="Song 3", page_number=15)
        ]
        
        assert validate_toc_entries(entries, min_entries=3) is False
    
    def test_validate_non_increasing_page_numbers(self):
        """Test validation with mostly non-increasing page numbers."""
        entries = [
            TOCEntry(song_title=f"Song {i}", page_number=50 - i*5)
            for i in range(1, 11)
        ]
        
        # All page numbers are decreasing - should fail
        assert validate_toc_entries(entries, min_entries=10) is False
    
    def test_validate_some_non_increasing_ok(self):
        """Test validation with some non-increasing page numbers (acceptable)."""
        entries = [
            TOCEntry(song_title="Song 1", page_number=5),
            TOCEntry(song_title="Song 2", page_number=10),
            TOCEntry(song_title="Song 3", page_number=9),  # One out of order
            TOCEntry(song_title="Song 4", page_number=15),
            TOCEntry(song_title="Song 5", page_number=20),
            TOCEntry(song_title="Song 6", page_number=25),
            TOCEntry(song_title="Song 7", page_number=30),
            TOCEntry(song_title="Song 8", page_number=35),
            TOCEntry(song_title="Song 9", page_number=40),
            TOCEntry(song_title="Song 10", page_number=45)
        ]
        
        # Only 1 out of 10 is out of order - should pass
        assert validate_toc_entries(entries, min_entries=10) is True
    
    def test_validate_custom_min_entries(self):
        """Test validation with custom minimum entries."""
        entries = [
            TOCEntry(song_title=f"Song {i}", page_number=i*5)
            for i in range(1, 6)
        ]
        
        # Should pass with min_entries=5
        assert validate_toc_entries(entries, min_entries=5) is True
        
        # Should fail with min_entries=10
        assert validate_toc_entries(entries, min_entries=10) is False


class TestTOCParserIntegration:
    """Integration tests for TOC parser."""
    
    @pytest.fixture
    def parser(self):
        return TOCParser()
    
    def test_realistic_toc_format_1(self, parser):
        """Test with realistic TOC format (dots)."""
        text = """
        CONTENTS
        
        All of Me ........................... 2
        Autumn Leaves ....................... 8
        Blue Moon ........................... 14
        Fly Me to the Moon .................. 20
        Georgia on My Mind .................. 26
        I Got Rhythm ........................ 32
        Misty ............................... 38
        My Funny Valentine .................. 44
        Satin Doll .......................... 50
        Take Five ........................... 56
        """
        
        result = parser.parse_toc(text)
        
        assert result.extraction_method == 'deterministic'
        assert len(result.entries) == 10
        assert validate_toc_entries(result.entries)
    
    def test_realistic_toc_format_2(self, parser):
        """Test with realistic TOC format (various artists)."""
        text = """
        TABLE OF CONTENTS
        
        All of Me (John Legend) ............. 2
        Happy (Pharrell Williams) ........... 8
        Rolling in the Deep (Adele) ......... 14
        Shape of You (Ed Sheeran) ........... 20
        Someone Like You (Adele) ............ 26
        Stay With Me (Sam Smith) ............ 32
        Thinking Out Loud (Ed Sheeran) ...... 38
        Uptown Funk (Bruno Mars) ............ 44
        When I Was Your Man (Bruno Mars) .... 50
        All About That Bass (Meghan Trainor). 56
        """
        
        result = parser.parse_toc(text)
        
        assert result.extraction_method == 'deterministic'
        # Note: Last entry has period after artist name which may not match pattern
        assert len(result.entries) >= 9
        assert len(result.artist_overrides) >= 9
        assert result.artist_overrides.get("All of Me") == "John Legend"
