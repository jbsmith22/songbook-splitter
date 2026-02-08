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


def to_title_case(text: str) -> str:
    """
    Convert text to Title Case while preserving certain patterns.
    
    Rules:
    - First letter of each word capitalized
    - Rest lowercase
    - Preserve apostrophes and special characters
    - Handle special cases like "O'Riley", "U.S.S.R.", etc.
    
    Args:
        text: Text to convert
    
    Returns:
        Title cased text
    
    Examples:
        >>> to_title_case("HELLO WORLD")
        'Hello World'
        >>> to_title_case("don't stop")
        "Don't Stop"
        >>> to_title_case("BACK IN THE U.S.S.R.")
        'Back In The U.s.s.r.'
    """
    if not text:
        return text
    
    # Simple title case - capitalize first letter of each word
    words = text.split()
    title_cased = []
    
    for word in words:
        if not word:
            continue
        
        # Handle words with apostrophes (e.g., "don't" -> "Don't", "O'Riley" -> "O'riley")
        if "'" in word:
            parts = word.split("'")
            # Capitalize first part, lowercase rest
            titled_parts = [parts[0].capitalize()] + [p.lower() for p in parts[1:]]
            title_cased.append("'".join(titled_parts))
        else:
            # Standard title case
            title_cased.append(word.capitalize())
    
    return ' '.join(title_cased)


def clean_artist_name(artist: str) -> str:
    """
    Clean and normalize artist names.
    
    - Converts to Title Case
    - Replaces "Unknown Artist" variants
    - Cleans up long descriptive names
    - Removes "from the motion picture" type prefixes
    
    Args:
        artist: Raw artist name
    
    Returns:
        Cleaned artist name
    """
    if not artist:
        return "Unknown Artist"
    
    # Normalize whitespace
    artist = ' '.join(artist.split())
    
    # Handle "no artist" cases
    if any(phrase in artist.lower() for phrase in [
        "no artist", "not provided", "unknown", "artist name is not"
    ]):
        return "Unknown Artist"
    
    # Remove "from the motion picture" type prefixes
    if "from the" in artist.lower() and "(" in artist:
        # Extract just the names from parentheses
        import re
        match = re.search(r'\(.*?by\s+([^)]+)\)', artist, re.IGNORECASE)
        if match:
            artist = match.group(1)
    
    # Remove "Words and Music by" prefix
    if artist.lower().startswith("words and music by"):
        artist = artist[18:].strip()
    
    # Convert to title case
    artist = to_title_case(artist)
    
    return artist


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
        'Artist Feat Other'
        >>> sanitize_artist_name("Artist/Band")
        'Artist-Band'
    """
    if not artist:
        return "Unknown Artist"
    
    # Clean and normalize the artist name
    cleaned = clean_artist_name(artist)
    
    # Apply filename sanitization
    sanitized = sanitize_filename(cleaned)
    
    # Ensure length limits
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized = sanitized[:MAX_FILENAME_LENGTH].rstrip('. ')
    
    return sanitized


def sanitize_song_title(title: str) -> str:
    """
    Sanitize a song title for use in filenames.
    
    Args:
        title: The song title to sanitize
    
    Returns:
        A sanitized song title in Title Case
    
    Examples:
        >>> sanitize_song_title("SONG: PART 1")
        'Song- Part 1'
        >>> sanitize_song_title("song (live version)")
        'Song (Live Version)'
    """
    if not title:
        return "Untitled"
    
    # Convert to title case first
    title = to_title_case(title)
    
    # Then sanitize for filesystem
    return sanitize_filename(title)


def sanitize_book_name(book_name: str) -> str:
    """
    Sanitize a book name for use in directory paths.
    
    Args:
        book_name: The book name to sanitize
    
    Returns:
        A sanitized book name in Title Case
    
    Examples:
        >>> sanitize_book_name("GREATEST HITS: VOLUME 1")
        'Greatest Hits- Volume 1'
    """
    if not book_name:
        return "Unknown Book"
    
    # Convert to title case
    book_name = to_title_case(book_name)
    
    return sanitize_filename(book_name)


def generate_output_filename(artist: str, song_title: str, extension: str = "pdf") -> str:
    """
    Generate a complete output filename in the format: <Artist> - <SongTitle>.<extension>
    
    Args:
        artist: The artist name
        song_title: The song title
        extension: File extension (default: "pdf")
    
    Returns:
        A sanitized filename in the format: Artist - SongTitle.pdf
    
    Examples:
        >>> generate_output_filename("The Beatles", "Hey Jude")
        'The Beatles - Hey Jude.pdf'
        >>> generate_output_filename("ARTIST: NAME", "SONG/TITLE")
        'Artist- Name - Song-Title.pdf'
    """
    sanitized_artist = sanitize_artist_name(artist)
    sanitized_title = sanitize_song_title(song_title)
    
    # Combine with " - " separator (space-dash-space)
    base_name = f"{sanitized_artist} - {sanitized_title}"
    
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
    Generate an S3 key (not full URI) for a song PDF.
    
    Format: <BookArtist>/<BookName>/Songs/<Artist> - <SongTitle>.pdf
    
    The artist in the filename is determined by:
    - For Various Artists books: Use song_artist (each song has its own artist)
    - For single-artist books: Use book artist (all songs by same artist)
    
    Args:
        output_bucket: The S3 bucket name (not used, kept for compatibility)
        artist: The book-level artist name (used for directory AND filename for single-artist books)
        book_name: The book name
        song_title: The song title
        song_artist: Song-level artist (only used for Various Artists books)
    
    Returns:
        An S3 key (path without bucket) for the output file
    
    Examples:
        >>> generate_output_path("my-bucket", "The Beatles", "Abbey Road", "Come Together", "The Beatles")
        'The Beatles/Abbey Road/Songs/The Beatles - Come Together.pdf'
        >>> generate_output_path("my-bucket", "Various Artists", "Hits", "Song", "Artist A")
        'Various Artists/Hits/Artist A - Song.pdf'
    """
    # Sanitize all components
    sanitized_book_artist = sanitize_artist_name(artist)
    sanitized_book = sanitize_book_name(book_name)
    
    # For filename artist: The page mapper already determined the correct artist
    # based on whether this is a Various Artists book or not.
    # If song_artist is provided, use it. Otherwise use book artist.
    resolved_filename_artist = song_artist if song_artist else artist
    filename = generate_output_filename(resolved_filename_artist, song_title)
    
    # Construct S3 key: <BookArtist>/<BookName>/<filename>
    return f"{sanitized_book_artist}/{sanitized_book}/{filename}"
