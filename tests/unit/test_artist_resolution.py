"""
Unit tests for artist resolution and normalization utilities.
"""

import pytest
from app.utils.artist_resolution import (
    is_various_artists,
    resolve_artist,
    normalize_artist_name,
    extract_artist_from_toc_entry,
    normalize_featuring_notation,
)


class TestIsVariousArtists:
    """Tests for is_various_artists function."""
    
    def test_various_artists_exact(self):
        """Test exact 'Various Artists' match."""
        assert is_various_artists("Various Artists") is True
    
    def test_various_artists_case_insensitive(self):
        """Test case-insensitive matching."""
        assert is_various_artists("VARIOUS ARTISTS") is True
        assert is_various_artists("various artists") is True
        assert is_various_artists("Various Artists") is True
    
    def test_various_short_form(self):
        """Test 'Various' short form."""
        assert is_various_artists("Various") is True
        assert is_various_artists("VARIOUS") is True
    
    def test_compilation(self):
        """Test 'Compilation' indicator."""
        assert is_various_artists("Compilation") is True
        assert is_various_artists("Greatest Hits Compilation") is True
    
    def test_va_abbreviations(self):
        """Test V.A. abbreviations."""
        assert is_various_artists("V.A.") is True
        assert is_various_artists("VA") is True
        assert is_various_artists("V/A") is True
    
    def test_multiple_artists(self):
        """Test 'Multiple Artists' indicator."""
        assert is_various_artists("Multiple Artists") is True
    
    def test_international_variations(self):
        """Test international variations."""
        assert is_various_artists("Varios Artistas") is True  # Spanish
        assert is_various_artists("Divers") is True  # French
    
    def test_regular_artist_names(self):
        """Test that regular artist names return False."""
        assert is_various_artists("The Beatles") is False
        assert is_various_artists("Taylor Swift") is False
        assert is_various_artists("AC/DC") is False
        assert is_various_artists("Artist Name") is False
    
    def test_empty_and_none(self):
        """Test empty and None inputs."""
        assert is_various_artists("") is False
        assert is_various_artists("   ") is False


class TestResolveArtist:
    """Tests for resolve_artist function."""
    
    def test_regular_book_uses_book_artist(self):
        """Test that regular books use the book-level artist."""
        result = resolve_artist("The Beatles", None)
        assert result == "The Beatles"
    
    def test_regular_book_ignores_song_artist(self):
        """Test that regular books ignore song-level artist."""
        result = resolve_artist("The Beatles", "John Lennon")
        assert result == "The Beatles"
    
    def test_various_artists_with_song_artist(self):
        """Test Various Artists book with song-level artist."""
        result = resolve_artist("Various Artists", "Artist A")
        assert result == "Artist A"
    
    def test_various_artists_without_song_artist(self):
        """Test Various Artists book without song-level artist."""
        result = resolve_artist("Various Artists", None)
        assert result == "Various Artists"
    
    def test_various_artists_with_empty_song_artist(self):
        """Test Various Artists book with empty song-level artist."""
        result = resolve_artist("Various Artists", "")
        assert result == "Various Artists"
        
        result = resolve_artist("Various Artists", "   ")
        assert result == "Various Artists"
    
    def test_compilation_auto_detection(self):
        """Test auto-detection of Various Artists from book name."""
        result = resolve_artist("Compilation", "Artist B")
        assert result == "Artist B"
        
        result = resolve_artist("Compilation", None)
        assert result == "Various Artists"
    
    def test_explicit_various_artists_flag(self):
        """Test explicit various_artists flag."""
        # Force Various Artists behavior even with regular name
        result = resolve_artist("Some Book", "Artist C", various_artists=True)
        assert result == "Artist C"
        
        # Force regular behavior even with Various Artists name
        result = resolve_artist("Various Artists", "Artist D", various_artists=False)
        assert result == "Various Artists"
    
    def test_empty_book_artist(self):
        """Test handling of empty book artist."""
        result = resolve_artist("", None)
        assert result == "Unknown Artist"
        
        result = resolve_artist("", "Artist E")
        assert result == "Unknown Artist"
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        result = resolve_artist("Various Artists", "  Artist F  ")
        assert result == "Artist F"


class TestNormalizeArtistName:
    """Tests for normalize_artist_name function."""
    
    def test_featuring_variations(self):
        """Test normalization of featuring variations."""
        assert normalize_artist_name("Artist feat. Other") == "Artist feat Other"
        assert normalize_artist_name("Artist ft. Other") == "Artist feat Other"
        assert normalize_artist_name("Artist featuring Other") == "Artist feat Other"
    
    def test_featuring_case_insensitive(self):
        """Test case-insensitive featuring normalization."""
        assert normalize_artist_name("Artist FEAT. Other") == "Artist feat Other"
        assert normalize_artist_name("Artist FT. Other") == "Artist feat Other"
        assert normalize_artist_name("Artist Featuring Other") == "Artist feat Other"
    
    def test_ampersand_normalization(self):
        """Test ampersand to 'and' conversion."""
        assert normalize_artist_name("Artist & Band") == "Artist and Band"
        assert normalize_artist_name("Artist&Band") == "Artist and Band"
        assert normalize_artist_name("Artist  &  Band") == "Artist and Band"
    
    def test_slash_normalization(self):
        """Test forward slash to hyphen conversion."""
        assert normalize_artist_name("Artist/Band") == "Artist-Band"
        assert normalize_artist_name("Artist / Band") == "Artist-Band"
    
    def test_special_character_removal(self):
        """Test removal/replacement of problematic special characters."""
        assert normalize_artist_name("Artist<Name>") == "Artist-Name-"
        assert normalize_artist_name('Artist"Name"') == "Artist-Name-"
        assert normalize_artist_name("Artist:Name") == "Artist-Name"
        assert normalize_artist_name("Artist|Name") == "Artist-Name"
        assert normalize_artist_name("Artist?Name") == "Artist-Name"
        assert normalize_artist_name("Artist*Name") == "Artist-Name"
        assert normalize_artist_name("Artist\\Name") == "Artist-Name"
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        assert normalize_artist_name("  Artist   Name  ") == "Artist Name"
        assert normalize_artist_name("Artist\t\tName") == "Artist Name"
        assert normalize_artist_name("Artist\nName") == "Artist Name"
    
    def test_parentheses_preserved(self):
        """Test that parentheses are preserved."""
        assert normalize_artist_name("Artist (Band)") == "Artist (Band)"
        assert normalize_artist_name("The Artist (Formerly Known)") == "The Artist (Formerly Known)"
    
    def test_apostrophes_preserved(self):
        """Test that apostrophes are preserved."""
        assert normalize_artist_name("Artist's Band") == "Artist's Band"
    
    def test_empty_input(self):
        """Test handling of empty input."""
        assert normalize_artist_name("") == "Unknown Artist"
        assert normalize_artist_name("   ") == "Unknown Artist"
    
    def test_complex_normalization(self):
        """Test complex normalization with multiple rules."""
        result = normalize_artist_name("Artist & Band feat. Other / Group")
        assert result == "Artist and Band feat Other-Group"
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        # Unicode characters should be preserved
        assert normalize_artist_name("Björk") == "Björk"
        assert normalize_artist_name("Café Tacvba") == "Café Tacvba"


class TestExtractArtistFromTocEntry:
    """Tests for extract_artist_from_toc_entry function."""
    
    def test_artist_in_parentheses(self):
        """Test extraction of artist from parentheses."""
        result = extract_artist_from_toc_entry("Song Title (Artist Name) ... 42")
        assert result == "Artist Name"
    
    def test_artist_in_parentheses_no_dots(self):
        """Test extraction without dots."""
        result = extract_artist_from_toc_entry("Song Title (Artist Name) 42")
        assert result == "Artist Name"
    
    def test_multiple_parentheses(self):
        """Test with multiple parentheses (takes first)."""
        result = extract_artist_from_toc_entry("Song (Artist) (Live) ... 42")
        assert result == "Artist"
    
    def test_song_descriptor_in_parentheses(self):
        """Test that song descriptors are not extracted as artists."""
        # These should return None because they're song descriptors
        assert extract_artist_from_toc_entry("Song Title (Live) ... 42") is None
        assert extract_artist_from_toc_entry("Song Title (Acoustic) ... 42") is None
        assert extract_artist_from_toc_entry("Song Title (Remix) ... 42") is None
        assert extract_artist_from_toc_entry("Song Title (Radio Edit) ... 42") is None
    
    def test_artist_after_hyphen(self):
        """Test extraction of artist after hyphen."""
        result = extract_artist_from_toc_entry("Song Title - Artist Name ... 42")
        assert result == "Artist Name"
    
    def test_artist_after_hyphen_no_dots(self):
        """Test extraction after hyphen without dots."""
        result = extract_artist_from_toc_entry("Song Title - Artist Name 42")
        assert result == "Artist Name"
    
    def test_no_artist_information(self):
        """Test entries without artist information."""
        assert extract_artist_from_toc_entry("Song Title ... 42") is None
        assert extract_artist_from_toc_entry("Song Title 42") is None
    
    def test_empty_input(self):
        """Test handling of empty input."""
        assert extract_artist_from_toc_entry("") is None
        assert extract_artist_from_toc_entry(None) is None
    
    def test_complex_entry(self):
        """Test complex TOC entry."""
        result = extract_artist_from_toc_entry("Beautiful Song (The Artist) .............. 123")
        assert result == "The Artist"


class TestNormalizeFeaturingNotation:
    """Tests for normalize_featuring_notation function."""
    
    def test_feat_with_period(self):
        """Test 'feat.' normalization."""
        assert normalize_featuring_notation("Artist feat. Other") == "Artist feat Other"
    
    def test_ft_with_period(self):
        """Test 'ft.' normalization."""
        assert normalize_featuring_notation("Artist ft. Other") == "Artist feat Other"
    
    def test_featuring_full_word(self):
        """Test 'featuring' normalization."""
        assert normalize_featuring_notation("Artist featuring Other") == "Artist feat Other"
    
    def test_case_insensitive(self):
        """Test case-insensitive normalization."""
        assert normalize_featuring_notation("Artist FEAT. Other") == "Artist feat Other"
        assert normalize_featuring_notation("Artist FT. Other") == "Artist feat Other"
    
    def test_multiple_featuring(self):
        """Test multiple featuring notations."""
        result = normalize_featuring_notation("Artist feat. Other ft. Another")
        assert result == "Artist feat Other feat Another"
    
    def test_no_featuring(self):
        """Test artist without featuring notation."""
        assert normalize_featuring_notation("Artist Name") == "Artist Name"
    
    def test_empty_input(self):
        """Test handling of empty input."""
        assert normalize_featuring_notation("") == ""
        assert normalize_featuring_notation(None) is None
    
    def test_whitespace_handling(self):
        """Test whitespace handling."""
        assert normalize_featuring_notation("Artist feat.Other") == "Artist feat Other"
        assert normalize_featuring_notation("Artist ft.  Other") == "Artist feat Other"


class TestIntegration:
    """Integration tests combining multiple functions."""
    
    def test_various_artists_workflow(self):
        """Test complete workflow for Various Artists book."""
        # Extract artist from TOC entry
        toc_entry = "Beautiful Song (The Artist) ... 42"
        song_artist = extract_artist_from_toc_entry(toc_entry)
        assert song_artist == "The Artist"
        
        # Resolve artist for Various Artists book
        resolved = resolve_artist("Various Artists", song_artist)
        assert resolved == "The Artist"
        
        # Normalize the resolved artist
        normalized = normalize_artist_name(resolved)
        assert normalized == "The Artist"
    
    def test_featuring_workflow(self):
        """Test workflow with featuring notation."""
        # Extract artist with featuring notation
        toc_entry = "Song Title (Artist feat. Other) ... 42"
        song_artist = extract_artist_from_toc_entry(toc_entry)
        assert song_artist == "Artist feat. Other"
        
        # Normalize featuring notation
        normalized = normalize_artist_name(song_artist)
        assert normalized == "Artist feat Other"
    
    def test_regular_book_workflow(self):
        """Test workflow for regular (non-Various Artists) book."""
        book_artist = "The Beatles"
        
        # Resolve artist (no song-level artist)
        resolved = resolve_artist(book_artist, None)
        assert resolved == "The Beatles"
        
        # Normalize
        normalized = normalize_artist_name(resolved)
        assert normalized == "The Beatles"
