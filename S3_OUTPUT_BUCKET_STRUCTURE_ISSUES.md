# S3 Output Bucket Structure Issues

**Date:** January 30, 2026  
**Analysis:** Comparison of S3 structure vs expected naming conventions

## Summary

**Total Objects in S3:** 23,629 files
- Song PDFs: 16,640
- Manifests: 1,137
- Artifacts: 5,852

**Expected:** 559 books from 127 artists
**S3 Has:** 913 book folders from 132 artists

**Difference:** 354 extra book folders (duplicates/old naming)

## Critical Issues Found

### 1. Path Duplication Bug (7 files)
**Status:** ❌ CRITICAL

Files with `s3://jsmith-output/` prefix in the key:
```
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Big Shot.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Half A Mile Away.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Honesty.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-My Life.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Rosalinda's Eyes.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Stiletto.pdf
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Zanzibar.pdf
```

**Issue:** These are the 7 songs from Billy Joel 52nd Street test run that have the bucket name duplicated in the S3 key.

**Impact:** These files are at the wrong path and need to be moved.

### 2. Duplicate Book Folders (354 duplicates)

Many books have multiple folders due to:
- Old processing runs with different naming conventions
- Retries with slightly different names
- Artist prefix in book name vs no prefix

**Examples:**

#### ACDC
- `Acdc/Acdc - Anthology` (3 songs)
- `Acdc/Anthology` (3 songs)

#### Adele
- `Adele/19 [pvg Book]` (12 songs)
- `Adele/Adele - 19 [pvg Book]` (5 songs)

#### Aerosmith
- `Aerosmith/Aerosmith - Greatest Hits (songbook)` (7 songs)
- `Aerosmith/Greatest Hits (songbook)` (15 songs)

#### Beatles (MASSIVE duplicates - 42 book folders!)
- `Beatles/Abbey Road` (17 songs)
- `Beatles/Beatles - Abbey Road` (7 songs)
- `Beatles/Beatles - Abbey Road [scores]` (6 songs)
- `Beatles/Abbey Road [scores]` (17 songs)
- `Beatles/Complete Scores` (210 songs)
- `Beatles/Beatles - Complete Scores` (167 songs)
- `Beatles/Beatles - Complete Scores (2)` (160 songs)
- `Beatles/Complete Scores (2)` (210 songs)

### 3. Inconsistent Naming Conventions

**Old Convention (with artist prefix):**
- `Billy Joel/Billy Joel - 52nd Street/`
- `Beatles/Beatles - Abbey Road/`

**New Convention (without artist prefix):**
- `Billy Joel/52nd Street/`
- `Beatles/Abbey Road/`

**Mixed Convention (some with, some without):**
- Both exist in S3 for many books

### 4. Structure Patterns

**Most Common (16,497 files):** `Artist/Book/Songs/Song.pdf`
- Has extra "Songs" subfolder
- Example: `Adele/Adele - 19 [pvg Book]/Songs/Adele - Best For Last.pdf`

**Expected (136 files):** `Artist/Book/Song.pdf`
- Direct structure without subfolder
- Example: `Adele/19 [pvg Book]/Adele - Best For Last.pdf`

**Broken (7 files):** `s3://jsmith-output/SheetMusicOut/...`
- Path duplication bug

## What Needs to Happen

### Option 1: Clean Slate (RECOMMENDED)
**Action:** Delete all song PDFs and manifests, keep artifacts, reprocess all 559 books with correct naming

**Pros:**
- Clean, consistent structure
- All books use new naming conventions
- No duplicates
- Correct paths

**Cons:**
- Requires reprocessing all 559 books (~$150-200 in AWS costs)
- Takes time (several hours)

**Steps:**
1. Keep artifacts (they have the book_id mapping)
2. Delete all song PDFs and manifests
3. Reprocess all 559 books using current pipeline
4. Verify output structure

### Option 2: Selective Cleanup
**Action:** Keep the "best" version of each book, delete duplicates

**Pros:**
- Cheaper (no reprocessing)
- Faster

**Cons:**
- Complex logic to determine "best" version
- May still have inconsistent naming
- Risk of deleting wrong files

**Steps:**
1. For each book in CSV, identify all S3 folders
2. Choose the folder with most songs (likely most complete)
3. Delete other folders
4. Move/rename to match new conventions
5. Fix the 7 Billy Joel files with path duplication

### Option 3: Keep As-Is
**Action:** Do nothing, accept the duplicates

**Pros:**
- No work required
- No cost

**Cons:**
- Confusing structure with duplicates
- Wasted storage ($0.37/month, but still wasteful)
- 7 files at wrong paths

## Recommendation

**Go with Option 1: Clean Slate**

**Why:**
1. You've already processed all 559 books successfully
2. The pipeline is working correctly now
3. Cost is reasonable (~$150-200)
4. Results in clean, consistent structure
5. Eliminates all duplicates and naming issues
6. Fixes the path duplication bug
7. You have all artifacts saved, so you can analyze what happened

**How:**
1. Backup current state (download manifests for reference)
2. Delete all song PDFs: `aws s3 rm s3://jsmith-output/ --recursive --exclude "artifacts/*" --include "*.pdf"`
3. Delete all manifests: `aws s3 rm s3://jsmith-output/ --recursive --exclude "artifacts/*" --include "manifest.json"`
4. Verify only artifacts remain
5. Reprocess all 559 books using the batch processing script
6. Verify clean structure

## Cost Estimate for Reprocessing

**Per Book:**
- TOC Discovery: ~$0.05
- TOC Parser: ~$0.10
- Page Mapper: ~$0.05
- Song Verifier: ~$0.05
- PDF Splitter: ~$0.01
- Manifest Generator: ~$0.01
- **Total per book:** ~$0.27

**For 559 books:** ~$150

**Plus ECS task costs:** ~$20-30

**Total:** ~$170-180

## Alternative: Fix Only Critical Issues

If you don't want to reprocess everything:

1. **Fix the 7 Billy Joel files** (path duplication bug)
2. **Delete obvious duplicates** (keep newest version)
3. **Accept some inconsistency** in naming conventions

This would be much cheaper but leaves the structure messy.

## Next Steps

**Decision needed:** Which option do you want to pursue?

1. Clean slate (reprocess all)
2. Selective cleanup (fix duplicates manually)
3. Fix only critical issues (7 Billy Joel files)
4. Keep as-is (do nothing)
