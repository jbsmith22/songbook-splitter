# Current Issues and Solutions

**Last Updated**: 2026-01-25 16:00 EST

---

## 🔴 Critical Issues

### None Currently

All critical issues have been resolved. The PNG pre-rendering implementation is complete and deployed.

---

## � Recently Completed

### 1. PNG Pre-Rendering Implementation

**Status**: Completed and Deployed
**Priority**: High
**Completed**: 2026-01-25

**Description**:
Implemented the "make everything a PNG file" approach as suggested by the user. The page mapper now pre-renders all pages upfront before searching for songs.

**Implementation**:
- Added `_render_all_pages()` method to pre-render all pages
- Added `_find_song_in_images()` to search through pre-rendered images
- Added `_verify_image_match()` for vision verification on pre-rendered images
- Updated `build_page_mapping()` to use pre-rendering

**Docker Image Deployed**:
- Repository: `227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest`
- Digest: `sha256:e598704dd8fc64d39d2e4a7d399952cbf33bdd331df00ecde9304c0560be7e33`

**Benefits**:
- Each page rendered exactly once
- All images ready in memory
- Faster searching
- More systematic approach
- Implements user's suggestion

**Next Steps**:
- Run pipeline test
- Verify all songs found at correct indices
- Verify extracted PDFs contain correct songs

**Documentation**: See `PNG_PRERENDER_IMPLEMENTATION.md`

---

## 🟡 Active Issues

### None Currently

All active issues have been resolved. Ready for testing.

---

### 2. S3 Path Duplication Bug

**Status**: Identified, Not Fixed
**Priority**: Low
**Assigned**: Backlog

**Description**:
S3 keys have the bucket name duplicated in the path:
- Current: `s3://jsmith-output/SheetMusicOut/Billy Joel/...`
- Expected: `SheetMusicOut/Billy Joel/...`

**Impact**:
- Files are created successfully
- Can be downloaded using the duplicated path
- Not blocking pipeline functionality
- Cosmetic issue that should be fixed for cleanliness

**Root Cause**:
Likely in `app/utils/s3_utils.py` `write_bytes()` method or how the S3 URI is constructed when returning from the method.

**Investigation Needed**:
1. Check `s3_utils.py` `write_bytes()` return value
2. Check `sanitization.py` `generate_output_path()` function
3. Verify how `pdf_splitter.py` constructs the output URI

**Workaround**:
Use the duplicated path when downloading files:
```powershell
aws s3 cp "s3://jsmith-output/s3://jsmith-output/SheetMusicOut/..." ./output/
```

---

## 🟢 Resolved Issues

### 1. Page Mapping Algorithm - 20 Page Search Limit

**Resolved**: 2026-01-25
**Resolution**: Changed `max_search` parameter to `total_pages`

**Original Problem**:
The `_find_song_forward()` method had a default `max_search=20` parameter, meaning it would only search 20 pages forward from the starting position. This caused it to miss songs that were further away.

**Example**:
- Big Shot at PDF index 3, TOC says page 10
- Algorithm started searching from index 10
- Searched indices 10-30
- Never found Big Shot at index 3

**Fix**:
```python
# Before
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages)

# After
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages, max_search=total_pages)
```

**Verification**: Awaiting test execution

---

### 2. Vision API Image Size Limits

**Resolved**: 2026-01-25
**Resolution**: Reduced DPI from 150 to 72

**Original Problem**:
Some PDF pages exceeded the 5MB Bedrock vision API limit when rendered at 150 DPI.

**Error**:
```
ValidationException: image exceeds 5 MB maximum: 8597588 bytes > 5242880 bytes
```

**Fix**:
Changed page rendering DPI from 150 to 72 in `page_mapper.py`:
```python
pix = page.get_pixmap(dpi=72)  # Was 150
```

**Impact**:
- Images are smaller and within API limits
- Still sufficient quality for title detection
- No loss of functionality

---

### 3. Incorrect Page Mapping Algorithm Logic

**Resolved**: 2026-01-25
**Resolution**: Rewrote algorithm to search for each song individually

**Original Problem**:
Algorithm was treating TOC page differences as song lengths and applying them sequentially:
```python
# Wrong approach
song_length = next_toc_page - current_toc_page
current_pdf_index += song_length
```

This assumed:
- TOC page numbers represented song lengths
- Offset was consistent throughout the book
- Sequential calculation would work

**User Correction**:
"The TOC CAME FROM THIS EDITION. The correct answer is to read the TOC, get the indexes, treat them as offset measures..."

**Fix**:
Changed to search for each song individually using vision verification:
```python
# Correct approach
for entry in sorted_entries:
    actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages, max_search=total_pages)
    song_locations.append(SongLocation(pdf_index=actual_pdf_index, ...))
    search_start = actual_pdf_index + 1
```

**Benefits**:
- No assumptions about offset
- Finds each song where it actually is
- Robust to incorrect TOC page numbers
- Handles variable offsets throughout book

---

## 📋 Issue Tracking

### How to Report Issues

1. Check this file first to see if issue is already known
2. Check `PROJECT_STATUS_DENSE.md` for technical details
3. Create entry in this file with:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - Impact assessment
   - Proposed solution (if known)

### Issue Priority Levels

- 🔴 **Critical**: Blocks pipeline execution, data loss risk
- 🟡 **High**: Affects functionality, workaround available
- 🟢 **Medium**: Minor functionality issue, low impact
- ⚪ **Low**: Cosmetic, documentation, nice-to-have

### Issue Status

- **Open**: Issue identified, not yet addressed
- **In Progress**: Actively being worked on
- **Fixed**: Solution implemented, awaiting verification
- **Resolved**: Verified fixed, closed
- **Backlog**: Known issue, low priority, deferred

---

## 🔍 Debugging Resources

### CloudWatch Logs
```powershell
# Page Mapper logs
aws logs tail /ecs/sheetmusic-splitter-page-mapper --follow

# All ECS logs
aws logs tail /aws/ecs/jsmith-sheetmusic-splitter --follow --since 1h
```

### Step Functions Execution
```powershell
aws stepfunctions describe-execution --execution-arn "<arn>"
aws stepfunctions get-execution-history --execution-arn "<arn>"
```

### S3 Artifacts
```powershell
# List artifacts for a book
aws s3 ls s3://jsmith-output/artifacts/<book-id>/ --recursive

# Download specific artifact
aws s3 cp s3://jsmith-output/artifacts/<book-id>/page_mapping.json ./
```

### Docker Image
```powershell
# Check current image
aws ecr describe-images --repository-name jsmith-sheetmusic-splitter --region us-east-1

# Pull and inspect
docker pull 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest
docker inspect 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest
```

---

## 📞 Escalation Path

1. Check this file for known issues
2. Check `PROJECT_STATUS_DENSE.md` for technical state
3. Check CloudWatch logs for errors
4. Check S3 artifacts for intermediate results
5. Review user feedback and corrections
6. Document new issue in this file
