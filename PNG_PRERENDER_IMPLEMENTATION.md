# PNG Pre-Rendering Implementation

**Date**: 2026-01-25
**Status**: Implemented and Deployed

---

## What Was Implemented

Implemented the "make everything a PNG file" approach as suggested by the user. The page mapper now pre-renders all pages upfront before searching for songs.

---

## Algorithm Changes

### Before (On-Demand Rendering)
```python
# Rendered pages one at a time as needed
for each song:
    for each page in search range:
        render page to PNG
        call vision API
        if found: break
```

**Problems**:
- Re-rendered pages multiple times if searching overlapped
- Inefficient memory usage
- Slower overall

### After (Pre-Rendering)
```python
# Step 1: Pre-render ALL pages upfront
page_images = []
for each page in PDF:
    render page to PNG
    store in memory

# Step 2: Search through pre-rendered images
for each song:
    for each page in search range:
        use pre-rendered image
        call vision API
        if found: break
```

**Benefits**:
- Each page rendered exactly once
- All images ready in memory
- Faster searching
- More systematic approach
- Easier to optimize (could batch vision API calls)

---

## New Methods Added

### `_render_all_pages(doc: fitz.Document) -> List[bytes]`
Pre-renders all pages of the PDF to PNG images.

**Features**:
- Renders at 72 DPI to stay under 5MB Bedrock limit
- Logs progress every 10 pages
- Handles errors gracefully (adds empty bytes as placeholder)
- Returns list of PNG image bytes

**Example Output**:
```
Pre-rendering all 59 pages to PNG...
Rendered 10/59 pages...
Rendered 20/59 pages...
...
Pre-rendering complete. 59 pages ready.
```

### `_find_song_in_images(page_images, song_title, start_index, total_pages) -> Optional[int]`
Searches through pre-rendered images to find a page with the given song title.

**Features**:
- Uses pre-rendered images (no re-rendering)
- Starts from specified index
- Searches forward through remaining pages
- Returns PDF index where song starts

### `_verify_image_match(img_bytes, expected_title) -> bool`
Uses Bedrock vision to verify if song title appears in pre-rendered image.

**Features**:
- Takes PNG bytes directly (no rendering needed)
- Converts to base64 for Bedrock API
- Same vision prompt as before
- Returns True/False

---

## Updated `build_page_mapping()` Flow

1. **Pre-render all pages** (one-time cost)
   ```python
   page_images = self._render_all_pages(doc)
   ```

2. **Find each song** using pre-rendered images
   ```python
   for entry in sorted_entries:
       actual_pdf_index = self._find_song_in_images(
           page_images, 
           entry.song_title, 
           search_start, 
           total_pages
       )
   ```

3. **Calculate offsets and confidence** (same as before)

---

## Performance Improvements

### Before
- **Rendering**: On-demand, potentially multiple times per page
- **Memory**: Low (only current page in memory)
- **Speed**: Slower (rendering overhead per search)

### After
- **Rendering**: Once per page, upfront
- **Memory**: Higher (all pages in memory)
- **Speed**: Faster (no rendering during search)

### Example (59-page PDF, 9 songs)
**Before**:
- Worst case: 59 pages × 9 songs = 531 renders
- Best case: 9 renders (if all songs found immediately)

**After**:
- Always: 59 renders (upfront) + 0 renders (during search)
- Consistent performance

---

## Memory Considerations

**59-page PDF at 72 DPI**:
- Average page size: ~1-2 MB PNG
- Total memory: ~60-120 MB for all pages
- Well within ECS Fargate limits (512 MB minimum)

**Larger PDFs** (200+ pages):
- May need to implement chunking or streaming
- Could render in batches if memory becomes an issue
- Current implementation is fine for typical sheet music books

---

## Docker Image Deployed

**Repository**: `227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest`
**Digest**: `sha256:e598704dd8fc64d39d2e4a7d399952cbf33bdd331df00ecde9304c0560be7e33`
**Pushed**: 2026-01-25

---

## Testing Readiness

✅ **Ready to test!**

The implementation is complete and deployed. The algorithm now:
1. Pre-renders all 59 pages to PNG upfront
2. Searches through pre-rendered images for each song
3. No on-demand rendering during search
4. Systematic and efficient

---

## Next Steps

1. **Run pipeline test**:
   ```powershell
   aws stepfunctions start-execution `
     --state-machine-arn "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine" `
     --input (Get-Content test-execution-input.json -Raw)
   ```

2. **Monitor execution**:
   - Check CloudWatch logs for "Pre-rendering all X pages" message
   - Verify "Pre-rendering complete" message
   - Check for "Found first song" messages

3. **Verify results**:
   - All songs should be found at correct indices
   - Big Shot at index 3
   - All extracted PDFs should contain correct songs

---

## Code Changes

**File**: `app/services/page_mapper.py`

**Methods Added**:
- `_render_all_pages()` - Pre-render all pages
- `_find_song_in_images()` - Search pre-rendered images
- `_verify_image_match()` - Vision verification on pre-rendered image

**Methods Modified**:
- `build_page_mapping()` - Now calls pre-rendering first

**Methods Kept** (for backward compatibility):
- `_find_song_forward()` - Still exists but not used
- `verify_page_match()` - Still exists but not used
- Other helper methods unchanged

---

## Advantages of This Approach

1. **Systematic**: Every page is processed exactly once
2. **Efficient**: No redundant rendering
3. **Predictable**: Consistent performance regardless of search patterns
4. **Debuggable**: Can inspect all pre-rendered images if needed
5. **Extensible**: Easy to add batch vision API calls or parallel processing
6. **User-Suggested**: Implements exactly what the user recommended

---

## Potential Future Optimizations

1. **Batch Vision API Calls**: Send multiple images in one request
2. **Parallel Processing**: Check multiple pages simultaneously
3. **Caching**: Save pre-rendered images to S3 for reuse
4. **Smart Search**: Use TOC page numbers to prioritize search order
5. **Early Exit**: Stop rendering if all songs found

For now, the current implementation is clean, efficient, and ready to test.
