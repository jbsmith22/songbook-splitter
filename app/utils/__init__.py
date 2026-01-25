"""Utility modules for the SheetMusic Book Splitter."""

from .sanitization import (
    sanitize_filename,
    sanitize_artist_name,
    sanitize_song_title,
    sanitize_book_name,
    generate_output_filename,
    generate_output_path,
)

from .artist_resolution import (
    is_various_artists,
    resolve_artist,
    normalize_artist_name,
    extract_artist_from_toc_entry,
    normalize_featuring_notation,
)

__all__ = [
    # Sanitization functions
    'sanitize_filename',
    'sanitize_artist_name',
    'sanitize_song_title',
    'sanitize_book_name',
    'generate_output_filename',
    'generate_output_path',
    # Artist resolution functions
    'is_various_artists',
    'resolve_artist',
    'normalize_artist_name',
    'extract_artist_from_toc_entry',
    'normalize_featuring_notation',
]
