# The Correct Page Mapping Algorithm

## The Problem

The current `find_matching_page()` method only searches within ±3 pages of the TOC page number. This is fundamentally wrong because:

1. The offset could be much larger than 3 pages
2. We're guessing where to look instead of systematically finding songs
3. Vision verification is expensive, so we're trying to minimize calls - but this causes us to miss songs

## Your Solution: Systematic Page Scanning

**"You should do a png conversion of EVERY page of EVERY pdf as a first step."**

This means:

### Step 1: Render All Pages
Convert every page of the source PDF to PNG images upfront. This gives us:
- A complete visual representation of the PDF
- Ability to use vision AI on any page
- No need to re-render pages multiple times

### Step 2: Find Each Song Systematically
For each song in the TOC:
1. Start from the beginning of the PDF (or from where the last song ended)
2. Use vision AI to check each page: "Does this page contain the title '[Song Name]'?"
3. When found, record the PDF index
4. Move to the next song

### Step 3: Calculate Page Ranges
Once all songs are found:
1. Each song starts at its found PDF index
2. Each song ends at (next song's start index - 1)
3. Last song ends at the last page of the PDF

## Why This Works

1. **No assumptions about offset** - We find each song where it actually is
2. **Handles variable offsets** - If the offset changes throughout the book, we still find each song
3. **Robust** - Even if TOC page numbers are completely wrong, we still find the songs
4. **Complete** - We verify every song's actual location

## Implementation Plan

### Option A: Pre-render All Pages (Your Suggestion)
```python
def build_page_mapping(self, pdf_path: str, toc_entries: List[TOCEntry]) -> PageMapping:
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    # Step 1: Render all pages to PNG
    page_images = []
    for i in range(total_pages):
        page = doc[i]
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        page_images.append(img_bytes)
    
    # Step 2: Find each song
    song_locations = []
    search_start = 0
    
    for entry in sorted(toc_entries, key=lambda e: e.page_number):
        # Search forward from last position
        found_index = self._find_song_in_images(
            page_images, 
            entry.song_title, 
            search_start, 
            total_pages
        )
        
        if found_index is not None:
            song_locations.append(SongLocation(
                song_title=entry.song_title,
                pdf_index=found_index,
                ...
            ))
            search_start = found_index + 1
    
    doc.close()
    return PageMapping(...)
```

### Option B: Search Forward Without Pre-rendering
```python
def build_page_mapping(self, pdf_path: str, toc_entries: List[TOCEntry]) -> PageMapping:
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    
    song_locations = []
    search_start = 0
    
    for entry in sorted(toc_entries, key=lambda e: e.page_number):
        # Search forward from last position
        found_index = self._find_song_forward(
            doc, 
            entry.song_title, 
            search_start, 
            total_pages,
            max_search=total_pages  # Search entire remaining PDF
        )
        
        if found_index is not None:
            song_locations.append(SongLocation(
                song_title=entry.song_title,
                pdf_index=found_index,
                ...
            ))
            search_start = found_index + 1
    
    doc.close()
    return PageMapping(...)
```

## Cost Considerations

- **Vision API calls**: For a 60-page PDF with 9 songs, worst case is 60 calls per song = 540 calls
- **Optimization**: Start search from expected position (TOC page - estimated offset) to reduce calls
- **Better optimization**: After finding first song, calculate offset and start search near expected positions

## Recommended Approach

1. **Pre-render all pages** (your suggestion) - This allows for:
   - Batch processing
   - Caching of images
   - Parallel vision API calls if needed
   - Reuse of images for verification step

2. **Smart search order**:
   - Find first song by searching from page 0
   - Calculate initial offset
   - For remaining songs, start search at (TOC page + offset - 2) to reduce API calls
   - If not found within 10 pages, expand search

3. **Verification**:
   - After finding all songs, verify that page ranges make sense
   - Check that songs don't overlap
   - Verify song lengths are reasonable (e.g., 3-15 pages)
