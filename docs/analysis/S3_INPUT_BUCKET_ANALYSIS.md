# S3 Input Bucket Analysis

**Date:** January 30, 2026  
**Bucket:** `jsmith-input`

## Current State

### S3 Bucket Contents
- **Total PDFs:** 590 files
- **Old structure (with /books/):** 569 files
- **New structure (without /books/):** 21 files
- **Storage size:** 10.67 GB (~$0.25/month)

### Source of Truth (Local)
- **Total books:** 559 files
- **Structure:** No `/books/` subfolder
- **Location:** `C:\Work\AWSMusic\SheetMusic\<Artist>\<Book>.pdf`

## The Mismatch

### DynamoDB Ledger
Points to **NEW structure** (without `/books/`):
```
s3://jsmith-input/SheetMusic/<Artist>/<Book>.pdf
```

### S3 Bucket
Contains **OLD structure** (with `/books/`):
```
s3://jsmith-input/SheetMusic/<Artist>/books/<Book>.pdf
```

### Impact
- ✓ **Current processing:** All 559 books already processed successfully
- ✓ **Output files:** All 12,408 songs in `jsmith-output` bucket
- ✗ **Reprocessing:** Would FAIL because DynamoDB points to paths that don't exist in S3

## Why This Happened

The S3 input bucket was never updated when you reorganized the local files. The processing pipeline:
1. Originally uploaded files with `/books/` subfolder
2. Processed all 559 books successfully
3. You reorganized local files (removed `/books/`)
4. We updated DynamoDB to match new local structure
5. But S3 input bucket still has old structure

## Do You Need the Input Bucket?

### Purpose of Input Bucket
The input bucket (`jsmith-input`) is ONLY used for:
- Initial ingestion of source PDFs
- Reprocessing books if needed

### Current Status
- ✓ All 559 books processed
- ✓ All outputs in `jsmith-output` bucket
- ✓ DynamoDB tracks everything
- ✓ Local files are source of truth

### Answer: NO, you don't need it anymore!

Since all books are processed and you have:
1. Local source files
2. Processed outputs in S3
3. Complete DynamoDB tracking

The input bucket is redundant.

## Recommendations

### Option A: Delete Entire Input Bucket (RECOMMENDED)
**Pros:**
- Saves $0.25/month in storage costs
- Simplifies architecture
- No confusion about which structure is current

**Cons:**
- Must re-upload from local if you want to reprocess
- Takes time to upload (~10 GB)

**When to choose:** You're confident in your processed outputs and don't plan to reprocess soon.

### Option B: Update S3 to Match New Structure
**Pros:**
- Can reprocess without re-uploading
- DynamoDB and S3 paths match

**Cons:**
- Costs $0.25/month ongoing
- Requires uploading 559 files (~10 GB)
- Duplicates what you have locally

**When to choose:** You plan to reprocess books frequently.

### Option C: Keep As-Is (NOT RECOMMENDED)
**Pros:**
- No work required

**Cons:**
- Costs $0.25/month for unused data
- Mismatch between DynamoDB and S3
- Reprocessing would fail
- Confusing for future maintenance

**When to choose:** Never. This is the worst option.

## Recommended Action

**Delete the entire input bucket:**

```powershell
# List what will be deleted (dry run)
aws s3 ls s3://jsmith-input/SheetMusic/ --recursive --profile default

# Delete everything
aws s3 rm s3://jsmith-input/SheetMusic/ --recursive --profile default

# Verify empty
aws s3 ls s3://jsmith-input/ --profile default
```

### Why This Is Safe

1. **All books processed:** 559/559 complete
2. **Outputs preserved:** 12,408 songs in `jsmith-output`
3. **Local backup:** All source PDFs in `C:\Work\AWSMusic\SheetMusic`
4. **DynamoDB tracking:** Complete ledger of all processing
5. **Can re-upload:** If needed, upload from local with new structure

### If You Need to Reprocess Later

1. Upload from local with new structure:
```powershell
aws s3 sync C:\Work\AWSMusic\SheetMusic s3://jsmith-input/SheetMusic/ --profile default
```

2. DynamoDB already points to correct paths
3. Pipeline will work immediately

## Cost Analysis

### Current Costs (keeping input bucket)
- Storage: 10.67 GB × $0.023/GB/month = **$0.25/month**
- Annual: **$3.00/year**

### After Deletion
- Storage: $0.00
- Savings: **$3.00/year**

Not a huge amount, but why pay for unused data?

## Summary

**Answer to your questions:**

1. **Does S3 input bucket match local?** NO - S3 has old structure, local has new
2. **Does it need to?** NO - input bucket is only for reprocessing
3. **Can we clean it out?** YES - safely delete everything

**Recommendation:** Delete the entire input bucket. You don't need it, and it's just costing money and causing confusion.
