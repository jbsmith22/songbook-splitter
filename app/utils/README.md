# Sanitization Module

The sanitization module provides utilities for creating Windows and S3-safe filenames and paths for the SheetMusic Book Splitter pipeline.

## Features

- **Invalid Character Removal**: Removes characters that are invalid on Windows filesystems: `< > : " / \ | ? *`
- **Control Character Removal**: Removes control characters (0x00-0x1F, 0x7F)
- **Unicode Normalization**: Normalizes Unicode strings to NFC (Canonical Decomposition followed by Canonical Composition)
- **Length Limiting**: Limits filenames to 200 characters for cross-platform compatibility
- **Artist Name Normalization**: Handles "featuring" notation consistently (feat., ft., featuring → feat)
- **Safe Defaults**: Returns sensible defaults for empty or invalid inputs

## Functions

### `sanitize_filename(filename: str, replacement: str = "-") -> str`

Core sanitization function that makes a filename safe for Windows and S3.

```python
from app.utils.sanitization import sanitize_filename

# Remove invalid characters
sanitize_filename("Song: The Best")  # Returns: "Song- The Best"

# Handle Unicode normalization
sanitize_filename("café")  # Returns: "café" (NFC normalized)

# Limit length
sanitize_filename("a" * 300)  # Returns: "a" * 200
```

### `sanitize_artist_name(artist: str) -> str`

Specialized function for artist names that also normalizes "featuring" variations.

```python
from app.utils.sanitization import sanitize_artist_name

sanitize_artist_name("Artist feat. Other")  # Returns: "Artist feat Other"
sanitize_artist_name("Artist ft. Other")    # Returns: "Artist feat Other"
sanitize_artist_name("Artist/Band")         # Returns: "Artist-Band"
```

### `sanitize_song_title(title: str) -> str`

Sanitizes song titles for use in filenames.

```python
from app.utils.sanitization import sanitize_song_title

sanitize_song_title("Song: Part 1")           # Returns: "Song- Part 1"
sanitize_song_title("Song (Live Version)")    # Returns: "Song (Live Version)"
```

### `sanitize_book_name(book_name: str) -> str`

Sanitizes book names for use in directory paths.

```python
from app.utils.sanitization import sanitize_book_name

sanitize_book_name("Greatest Hits: Volume 1")  # Returns: "Greatest Hits- Volume 1"
```

### `generate_output_filename(artist: str, song_title: str, extension: str = "pdf") -> str`

Generates a complete output filename in the format: `<Artist>-<SongTitle>.<extension>`

```python
from app.utils.sanitization import generate_output_filename

generate_output_filename("The Beatles", "Hey Jude")
# Returns: "The Beatles-Hey Jude.pdf"

generate_output_filename("Artist: Name", "Song/Title")
# Returns: "Artist- Name-Song-Title.pdf"
```

### `generate_output_path(output_bucket: str, artist: str, book_name: str, song_title: str, song_artist: Optional[str] = None) -> str`

Generates a complete S3 output path for a song PDF.

Format: `s3://<OUTPUT_BUCKET>/SheetMusicOut/<ResolvedArtist>/books/<BookName>/<ResolvedArtist>-<SongTitle>.pdf`

```python
from app.utils.sanitization import generate_output_path

# Basic usage
generate_output_path("my-bucket", "The Beatles", "Abbey Road", "Come Together")
# Returns: "s3://my-bucket/SheetMusicOut/The Beatles/books/Abbey Road/The Beatles-Come Together.pdf"

# Various Artists with song-level artist override
generate_output_path("my-bucket", "Various Artists", "Hits", "Song", song_artist="Artist A")
# Returns: "s3://my-bucket/SheetMusicOut/Artist A/books/Hits/Artist A-Song.pdf"
```

## Requirements Validation

This module validates the following requirements:

- **Requirement 1.3**: Sanitize filenames to be safe for both Windows filesystems and S3
- **Requirement 6.4**: Generate filenames in the format `<ResolvedArtist>-<SongTitle>.pdf` with sanitized characters

## Testing

The module includes comprehensive unit tests covering:

- Invalid character removal (all Windows-invalid characters)
- Control character removal
- Unicode normalization (NFC)
- Length limiting
- Edge cases (empty strings, only invalid characters, etc.)
- Artist name normalization (featuring variations)
- Path generation and format compliance

Run tests with:

```bash
pytest tests/unit/test_sanitization.py -v
```

## Design Decisions

### Why 200 characters?

While Windows supports up to 255 characters for filenames, we use 200 as a conservative limit to:
- Leave room for file extensions
- Account for path length limits (Windows has a 260-character total path limit)
- Provide a safety margin for various edge cases

### Why NFC normalization?

Unicode characters can be represented in multiple ways (e.g., é as a single character or e + combining accent). NFC normalization ensures consistent representation, which is important for:
- File system compatibility
- String comparison and matching
- Preventing duplicate files with different Unicode representations

### Why replace with hyphens?

Hyphens are safe across all platforms and provide good readability. They're commonly used in URLs and filenames, making them a natural choice for replacement characters.

## Future Enhancements

Potential improvements for future versions:

- Configurable replacement characters per context
- More sophisticated length limiting (e.g., smart truncation at word boundaries)
- Support for additional artist notation patterns
- Transliteration of non-Latin characters (optional)
