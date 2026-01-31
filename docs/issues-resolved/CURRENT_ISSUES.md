# Current Issues

## ✅ ALL ISSUES RESOLVED

As of 2026-01-25 17:45, all known issues have been resolved and the pipeline is production ready.

## Previously Resolved Issues

### 1. ✅ Song Verifier Incorrectly Adjusting Page Indices
**Status**: RESOLVED  
**Date**: 2026-01-25 17:45

**Problem**: Song verifier was searching nearby pages and finding page 46 (last page of "Half A Mile Away") as a valid song start for "Until The Night", causing incorrect page boundaries.

**Root Cause**: 
- Song verifier used `OR` logic: valid if staff lines OR title match
- Page 46 had staff lines (last page of previous song)
- Verifier thought it was a valid song start

**Solution**:
- Updated song verifier to trust page mapper's vision detection
- Changed to `AND` logic: require BOTH staff lines AND title match
- Removed nearby page search (trust vision as authoritative)
- Flag uncertainty with lower confidence instead of adjusting

**Files Modified**: `app/services/song_verifier.py`

### 2. ✅ Vision Detecting False Positives
**Status**: RESOLVED  
**Date**: 2026-01-25

**Problem**: Vision was detecting title pages and lyrics as song starts.

**Solution**: Updated vision prompts to require:
- Song title prominently displayed at top
- Music staffs with notes (actual sheet music)
- Artist name (usually present)
- Explicitly exclude title pages with no music
- Explicitly exclude lyrics within songs

**Files Modified**: `app/services/page_mapper.py`

### 3. ✅ Missing Pages in Source PDF
**Status**: HANDLED CORRECTLY  
**Date**: 2026-01-25

**Not Actually a Bug**: The algorithm correctly handles missing pages by using actual detected song start indices rather than calculating based on TOC page numbers.

**How It Works**:
- Page mapper detects actual song starts using vision
- Song verifier trusts these detections
- Page ranges calculated as (song_start, next_song_start)
- Works correctly even when pages are missing

### 4. ✅ Page Mapping Algorithm - 20 Page Search Limit
**Status**: RESOLVED  
**Date**: 2026-01-25

**Problem**: The `_find_song_forward()` method had a default `max_search=20` parameter that limited the search range.

**Solution**: Changed to use `total_pages` instead of fixed limit.

**Files Modified**: `app/services/page_mapper.py`

### 5. ✅ Vision API Image Size Limits
**Status**: RESOLVED  
**Date**: 2026-01-25

**Problem**: Some pages exceeded 5MB Bedrock vision API limit at 150 DPI.

**Solution**: Reduced DPI from 150 to 72.

**Files Modified**: `app/services/page_mapper.py`

## Pipeline Status

**PRODUCTION READY** ✅

All 9 songs from Billy Joel 52nd Street test book extracted correctly with proper page boundaries.

See `PIPELINE_SUCCESS.md` for full details.
