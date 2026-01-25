"""
Artist resolution and normalization utilities.

This module provides functions to resolve artist names for Various Artists compilations
and normalize artist names for consistent formatting and filesystem safety.
"""

import re
from typing import Optional


def is_various_artists(artist: str) -> bool:
    """
    Determine if an artist name indicates a Various Artists compilation.
    
    Args:
        artist: The artist name to check
    
    Returns:
        True if the artist indicates Various Artists, False otherwise
    
    Examples:
        >>> is_various_artists("Various Artists")
        True
        >>> is_various_artists("Various")
        True
        >>> is_various_artists("Compilation")
        True
        >>> is_various_artists("The Beatles")
        False
    """
    if not artist:
        return False
    
    # Normalize to lowercase for comparison
    normalized = artist.lower().strip()
    
    # Check for common Various Artists indicators
    various_indicators = [
        'various artists',
        'various',
        'compilation',
        'va',
        'v.a.',
        'v/a',
        'multiple artists',
        'varios artistas',  # Spanish
        'divers',  # French
    ]
    
    return any(indicator in normalized for indicator in various_indicators)


def resolve_artist(
    book_artist: str,
    song_artist: Optional[str] = None,
    various_artists: Optional[bool] = None
) -> str:
    """
    Resolve the artist name for a song, handling Various Artists compilations.
    
    For Various Artists books:
    - If a song-level artist is provided, use it
    - Otherwise, use "Various Artists" as the artist name
    
    For regular books:
    - Use the book-level artist
    - Song-level artist is ignored (unless explicitly Various Artists)
    
    Args:
        book_artist: The book-level artist name
        song_artist: Optional song-level artist name (for Various Artists books)
        various_artists: Optional explicit flag indicating Various Artists book.
                        If None, will be auto-detected from book_artist.
    
    Returns:
        The resolved artist name to use for output paths and filenames
    
    Examples:
        >>> resolve_artist("The Beatles", None)
        'The Beatles'
        >>> resolve_artist("Various Artists", "Artist A")
        'Artist A'
        >>> resolve_artist("Various Artists", None)
        'Various Artists'
        >>> resolve_artist("Compilation", "Artist B", various_artists=True)
        'Artist B'
    """
    if not book_artist:
        book_artist = "Unknown Artist"
    
    # Auto-detect Various Artists if not explicitly specified
    if various_artists is None:
        various_artists = is_various_artists(book_artist)
    
    # For Various Artists books, prefer song-level artist
    if various_artists:
        if song_artist and song_artist.strip():
            return song_artist.strip()
        else:
            # No song-level artist provided, use "Various Artists"
            return "Various Artists"
    
    # For regular books, use book-level artist
    return book_artist


def normalize_artist_name(artist: str, replacement: str = "-") -> str:
    """
    Normalize an artist name for consistent formatting.
    
    This function:
    - Handles "featuring" notation consistently (feat., ft., featuring -> feat)
    - Removes/replaces special characters except hyphens and spaces
    - Normalizes whitespace
    - Preserves parentheses for grouping (e.g., "Artist (Band)")
    - Makes the name safe for filesystem paths
    
    Args:
        artist: The artist name to normalize
        replacement: Character to replace invalid characters with (default: "-")
    
    Returns:
        A normalized artist name
    
    Examples:
        >>> normalize_artist_name("Artist feat. Other")
        'Artist feat Other'
        >>> normalize_artist_name("Artist ft. Other")
        'Artist feat Other'
        >>> normalize_artist_name("Artist featuring Other")
        'Artist feat Other'
        >>> normalize_artist_name("Artist & Band")
        'Artist and Band'
        >>> normalize_artist_name("Artist/Band")
        'Artist-Band'
        >>> normalize_artist_name("  Artist   Name  ")
        'Artist Name'
        >>> normalize_artist_name("Artist: Name")
        'Artist- Name'
    """
    if not artist:
        return "Unknown Artist"
    
    # Start with the original artist name
    normalized = artist.strip()
    
    # Normalize "featuring" variations to "feat"
    # Handle: "feat.", "ft.", "featuring"
    normalized = re.sub(r'\bfeat\.\s*', 'feat ', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bft\.\s*', 'feat ', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bfeaturing\s+', 'feat ', normalized, flags=re.IGNORECASE)
    
    # Normalize ampersand to "and"
    normalized = re.sub(r'\s*&\s*', ' and ', normalized)
    
    # Replace forward slashes with hyphens (common in band names)
    normalized = re.sub(r'\s*/\s*', '-', normalized)
    
    # Remove/replace special characters that are problematic for filesystems
    # Keep: letters, numbers, spaces, hyphens, parentheses, apostrophes
    # Replace: < > : " \ | ? * and other special chars with replacement character
    normalized = re.sub(r'[<>:"|?*\\]', replacement, normalized)
    
    # Normalize multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Remove leading/trailing spaces
    normalized = normalized.strip()
    
    # If the result is empty, return a default
    if not normalized:
        return "Unknown Artist"
    
    return normalized


def extract_artist_from_toc_entry(toc_entry: str) -> Optional[str]:
    """
    Extract artist information from a TOC entry string.
    
    Common patterns:
    - "Song Title (Artist Name) ... 42"
    - "Song Title - Artist Name ... 42"
    - "Artist Name - Song Title ... 42"
    
    Args:
        toc_entry: A single line from the Table of Contents
    
    Returns:
        The extracted artist name, or None if no artist found
    
    Examples:
        >>> extract_artist_from_toc_entry("Song Title (Artist Name) ... 42")
        'Artist Name'
        >>> extract_artist_from_toc_entry("Song Title - Artist Name ... 42")
        'Artist Name'
        >>> extract_artist_from_toc_entry("Song Title ... 42")
        None
    """
    if not toc_entry:
        return None
    
    # Pattern 1: Artist in parentheses - "Song Title (Artist Name)"
    # This is the most common pattern for Various Artists books
    match = re.search(r'\(([^)]+)\)', toc_entry)
    if match:
        potential_artist = match.group(1).strip()
        # Verify it's not a song descriptor like "(Live)" or "(Acoustic)"
        descriptors = ['live', 'acoustic', 'remix', 'version', 'edit', 'mix', 'instrumental']
        if not any(desc in potential_artist.lower() for desc in descriptors):
            return potential_artist
    
    # Pattern 2: Artist after hyphen - "Song Title - Artist Name"
    # Split by hyphen and check if the second part looks like an artist
    if ' - ' in toc_entry:
        parts = toc_entry.split(' - ')
        if len(parts) >= 2:
            # Take the part after the first hyphen, before any page numbers
            potential_artist = parts[1].split('...')[0].strip()
            # Remove page numbers if present
            potential_artist = re.sub(r'\s+\d+\s*$', '', potential_artist).strip()
            if potential_artist and len(potential_artist) > 2:
                return potential_artist
    
    # No artist found
    return None


def normalize_featuring_notation(artist: str) -> str:
    """
    Normalize "featuring" notation in artist names.
    
    This is a focused function that only handles featuring notation,
    useful when you want to normalize just this aspect without other changes.
    
    Args:
        artist: The artist name with potential featuring notation
    
    Returns:
        Artist name with normalized featuring notation
    
    Examples:
        >>> normalize_featuring_notation("Artist feat. Other")
        'Artist feat Other'
        >>> normalize_featuring_notation("Artist ft. Other")
        'Artist feat Other'
        >>> normalize_featuring_notation("Artist featuring Other")
        'Artist feat Other'
    """
    if not artist:
        return artist
    
    # Normalize all variations to "feat"
    normalized = re.sub(r'\bfeat\.\s*', 'feat ', artist, flags=re.IGNORECASE)
    normalized = re.sub(r'\bft\.\s*', 'feat ', normalized, flags=re.IGNORECASE)
    normalized = re.sub(r'\bfeaturing\s+', 'feat ', normalized, flags=re.IGNORECASE)
    
    return normalized.strip()
