# S3 Output Bucket - Decision Required

**Date:** January 30, 2026  
**Status:** Analysis Complete - Awaiting Decision

## Current State

**S3 Output Bucket (`jsmith-output`):**
- Total objects: 23,629 files
- Song PDFs: 16,640 files (16.15 GB)
- Manifests: 1,137 files (0.60 MB)
- Artifacts: 5,852 files (21.79 MB)
- Cost: $0.37/month

**Expected (from CSV):**
- 559 books
- 12,408 songs
- 127 artists

**Actual in S3:**
- 913 book folders (354 extra)
- 16,640 songs (4,232 extra)
- 132 artists

## Problems Identified

### 1. Path Duplication Bug (7 files) ❌ CRITICAL
Billy Joel 52nd Street test files have bucket name in the S3 key:
```
s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Big Shot.pdf
```

Should be:
```
Billy Joel/52nd Street/Billy Joel - Big Shot.pdf
```

### 2. Duplicate Book Folders (354 extra folders)
Many books have 2-3 versions in S3:
- With artist prefix: `Beatles/Beatles - Abbey Road/`
- Without artist prefix: `Beatles/Abbey Road/`
- With old naming: `Beatles/Beatles - Abbey Road [scores]/`

**Examples:**
- Beatles: 42 book folders (should be 21)
- Billy Joel: 18 book folders (should be 17)
- Bob Dylan: 16 book folders (should be 13)

### 3. Extra Songs (4,232 more than expected)
Likely due to:
- Duplicate folders containing same songs
- Multiple processing runs
- Test runs that weren't cleaned up

### 4. Inconsistent Structure
**Most files (16,497):** `Artist/Book/Songs/Song.pdf` (extra "Songs" subfolder)
**Some files (136):** `Artist/Book/Song.pdf` (correct structure)
**Broken (7):** Path duplication bug

## Options

### Option 1: Clean Slate - Reprocess Everything ⭐ RECOMMENDED

**What:**
1. Keep artifacts (they have book_id mappings)
2. Delete all song PDFs and manifests
3. Reprocess all 559 books with current pipeline
4. Get clean, consistent structure

**Pros:**
- ✅ Clean, consistent naming
- ✅ No duplicates
- ✅ Correct structure (no extra "Songs" subfolder)
- ✅ Fixes path duplication bug
- ✅ All books use new naming conventions
- ✅ Known good state

**Cons:**
- ❌ Cost: ~$170-180 for reprocessing
- ❌ Time: Several hours to complete
- ❌ Requires monitoring

**Cost Breakdown:**
- Bedrock API calls: ~$150 (559 books × $0.27/book)
- ECS task time: ~$20-30
- **Total: ~$170-180**

**Time Estimate:**
- With concurrency of 10: ~2-3 hours
- With concurrency of 20: ~1-2 hours

### Option 2: Selective Cleanup - Keep Best, Delete Duplicates

**What:**
1. For each book, identify all S3 folders
2. Keep the folder with most songs (likely most complete)
3. Delete duplicate folders
4. Manually fix the 7 Billy Joel files
5. Accept inconsistent naming

**Pros:**
- ✅ No reprocessing cost
- ✅ Faster (can script it)
- ✅ Keeps existing good data

**Cons:**
- ❌ Complex logic to determine "best" version
- ❌ Still have inconsistent naming (some with artist prefix, some without)
- ❌ Still have extra "Songs" subfolder in most paths
- ❌ Risk of deleting wrong files
- ❌ Manual work to fix Billy Joel files

**Estimated Cleanup:**
- Delete: 245 folders, 5,366 songs
- Keep: 668 folders, 11,274 songs
- Still have duplicates and inconsistencies

### Option 3: Fix Only Critical Issues

**What:**
1. Fix the 7 Billy Joel files (path duplication bug)
2. Leave everything else as-is

**Pros:**
- ✅ Minimal work
- ✅ No cost
- ✅ Fixes the broken paths

**Cons:**
- ❌ Still have 354 duplicate folders
- ❌ Still have 4,232 extra songs
- ❌ Still have inconsistent naming
- ❌ Wasted storage (though only $0.37/month)

### Option 4: Do Nothing

**What:**
- Accept current state

**Pros:**
- ✅ No work
- ✅ No cost

**Cons:**
- ❌ Broken paths (7 files)
- ❌ Duplicates everywhere
- ❌ Inconsistent naming
- ❌ Confusing structure

## Recommendation

**Go with Option 1: Clean Slate**

**Why:**
1. **You've already proven the pipeline works** - All 559 books processed successfully
2. **Cost is reasonable** - $170-180 is acceptable for a clean, production-ready system
3. **Time is manageable** - 2-3 hours with monitoring
4. **Eliminates all issues** - No duplicates, no broken paths, consistent naming
5. **Future-proof** - Clean structure for any future processing
6. **You have backups** - Artifacts are preserved, can analyze what happened

**When NOT to do this:**
- If budget is extremely tight
- If you need results immediately (can't wait 2-3 hours)
- If you're okay with messy structure

## Implementation Plan for Option 1

### Step 1: Backup Current State
```powershell
# Download all manifests for reference
aws s3 sync s3://jsmith-output/ ./S3Backup/ --exclude "*" --include "*/manifest.json" --profile default

# Verify artifacts are safe
aws s3 ls s3://jsmith-output/artifacts/ --recursive --profile default | Measure-Object -Line
# Should show 5,852 files
```

### Step 2: Clean Output Bucket
```powershell
# Delete all song PDFs (keep artifacts)
aws s3 rm s3://jsmith-output/ --recursive --exclude "artifacts/*" --include "*.pdf" --profile default

# Delete all manifests (keep artifacts)
aws s3 rm s3://jsmith-output/ --recursive --exclude "artifacts/*" --include "manifest.json" --profile default

# Delete any other non-artifact files
aws s3 rm s3://jsmith-output/output/ --recursive --profile default
aws s3 rm s3://jsmith-output/s3:/ --recursive --profile default

# Verify only artifacts remain
aws s3 ls s3://jsmith-output/ --recursive --profile default | Measure-Object -Line
# Should show ~5,852 files (only artifacts)
```

### Step 3: Reprocess All Books
```powershell
# Use existing batch processing script
.\process-all-books.ps1

# Monitor progress
.\monitor-all-executions.ps1
```

### Step 4: Verify Results
```powershell
# Check final structure
py analyze_s3_output_structure.py

# Should show:
# - 559 book folders (no duplicates)
# - ~12,408 songs
# - Clean structure: Artist/Book/Song.pdf
# - No path duplication bugs
```

## Decision Needed

**Which option do you want to pursue?**

1. ⭐ **Option 1: Clean Slate** (reprocess all, ~$170-180, 2-3 hours)
2. **Option 2: Selective Cleanup** (keep best, delete duplicates, complex)
3. **Option 3: Fix Only Critical** (fix 7 Billy Joel files, leave rest)
4. **Option 4: Do Nothing** (accept current state)

**My recommendation:** Option 1

**Your decision:** _____________
