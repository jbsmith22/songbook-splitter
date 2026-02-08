# S3 Output Bucket Sync Plan - FINAL

**Date:** January 30, 2026  
**Strategy:** Match S3 to Local (Local is Source of Truth)

## Executive Summary

By comparing S3 folders to local files, we've identified exactly which S3 folders are correct and which are duplicates/old versions.

**Current State:**
- S3 has 2,050 folders (913 book folders + manifests + other)
- Local has 563 books (source of truth)
- 16,640 song PDFs in S3
- 12,408 songs locally

**Sync Plan:**
- **Keep:** 439 folders (matched to local)
- **Rename:** 408 folders (correct content, wrong name)
- **Delete:** 1,611 folders (duplicates/old versions)
- **Delete:** 7,950 files (songs in duplicate folders)

**Result After Sync:**
- Clean structure matching local
- No duplicates
- Consistent naming conventions
- ~8,690 songs remaining (correct versions)

## Matching Results

**Match Quality:**
- PERFECT (100%): 430 books
- EXCELLENT (95%+): 7 books
- GOOD (80-95%): 31 books
- PARTIAL (50-80%): 59 books
- POOR (<50%): 28 books
- NO MATCH: 8 books

**Total matched:** 555 out of 563 local books (98.6%)

## What Needs to Happen

### Phase 1: Fix Critical Issues (7 files)

**Billy Joel Path Duplication Bug:**
```
FROM: s3://jsmith-output/SheetMusicOut/Billy Joel/books/52nd Street/Billy Joel-Big Shot.pdf
TO:   Billy Joel/Billy Joel - 52nd Street/Billy Joel - Big Shot.pdf
```

These 7 files need special handling because they have the bucket name in the S3 key.

### Phase 2: Rename Folders (408 operations)

Rename S3 folders to match local naming conventions.

**Examples:**
```
FROM: Acdc/Anthology
TO:   Acdc/ACDC - Anthology

FROM: Adele/19 [pvg Book]
TO:   Adele/Adele - 19 _PVG Book_

FROM: Beatles/Abbey Road
TO:   Beatles/Beatles - Abbey Road
```

**Why:** These folders have the correct content but wrong names (missing artist prefix, wrong bracket style, etc.)

### Phase 3: Delete Duplicates (1,611 folders, 7,950 files)

Delete folders that are:
- Duplicates of kept folders
- Old processing runs
- Test runs
- No match to local

**Examples of duplicates to delete:**
```
KEEP:   Beatles/Beatles - Abbey Road (19 songs)
DELETE: Beatles/Abbey Road (17 songs)
DELETE: Beatles/Beatles - Abbey Road Guitar Recorded Version (6 songs)
DELETE: Beatles/Beatles - Abbey Road [scores] (6 songs)
```

### Phase 4: Verify Structure

After sync, verify:
- 563 book folders (one per local book)
- ~8,690 songs (no duplicates)
- All paths match local structure
- No broken paths

## Implementation Options

### Option A: Automated Script (RECOMMENDED)

Create a script that:
1. Fixes the 7 Billy Joel files
2. Renames 408 folders using S3 copy + delete
3. Deletes 1,611 duplicate folders
4. Verifies final structure

**Pros:**
- Fast (can run in parallel)
- Accurate (based on file matching)
- Repeatable (can test on subset first)
- No reprocessing cost

**Cons:**
- Need to write and test script
- S3 API costs (minimal, ~$1-2)
- Risk if script has bugs

**Time:** 1-2 hours to write/test, 30 minutes to run

### Option B: Manual Cleanup

Use the CSV files to manually:
1. Review each rename operation
2. Use AWS Console or CLI to rename
3. Delete duplicates one by one

**Pros:**
- Full control
- Can verify each operation

**Cons:**
- Very time consuming (days of work)
- Error prone
- Not practical for 408 renames + 1,611 deletes

### Option C: Clean Slate (Reprocess All)

Delete everything and reprocess all 559 books.

**Pros:**
- Guaranteed clean result
- No complex logic

**Cons:**
- Cost: ~$170-180
- Time: 2-3 hours
- Unnecessary since we have correct data

## Recommendation

**Go with Option A: Automated Script**

**Why:**
1. We have accurate matching data (98.6% match rate)
2. Much cheaper than reprocessing (~$2 vs $170)
3. Faster than manual cleanup
4. Can test on small subset first
5. Local files are the source of truth

**Implementation Plan:**

### Step 1: Create Sync Script

```python
# Script will:
# 1. Read s3_rename_plan.csv
# 2. Read s3_delete_plan.csv
# 3. For each rename: S3 copy old → new, then delete old
# 4. For each delete: S3 delete folder
# 5. Fix Billy Joel files specially
# 6. Verify final structure
```

### Step 2: Test on Subset

```powershell
# Test with 5 books first
py execute_s3_sync.py --test --limit 5
```

### Step 3: Run Full Sync

```powershell
# Run full sync
py execute_s3_sync.py --execute
```

### Step 4: Verify Results

```powershell
# Verify structure matches local
py verify_s3_sync.py
```

## Cost Estimate

**S3 API Costs:**
- Copy operations: 408 × $0.0004 per 1000 = $0.16
- Delete operations: 1,611 × $0.0004 per 1000 = $0.64
- List operations: ~10 × $0.005 per 1000 = $0.05
- **Total: ~$0.85**

**Storage Savings:**
- Delete 7,950 files (~4 GB)
- Save ~$0.10/month

## Files Generated

1. **`s3_local_matches.csv`** - Complete matching results (563 rows)
2. **`s3_rename_plan.csv`** - Rename operations (408 rows)
3. **`s3_delete_plan.csv`** - Delete operations (1,611 rows)
4. **`s3_output_structure_analysis.csv`** - Current S3 structure (913 rows)

## Next Steps

**Decision needed:** Proceed with Option A (automated script)?

If yes:
1. I'll create the sync execution script
2. We'll test on a small subset
3. Run full sync
4. Verify results

**Your decision:** _____________
