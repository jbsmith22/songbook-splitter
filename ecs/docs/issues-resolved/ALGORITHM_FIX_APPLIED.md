# Algorithm Fix Applied

## The Root Cause

The `_find_song_forward()` method had a `max_search` parameter that defaulted to **20 pages**. This meant:
- If a song wasn't found within 20 pages of the search start position, it would give up
- For "Big Shot" at index 3, if we started searching from index 10 (the TOC page), we'd search indices 10-30 and miss it entirely

## The Fix

Changed this line in `build_page_mapping()`:
```python
# BEFORE (wrong - only searches 20 pages)
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages)

# AFTER (correct - searches entire remaining PDF)
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages, max_search=total_pages)
```

## How It Works Now

1. **First song**: Search from page 0 through the entire PDF until "Big Shot" is found
2. **Subsequent songs**: 
   - Calculate expected position based on TOC page differences
   - Start search from expected position
   - But search up to `total_pages` forward (i.e., the entire remaining PDF)
   - This ensures we find the song even if the offset is wrong

## Why This Will Work

- **No arbitrary limits**: We search the entire PDF if needed
- **Still optimized**: We start from expected positions to minimize vision API calls
- **Robust**: Even if TOC is completely wrong, we'll find each song

## Next Steps

1. Rebuild Docker image with this fix
2. Push to ECR
3. Run new pipeline execution
4. Verify that all songs are found at their correct indices
5. Check that extracted PDFs contain the correct songs

## Expected Results

With TOC entries:
- Big Shot (page 10) → Should find at index 3
- Honesty (page 19) → Should find at index 12 (if offset is -7)
- My Life (page 25) → Should find at index 18 (if offset is -7)
- etc.

The algorithm will now find each song wherever it actually is in the PDF.
