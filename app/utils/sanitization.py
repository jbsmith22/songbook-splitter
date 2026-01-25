"""
Filename sanitization utilities for Windows and S3 compatibility.

This module provides functions to sanitize filenames and paths to ensure they are
safe for both Windows filesystems and S3 object keys.
"""

import re
import unicodedata
from typing import Optional


# Invalid characters for Windows filenames: < > : " / \ | ? *
# Also includes control characters (0x00-0x1F, 0x7F)
INVALID_CHARS_PATTERN = re.compile(r'[<>:"/\\|?*\x00-\x1F\x7F]')

# Maximum filename length (conservative limit for cross-platform compatibility)
MAX_FILENAME_LENGTH = 200


def sanitize_filename(filename: str, replacement: str = "-") -> str:
    """
    Sanitize a filename to be safe for Windows filesystems and S3.
    
    This function:
    - Removes invalid characters: < > : " / \\ | ? *
    - Removes control characters (0x00-0x1F, 0x7F)
    - Normalizes Unicode to NFC form
    - Limits length to 200 characters
    - Removes leading/trailing dots and spaces
    - Ensures the result is not empty
    
    Args:
        filename: The filename to sanitize
        replacement: Character to replace invalid characters with (default: "-")
    
    Returns:
        A sanitized filename safe for Windows and S3
    
    Examples:
        >>> sanitize_filename("Song: The Best")
        'Song- The Best'
        >>> sanitize_filename("Artist/Song")
        'Artist-Song'
        >>> sanitize_filename("Song<>Title")
        'Song--Title'
    """
    if not filename:
        return "unnamed"
    
    # Normalize Unicode to NFC (Canonical Decomposition, followed by Canonical Composition)
    # This ensures consistent representation of characters like é (e + combining acute)
    normalized = unicodedata.normalize('NFC', filename)
    
    # Replace invalid characters with the replacement character
    sanitized = INVALID_CHARS_PATTERN.sub(replacement, normalized)
    
    # Remove leading/trailing dots and spaces (Windows doesn't allow these)
    sanitized = sanitized.strip('. ')
    
    # If the result is empty or only contains replacement characters, use a default name
    if not sanitized or sanitized.replace(replacement, '').strip() == '':
        return "unnamed"
    
    # Limit length to MAX_FILENAME_LENGTH characters
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized = sanitized[:MAX_FILENAME_LENGTH].rstrip('. ')
    
    return sanitized


def sanitize_artist_name(artist: str) -> str:
    """
    Sanitize an artist name for use in file paths.
    
    This function combines artist name normalization with filename sanitization
    to produce filesystem-safe artist names.
    
    Args:
        artist: The artist name to sanitize
    
    Returns:
        A sanitized artist name
    
    Examples:
        >>> sanitize_artist_name("Artist feat. Other")
        'Artist feat Other'
        >>> sanitize_artist_name("Artist/Band")
        'Artist-Band'
    """
    # Import here to avoid circular dependency
    from .artist_resolution import normalize_artist_name as normalize_artist
    
    if not artist:
        return "Unknown Artist"
    
    # Use the artist resolution module for normalization
    normalized = normalize_artist(artist)
    
    # Apply additional filename sanitization if needed
    # (normalize_artist already handles most of this, but we ensure length limits)
    if len(normalized) > MAX_FILENAME_LENGTH:
        normalized = normalized[:MAX_FILENAME_LENGTH].rstrip('. ')
    
    return normalized


def sanitize_song_title(title: str) -> str:
    """
    Sanitize a song title for use in filenames.
    
    Args:
        title: The song title to sanitize
    
    Returns:
        A sanitized song title
    
    Examples:
        >>> sanitize_song_title("Song: Part 1")
        'Song- Part 1'
        >>> sanitize_song_title("Song (Live Version)")
        'Song (Live Version)'
    """
    if not title:
        return "Untitled"
    
    return sanitize_filename(title)


def sanitize_book_name(book_name: str) -> str:
    """
    Sanitize a book name for use in directory paths.
    
    Args:
        book_name: The book name to sanitize
    
    Returns:
        A sanitized book name
    
    Examples:
        >>> sanitize_book_name("Greatest Hits: Volume 1")
        'Greatest Hits- Volume 1'
    """
    if not book_name:
        return "Unknown Book"
    
    return sanitize_filename(book_name)


def generate_output_filename(artist: str, song_title: str, extension: str = "pdf") -> str:
    """
    Generate a complete output filename in the format: <Artist>-<SongTitle>.<extension>
    
    Args:
        artist: The artist name
        song_title: The song title
        extension: File extension (default: "pdf")
    
    Returns:
        A sanitized filename in the format: Artist-SongTitle.pdf
    
    Examples:
        >>> generate_output_filename("The Beatles", "Hey Jude")
        'The Beatles-Hey Jude.pdf'
        >>> generate_output_filename("Artist: Name", "Song/Title")
        'Artist- Name-Song-Title.pdf'
    """
    sanitized_artist = sanitize_artist_name(artist)
    sanitized_title = sanitize_song_title(song_title)
    
    # Combine with hyphen separator
    base_name = f"{sanitized_artist}-{sanitized_title}"
    
    # Ensure the complete filename (with extension) doesn't exceed the limit
    max_base_length = MAX_FILENAME_LENGTH - len(extension) - 1  # -1 for the dot
    if len(base_name) > max_base_length:
        base_name = base_name[:max_base_length].rstrip('. -')
    
    return f"{base_name}.{extension}"


def generate_output_path(
    output_bucket: str,
    artist: str,
    book_name: str,
    song_title: str,
    song_artist: Optional[str] = None
) -> str:
    """
    Generate a complete S3 output path for a song PDF.
    
    Format: s3://<OUTPUT_BUCKET>/SheetMusicOut/<ResolvedArtist>/books/<BookName>/<ResolvedArtist>-<SongTitle>.pdf
    
    Args:
        output_bucket: The S3 bucket name
        artist: The book-level artist name
        book_name: The book name
        song_title: The song title
        song_artist: Optional song-level artist (for Various Artists books)
    
    Returns:
        A complete S3 path for the output file
    
    Examples:
        >>> generate_output_path("my-bucket", "The Beatles", "Abbey Road", "Come Together")
        's3://my-bucket/SheetMusicOut/The Beatles/books/Abbey Road/The Beatles-Come Together.pdf'
        >>> generate_output_path("my-bucket", "Various Artists", "Hits", "Song", "Artist A")
        's3://my-bucket/SheetMusicOut/Artist A/books/Hits/Artist A-Song.pdf'
    """
    # Resolve artist (song-level overrides book-level)
    resolved_artist = song_artist if song_artist else artist
    
    # Sanitize all components
    sanitized_artist = sanitize_artist_name(resolved_artist)
    sanitized_book = sanitize_book_name(book_name)
    filename = generate_output_filename(sanitized_artist, song_title)
    
    # Construct S3 path
    # Note: S3 uses forward slashes, which is fine since we've sanitized the components
    return f"s3://{output_bucket}/SheetMusicOut/{sanitized_artist}/books/{sanitized_book}/{filename}"
