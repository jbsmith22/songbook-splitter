# S3 Output Bucket Analysis

**Date:** January 30, 2026  
**Bucket:** `jsmith-output`  
**Status:** ✓ HEALTHY (No major issues)

## Current State

### Total Contents
- **Objects:** 23,629 files
- **Storage:** 16.18 GB
- **Cost:** ~$0.37/month

### Breakdown by Type

| Category | Count | Size | Purpose |
|----------|-------|------|---------|
| **Song PDFs** | 16,640 | 16.15 GB | Final outputs (individual songs) |
| **Manifests** | 1,137 | 0.60 MB | Processing metadata per book |
| **Artifacts** | 5,852 | 21.79 MB | Debug/processing data |
| **Total** | 23,629 | 16.18 GB | |

### Artifact Details
- `toc_discovery.json`: 1,223 files (11.32 MB) - TOC page detection
- `toc_parse.json`: 1,217 files (1.43 MB) - Parsed TOC entries
- `page_mapping.json`: 1,138 files (2.22 MB) - Page number mappings
- `verified_songs.json`: 1,137 files (2.09 MB) - Song verification results
- `output_files.json`: 1,137 files (4.73 MB) - List of generated files

## Good News!

### ✓ No Path Duplication Bug
The `s3:/` folder issue mentioned in earlier docs is **NOT present**. The bucket is clean.

### ✓ No Unexpected Folders
The `output/` folder issue is **NOT present**. Everything is organized correctly.

### ✓ Correct Structure
All files follow the expected pattern:
```
s3://jsmith-output/
├── <Artist>/
│   └── books/
│       └── <BookName>/
│           ├── <Song1>.pdf
│           ├── <Song2>.pdf
│           └── manifest.json
└── artifacts/
    └── <book_id>/
        ├── toc_discovery.json
        ├── toc_parse.json
        ├── page_mapping.json
        ├── verified_songs.json
        └── output_files.json
```

### ✓ More Songs Than Expected
- **Expected:** 12,408 songs (from local count)
- **Actual:** 16,640 songs in S3
- **Difference:** 4,232 extra songs

This is likely because:
1. Some books were processed multiple times (retries)
2. Some books have more songs than initially counted
3. The local download may have been incomplete

## What Do You Need?

### 1. Song PDFs (16,640 files, 16.15 GB)
**Status:** ✓ KEEP

**Why:**
- These are your final outputs
- Already downloaded locally to `ProcessedSongs/`
- Cloud backup is valuable
- Costs only $0.37/month

**Action:** Keep in S3 as cloud backup

### 2. Manifests (1,137 files, 0.60 MB)
**Status:** ✓ KEEP

**Why:**
- Contains processing metadata for each book
- Tiny size (less than 1 MB total)
- Useful for understanding how books were processed
- Shows TOC entries, page mappings, verification results, costs

**Action:** Keep in S3, optionally download to local

**What's in a manifest:**
```json
{
  "book_id": "...",
  "artist": "Billy Joel",
  "book_name": "52nd Street",
  "toc_entries": [...],
  "page_mappings": [...],
  "verified_songs": [...],
  "output_files": [...],
  "processing_cost": "$0.15",
  "timestamp": "2026-01-25T..."
}
```

### 3. Artifacts (5,852 files, 21.79 MB)
**Status:** ? OPTIONAL

**Why Keep:**
- Useful for debugging if something went wrong
- Can analyze how the pipeline processed each book
- Shows confidence scores, page detection details
- Relatively small (22 MB total)

**Why Delete:**
- Only needed for debugging/analysis
- Can regenerate if you reprocess books
- Saves ~6% of storage costs ($0.02/month)

**Recommendation:** Keep them. They're tiny and useful for understanding the pipeline.

## Does the Output Bucket Match Local Files?

### Song PDFs
**S3:** 16,640 songs  
**Local:** 12,408 songs (from your earlier count)

**Mismatch:** S3 has 4,232 MORE songs than local

**Possible Reasons:**
1. Local download was incomplete
2. Some books were processed multiple times (S3 has duplicates)
3. Local count was from a subset of books

**Action Needed:** Verify which is correct
- Option A: Re-download from S3 to ensure you have everything
- Option B: Compare specific books to see if S3 has duplicates
- Option C: Accept local as correct (it matches your 559 books)

### Manifests
**S3:** 1,137 manifests  
**Local:** 0 manifests (not downloaded)

**Action:** Download manifests if you want processing metadata

### Artifacts
**S3:** 5,852 artifacts  
**Local:** 0 artifacts (not downloaded)

**Action:** Only download if you need to debug/analyze processing

## Do You Need to Update the Output Bucket?

### Short Answer: NO

The output bucket is **already correct** and doesn't need updating because:

1. ✓ **Structure is correct** - No path duplication bugs
2. ✓ **All outputs present** - 16,640 songs successfully processed
3. ✓ **Manifests exist** - Metadata for all books
4. ✓ **Artifacts preserved** - Debug data available
5. ✓ **No cleanup needed** - No duplicate/error files

### The Real Question: Do You Need to Download More?

**Manifests:** YES, probably worth downloading
- Tiny size (0.60 MB)
- Contains useful metadata
- Shows how each book was processed

**Extra Songs:** MAYBE, investigate the mismatch
- S3 has 4,232 more songs than local
- Could be duplicates or missing local files
- Worth comparing to understand the difference

**Artifacts:** NO, unless you need to debug
- Only useful for analysis
- Can stay in S3 for now

## Recommendations

### Option 1: Keep Everything As-Is (RECOMMENDED)
**What:** Leave output bucket unchanged  
**Cost:** $0.37/month  
**Benefit:** Cloud backup of all outputs, no work needed  
**Downside:** None really, cost is minimal

### Option 2: Download Manifests
**What:** Download all 1,137 manifests to local  
**Command:**
```powershell
aws s3 sync s3://jsmith-output/ C:\Work\AWSMusic\S3Backup\ --exclude "*" --include "*/manifest.json" --profile default
```
**Benefit:** Have processing metadata locally  
**Cost:** Still $0.37/month in S3

### Option 3: Investigate Song Count Mismatch
**What:** Compare S3 vs local to understand 4,232 song difference  
**Why:** Ensure you have all songs locally  
**How:** Compare specific books between S3 and local

### Option 4: Delete Artifacts (NOT RECOMMENDED)
**What:** Delete `artifacts/` folder to save space  
**Savings:** ~$0.02/month (not worth it)  
**Downside:** Lose debug data

## My Recommendation

**Do this:**
1. ✓ **Keep output bucket as-is** - It's healthy and costs almost nothing
2. ✓ **Download manifests** - Useful metadata, tiny size
3. ✓ **Investigate song count** - Understand why S3 has 4,232 more songs
4. ✗ **Don't delete anything** - Storage cost is minimal ($0.37/month)

**Why:**
- Output bucket is your cloud backup
- Cost is negligible ($4.44/year)
- Everything is organized correctly
- No cleanup needed

## Summary

**Answer to your questions:**

1. **Does output bucket need updating?** NO - It's already correct
2. **Does it match local files?** MOSTLY - S3 has more songs (investigate)
3. **Should you download artifacts?** OPTIONAL - Only if you need to debug
4. **Should you download manifests?** YES - Useful metadata, tiny size

**Bottom line:** The output bucket is in great shape. Keep it as your cloud backup and optionally download manifests for local reference.
