# Page Mapping Algorithm Analysis

## Current Status: ALGORITHM IS INCORRECT

### What We Discovered

1. **Big Shot is correct** - The first PDF extracted correctly contains "Big Shot"
2. **All other songs are wrong** - They don't contain the expected song titles

### Root Cause

The current algorithm in `app/services/page_mapper.py` is **misinterpreting the TOC page numbers**.

#### What the Algorithm Currently Does (WRONG):
```python
# Current algorithm treats TOC page differences as song lengths
current_pdf_index = first_song_pdf_index  # 8

for i, entry in enumerate(sorted_entries):
    if i < len(sorted_entries) - 1:
        # Length = next song's TOC page - this song's TOC page
        song_length = sorted_entries[i + 1].page_number - entry.page_number
    
    # Assign current PDF index to this song
    song_locations.append(SongLocation(
        song_title=entry.song_title,
        pdf_index=current_pdf_index,
        ...
    ))
    
    # Move to next song by adding the calculated length
    if song_length is not None:
        current_pdf_index += song_length
```

This produces:
- Big Shot: PDF index 8 ✅ (correct)
- Honesty: PDF index 17 ❌ (should be 17, but calculated from wrong assumption)
- My Life: PDF index 23 ❌ (should be 23)
- etc.

#### What the Algorithm SHOULD Do (CORRECT):

The TOC page numbers are **PRINTED PAGE NUMBERS** from the book, not relative offsets!

```python
# Correct algorithm:
# 1. Find first song's actual PDF index
first_song_pdf_index = 8  # Found via vision verification
first_song_toc_page = 10   # From TOC

# 2. Calculate offset
offset = first_song_pdf_index - first_song_toc_page  # 8 - 10 = -2

# 3. Apply offset to ALL TOC page numbers
for entry in toc_entries:
    pdf_index = entry.page_number + offset  # TOC page + (-2)
    song_locations.append(SongLocation(
        song_title=entry.song_title,
        pdf_index=pdf_index,
        ...
    ))
```

This produces:
- Big Shot: TOC page 10 → PDF index 8 (10 + -2)
- Honesty: TOC page 19 → PDF index 17 (19 + -2)
- My Life: TOC page 25 → PDF index 23 (25 + -2)
- Zanzibar: TOC page 33 → PDF index 31 (33 + -2)
- Stiletto: TOC page 40 → PDF index 38 (40 + -2)
- Rosalinda's Eyes: TOC page 46 → PDF index 44 (46 + -2)
- Half A Mile Away: TOC page 52 → PDF index 50 (52 + -2)
- 52nd Street: TOC page 60 → PDF index 58 (60 + -2)

### Verification Results

Using Bedrock vision on source PDF:
- **Big Shot** appears at PDF indices 8 and 9 ✅
- **Honesty** was NOT found at indices 17-21 (needs verification)
- **My Life** was NOT found at indices 23-27 (needs verification)
- **Zanzibar** was NOT found at indices 31-35 (needs verification)

### The Fix

The algorithm needs to be changed from:
- ❌ "Use TOC page differences as song lengths and apply sequentially"

To:
- ✅ "Calculate a single offset from the first song, then apply that offset to ALL TOC page numbers"

This is the **simple offset model** that was originally in the code before the recent changes.

### Next Steps

1. Revert `build_page_mapping()` to use simple offset calculation
2. Keep the vision-based verification for finding the first song
3. Apply the offset to all TOC entries
4. Rebuild Docker image and redeploy
5. Run new test execution
6. Verify extracted PDFs contain correct songs

### Additional Issue Found

**S3 Path Duplication Bug**: The S3 keys still have the bucket name duplicated:
- Actual S3 key: `s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Big Shot.pdf`
- Should be: `SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Big Shot.pdf`

This needs to be fixed in `app/utils/sanitization.py` or wherever the S3 path is generated.
