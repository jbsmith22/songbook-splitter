# Page Mapping Fix Summary

## What You Told Me (The Correct Algorithm)

From your instruction:
> "If the TOC indicates a song starts on 'page 10' and you discover it starts at pdf index 15, then it is reasonable to assume that ALL of the songs in the table of contents will be right shifted by 5."

And you told me:
> "the first song starts on pdf index 3 NOT 8"

This means:
1. Find the first song's actual PDF index using vision verification
2. Calculate the offset: `actual_pdf_index - toc_page_number`
3. **Apply that same offset to ALL TOC entries**

Example with CORRECT data:
- TOC says "Big Shot" is on page 10
- **You told me it actually starts at PDF index 3**
- Offset = 3 - 10 = **-7**
- Apply -7 to ALL songs:
  - Big Shot: page 10 → index 3 (10 + -7)
  - Honesty: page 19 → index 12 (19 + -7)
  - My Life: page 25 → index 18 (25 + -7)
  - Zanzibar: page 33 → index 26 (33 + -7)
  - Stiletto: page 40 → index 33 (40 + -7)
  - Rosalinda's Eyes: page 46 → index 39 (46 + -7)
  - Half A Mile Away: page 52 → index 45 (52 + -7)
  - 52nd Street: page 60 → index 53 (60 + -7)

## What the Current Code Does (WRONG)

The current `build_page_mapping()` method calculates song lengths from TOC page differences and applies them sequentially:

```python
current_pdf_index = first_song_pdf_index  # 8

for i, entry in enumerate(sorted_entries):
    if i < len(sorted_entries) - 1:
        song_length = sorted_entries[i + 1].page_number - entry.page_number
    
    song_locations.append(SongLocation(
        pdf_index=current_pdf_index,  # Wrong!
        ...
    ))
    
    if song_length is not None:
        current_pdf_index += song_length  # Wrong approach!
```

## The Fix

Change `build_page_mapping()` to use simple offset:

```python
# 1. Find first song
first_song_pdf_index = self.find_matching_page(pdf_path, sorted_entries[0])

# 2. Calculate offset
offset = first_song_pdf_index - sorted_entries[0].page_number

# 3. Apply offset to ALL entries
for entry in sorted_entries:
    pdf_index = entry.page_number + offset
    song_locations.append(SongLocation(
        song_title=entry.song_title,
        pdf_index=pdf_index,
        ...
    ))
```

## Files to Fix

1. **`app/services/page_mapper.py`** - Fix the `build_page_mapping()` method
2. **Rebuild Docker image** - Push new image to ECR
3. **Run new test** - Execute pipeline again
4. **Verify results** - Check that all extracted PDFs contain correct songs

## S3 Path Bug (Separate Issue)

The S3 keys have the bucket name duplicated:
- Current: `s3://jsmith-output/SheetMusicOut/...`
- Should be: `SheetMusicOut/...`

This appears to be in how the S3 URI is constructed when returning from `write_bytes()`.
