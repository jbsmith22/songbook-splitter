"""
Unit tests for filename sanitization utilities.

Tests cover:
- Invalid character removal
- Unicode normalization
- Length limiting
- Edge cases (empty strings, special characters)
- Windows and S3 compatibility
"""

import pytest
from app.utils.sanitization import (
    sanitize_filename,
    sanitize_artist_name,
    sanitize_song_title,
    sanitize_book_name,
    generate_output_filename,
    generate_output_path,
    MAX_FILENAME_LENGTH,
)


class TestSanitizeFilename:
    """Tests for the sanitize_filename function."""
    
    def test_removes_invalid_windows_characters(self):
        """Test that all invalid Windows characters are removed."""
        # Test each invalid character: < > : " / \ | ? *
        assert sanitize_filename("file<name") == "file-name"
        assert sanitize_filename("file>name") == "file-name"
        assert sanitize_filename("file:name") == "file-name"
        assert sanitize_filename('file"name') == "file-name"
        assert sanitize_filename("file/name") == "file-name"
        assert sanitize_filename("file\\name") == "file-name"
        assert sanitize_filename("file|name") == "file-name"
        assert sanitize_filename("file?name") == "file-name"
        assert sanitize_filename("file*name") == "file-name"
    
    def test_removes_multiple_invalid_characters(self):
        """Test that multiple invalid characters are all replaced."""
        assert sanitize_filename("file<>:name") == "file---name"
        assert sanitize_filename("file/\\|name") == "file---name"
    
    def test_removes_control_characters(self):
        """Test that control characters (0x00-0x1F, 0x7F) are removed."""
        # Test null character
        assert sanitize_filename("file\x00name") == "file-name"
        # Test tab and newline
        assert sanitize_filename("file\tname\ntest") == "file-name-test"
        # Test DEL character
        assert sanitize_filename("file\x7Fname") == "file-name"
    
    def test_unicode_normalization_nfc(self):
        """Test that Unicode is normalized to NFC form."""
        # é can be represented as single character (U+00E9) or e + combining acute (U+0065 U+0301)
        # NFC normalization should convert to single character form
        composed = "café"  # é as single character
        decomposed = "cafe\u0301"  # e + combining acute
        
        result1 = sanitize_filename(composed)
        result2 = sanitize_filename(decomposed)
        
        # Both should produce the same result
        assert result1 == result2
        assert result1 == "café"
    
    def test_strips_leading_trailing_dots_and_spaces(self):
        """Test that leading/trailing dots and spaces are removed."""
        assert sanitize_filename("  filename  ") == "filename"
        assert sanitize_filename("..filename..") == "filename"
        assert sanitize_filename(" . filename . ") == "filename"
        assert sanitize_filename(".hidden") == "hidden"
    
    def test_length_limiting(self):
        """Test that filenames are limited to MAX_FILENAME_LENGTH characters."""
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        assert len(result) == MAX_FILENAME_LENGTH
        assert result == "a" * MAX_FILENAME_LENGTH
    
    def test_length_limiting_with_trailing_chars(self):
        """Test that trailing dots/spaces are removed after length limiting."""
        # Create a string that ends with dots after truncation
        long_name = "a" * (MAX_FILENAME_LENGTH - 5) + "....."
        result = sanitize_filename(long_name)
        assert len(result) <= MAX_FILENAME_LENGTH
        assert not result.endswith(".")
    
    def test_empty_string_returns_default(self):
        """Test that empty string returns 'unnamed'."""
        assert sanitize_filename("") == "unnamed"
    
    def test_only_invalid_chars_returns_default(self):
        """Test that string with only invalid characters returns 'unnamed'."""
        assert sanitize_filename("<>:|?*") == "unnamed"
        assert sanitize_filename("...") == "unnamed"
        assert sanitize_filename("   ") == "unnamed"
    
    def test_preserves_valid_characters(self):
        """Test that valid characters are preserved."""
        assert sanitize_filename("Song Title (Live)") == "Song Title (Live)"
        assert sanitize_filename("Track 01 - Artist") == "Track 01 - Artist"
        assert sanitize_filename("Song_Title_123") == "Song_Title_123"
    
    def test_custom_replacement_character(self):
        """Test using a custom replacement character."""
        assert sanitize_filename("file/name", replacement="_") == "file_name"
        assert sanitize_filename("file:name", replacement=" ") == "file name"


class TestSanitizeArtistName:
    """Tests for the sanitize_artist_name function."""
    
    def test_normalizes_featuring_variations(self):
        """Test that 'featuring' variations are normalized."""
        assert sanitize_artist_name("Artist feat. Other") == "Artist feat Other"
        assert sanitize_artist_name("Artist ft. Other") == "Artist feat Other"
        assert sanitize_artist_name("Artist featuring Other") == "Artist feat Other"
        assert sanitize_artist_name("Artist FEAT. Other") == "Artist feat Other"
    
    def test_removes_invalid_characters(self):
        """Test that invalid characters are removed from artist names."""
        assert sanitize_artist_name("Artist/Band") == "Artist-Band"
        assert sanitize_artist_name("Artist: The Band") == "Artist- The Band"
    
    def test_empty_artist_returns_default(self):
        """Test that empty artist name returns 'Unknown Artist'."""
        assert sanitize_artist_name("") == "Unknown Artist"
    
    def test_preserves_valid_artist_names(self):
        """Test that valid artist names are preserved."""
        assert sanitize_artist_name("The Beatles") == "The Beatles"
        assert sanitize_artist_name("AC-DC") == "AC-DC"


class TestSanitizeSongTitle:
    """Tests for the sanitize_song_title function."""
    
    def test_removes_invalid_characters(self):
        """Test that invalid characters are removed from song titles."""
        assert sanitize_song_title("Song: Part 1") == "Song- Part 1"
        assert sanitize_song_title("Song/Title") == "Song-Title"
    
    def test_empty_title_returns_default(self):
        """Test that empty song title returns 'Untitled'."""
        assert sanitize_song_title("") == "Untitled"
    
    def test_preserves_valid_titles(self):
        """Test that valid song titles are preserved."""
        assert sanitize_song_title("Song (Live Version)") == "Song (Live Version)"
        assert sanitize_song_title("Track 01") == "Track 01"


class TestSanitizeBookName:
    """Tests for the sanitize_book_name function."""
    
    def test_removes_invalid_characters(self):
        """Test that invalid characters are removed from book names."""
        assert sanitize_book_name("Greatest Hits: Volume 1") == "Greatest Hits- Volume 1"
        assert sanitize_book_name("Book/Collection") == "Book-Collection"
    
    def test_empty_book_returns_default(self):
        """Test that empty book name returns 'Unknown Book'."""
        assert sanitize_book_name("") == "Unknown Book"
    
    def test_preserves_valid_book_names(self):
        """Test that valid book names are preserved."""
        assert sanitize_book_name("Abbey Road") == "Abbey Road"
        assert sanitize_book_name("Greatest Hits (2020)") == "Greatest Hits (2020)"


class TestGenerateOutputFilename:
    """Tests for the generate_output_filename function."""
    
    def test_basic_filename_generation(self):
        """Test basic filename generation with valid inputs."""
        result = generate_output_filename("The Beatles", "Hey Jude")
        assert result == "The Beatles-Hey Jude.pdf"
    
    def test_sanitizes_artist_and_title(self):
        """Test that artist and title are sanitized."""
        result = generate_output_filename("Artist: Name", "Song/Title")
        assert result == "Artist- Name-Song-Title.pdf"
    
    def test_custom_extension(self):
        """Test using a custom file extension."""
        result = generate_output_filename("Artist", "Song", extension="txt")
        assert result == "Artist-Song.txt"
    
    def test_length_limiting_with_extension(self):
        """Test that total filename length (including extension) is limited."""
        long_artist = "a" * 150
        long_title = "b" * 150
        result = generate_output_filename(long_artist, long_title)
        
        # Total length should not exceed MAX_FILENAME_LENGTH + extension
        assert len(result) <= MAX_FILENAME_LENGTH + 4  # +4 for ".pdf"
        assert result.endswith(".pdf")
    
    def test_handles_empty_inputs(self):
        """Test handling of empty artist or title."""
        result = generate_output_filename("", "Song")
        assert result == "Unknown Artist-Song.pdf"
        
        result = generate_output_filename("Artist", "")
        assert result == "Artist-Untitled.pdf"


class TestGenerateOutputPath:
    """Tests for the generate_output_path function."""
    
    def test_basic_path_generation(self):
        """Test basic S3 path generation."""
        result = generate_output_path(
            "my-bucket",
            "The Beatles",
            "Abbey Road",
            "Come Together"
        )
        expected = "s3://my-bucket/SheetMusicOut/The Beatles/books/Abbey Road/The Beatles-Come Together.pdf"
        assert result == expected
    
    def test_song_artist_override(self):
        """Test that song-level artist overrides book-level artist."""
        result = generate_output_path(
            "my-bucket",
            "Various Artists",
            "Greatest Hits",
            "Song Title",
            song_artist="Artist A"
        )
        expected = "s3://my-bucket/SheetMusicOut/Artist A/books/Greatest Hits/Artist A-Song Title.pdf"
        assert result == expected
    
    def test_sanitizes_all_components(self):
        """Test that all path components are sanitized."""
        result = generate_output_path(
            "my-bucket",
            "Artist: Name",
            "Book/Title",
            "Song<>Title"
        )
        # Check that invalid characters are replaced in the filename
        assert "<>" not in result
        # The colon should be replaced (except in s3:// protocol)
        assert result.count(":") == 1  # Only in s3://
        # Forward slashes are valid in S3 paths as separators, but not in individual components
        # Check that the sanitized components don't have the original invalid chars
        assert "Book/Title" not in result  # Original unsanitized version shouldn't be there
        assert "Book-Title" in result  # Should be sanitized
        assert "Artist: Name" not in result  # Original unsanitized version shouldn't be there
        assert "Artist- Name" in result  # Should be sanitized
    
    def test_path_format_compliance(self):
        """Test that path follows the required format."""
        result = generate_output_path(
            "test-bucket",
            "Artist",
            "Book",
            "Song"
        )
        
        # Verify format: s3://<bucket>/SheetMusicOut/<artist>/books/<book>/<artist>-<song>.pdf
        assert result.startswith("s3://test-bucket/")
        assert "/SheetMusicOut/" in result
        assert "/books/" in result
        assert result.endswith(".pdf")
    
    def test_no_song_artist_uses_book_artist(self):
        """Test that book artist is used when no song artist is provided."""
        result = generate_output_path(
            "my-bucket",
            "The Beatles",
            "Abbey Road",
            "Come Together",
            song_artist=None
        )
        assert "The Beatles" in result
        assert result.count("The Beatles") == 2  # Once in path, once in filename


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_unicode_characters_preserved(self):
        """Test that valid Unicode characters are preserved."""
        # Test various Unicode characters
        assert "café" in sanitize_filename("café")
        assert "naïve" in sanitize_filename("naïve")
        assert "Zürich" in sanitize_filename("Zürich")
    
    def test_emoji_handling(self):
        """Test handling of emoji characters."""
        # Emojis should be preserved (they're valid Unicode)
        result = sanitize_filename("Song 🎵 Title")
        assert "🎵" in result
    
    def test_multiple_spaces_preserved(self):
        """Test that internal spaces are preserved."""
        assert sanitize_filename("Song   Title") == "Song   Title"
    
    def test_hyphen_preservation(self):
        """Test that hyphens are preserved (they're valid)."""
        assert sanitize_filename("Artist-Song-Title") == "Artist-Song-Title"
    
    def test_parentheses_and_brackets(self):
        """Test that parentheses and brackets are preserved."""
        assert sanitize_filename("Song (Live) [2020]") == "Song (Live) [2020]"
    
    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        assert sanitize_filename("Track 01 - Song 123") == "Track 01 - Song 123"
    
    def test_mixed_invalid_and_valid(self):
        """Test strings with mix of valid and invalid characters."""
        result = sanitize_filename("Song: Title (Live) / Version 2")
        assert ":" not in result
        assert "/" not in result
        assert "(Live)" in result
        assert "Version 2" in result


class TestRequirementCompliance:
    """Tests to verify compliance with specific requirements."""
    
    def test_requirement_1_3_invalid_character_removal(self):
        """Validates Requirement 1.3: Remove invalid characters."""
        # Test all specified invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            result = sanitize_filename(f"file{char}name")
            assert char not in result
    
    def test_requirement_6_4_filename_safety(self):
        """Validates Requirement 6.4: Generate safe filenames."""
        # Test that generated filenames are safe
        filename = generate_output_filename("Artist/Name", "Song:Title")
        
        # Should not contain any invalid characters
        assert not any(c in filename for c in '<>:"/\\|?*')
        
        # Should have reasonable length
        assert len(filename) <= 255
    
    def test_unicode_nfc_normalization(self):
        """Test Unicode NFC normalization as specified."""
        # Test that combining characters are normalized
        decomposed = "e\u0301"  # e + combining acute accent
        result = sanitize_filename(decomposed)
        
        # Should be normalized to composed form
        import unicodedata
        assert unicodedata.is_normalized('NFC', result)
    
    def test_length_limit_200_characters(self):
        """Test that length is limited to 200 characters as specified."""
        long_name = "x" * 300
        result = sanitize_filename(long_name)
        assert len(result) == 200
