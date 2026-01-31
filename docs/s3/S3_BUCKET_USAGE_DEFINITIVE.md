# S3 Bucket Usage - Definitive Guide

**Date**: January 29, 2026  
**Source**: CloudFormation template + Pipeline code analysis

---

## Summary

The SheetMusic Book Splitter pipeline uses **3 S3 buckets**:

1. **`jsmith-input`** (625 objects) - Source PDFs
2. **`jsmith-output`** (23,629 objects) - Processed songs + artifacts
3. **`jsmith-jsmith-sheetmusic-splitter-artifacts`** (1 object) - Lambda deployment packages

---

## Bucket 1: `jsmith-input` (Input Bucket)

### Purpose
Stores source songbook PDF files that need to be processed by the pipeline.

### Expected Structure (Per Design)
```
s3://jsmith-input/
└── SheetMusic/
    └── <Artist>/
        └── books/
            └── <BookName>.pdf
```

### Actual Current Structure
```
s3://jsmith-input/
├── SheetMusic/          (expected location)
├── books/               (unexpected - should be under SheetMusic/)
└── Mamas and the Papas/ (unexpected - should be under SheetMusic/)
```

### Current Contents
- **Total Objects**: 625
- **Expected**: ~559 PDFs (one per book)
- **Discrepancy**: 66 extra objects

### What the Pipeline Does With This Bucket
1. **Ingest Service** (Lambda) scans this bucket for PDFs matching pattern: `SheetMusic/<Artist>/books/*.pdf`
2. **TOC Discovery** (ECS) downloads PDFs from here to process
3. **All ECS tasks** read source PDFs from this bucket

### IAM Permissions Required
- `s3:ListBucket` - List PDFs for discovery
- `s3:GetObject` - Download PDFs for processing

### Lifecycle Policy
- **Versioning**: Enabled
- **Old Versions**: Deleted after 30 days

---

## Bucket 2: `jsmith-output` (Output Bucket)

### Purpose
Stores ALL pipeline outputs including:
1. Individual song PDFs (final output)
2. Processing artifacts (intermediate data)
3. Manifest files (metadata)

### Expected Structure (Per Design)
```
s3://jsmith-output/
├── <Artist>/                    # Final song outputs
│   └── books/
│       └── <BookName>/
│           ├── <Artist> - <Song1>.pdf
│           ├── <Artist> - <Song2>.pdf
│           └── manifest.json
│
└── artifacts/                   # Processing artifacts
    └── <book_id>/
        ├── toc_discovery.json
        ├── toc_parse.json
        ├── page_mapping.json
        ├── verified_songs.json
        └── output_files.json
```

### Actual Current Structure
```
s3://jsmith-output/
├── Abba/                        # Artist folders (A-Z)
├── Acdc/
├── ...
├── Zz Top/
├── _broadway Shows/             # Special collections
├── _movie And Tv/
├── artifacts/                   # ✅ Processing artifacts (expected)
├── output/                      # ⚠️ Unexpected folder
└── s3:/                         # ⚠️ Path duplication bug!
```

### Current Contents
- **Total Objects**: 23,629
- **Expected**: ~12,408 song PDFs + ~559 manifests + ~2,795 artifact files = ~15,762
- **Discrepancy**: ~7,867 extra objects (likely duplicates or errors)

### What the Pipeline Writes Here

#### 1. Final Song PDFs
- **Written by**: PDF Splitter (ECS task)
- **Location**: `<Artist>/books/<BookName>/<Artist> - <SongTitle>.pdf`
- **Count**: 12,408 files (confirmed from local download)

#### 2. Manifest Files
- **Written by**: Manifest Generator (Lambda)
- **Location**: `<Artist>/books/<BookName>/manifest.json`
- **Count**: ~559 files (one per book)
- **Contents**: Metadata about processing (TOC entries, page mappings, verification results, costs)

#### 3. Processing Artifacts
- **Written by**: All ECS tasks
- **Location**: `artifacts/<book_id>/<artifact_name>.json`
- **Files per book**:
  - `toc_discovery.json` - TOC page numbers and confidence scores
  - `toc_parse.json` - Parsed TOC entries with song titles and page numbers
  - `page_mapping.json` - Mapping between printed pages and PDF indices
  - `verified_songs.json` - Song start page verification results
  - `output_files.json` - List of generated song PDFs
- **Count**: ~2,795 files (5 per book × 559 books)

### IAM Permissions Required
- `s3:PutObject` - Write song PDFs, manifests, and artifacts
- `s3:GetObject` - Read artifacts for downstream tasks
- `s3:ListBucket` - List existing outputs

### Lifecycle Policy
- **Versioning**: Enabled
- **No expiration** - outputs are kept indefinitely

### Known Issues
1. **Path Duplication Bug**: Some objects have `s3:/` prefix (bucket name duplicated in key)
2. **Unexpected `output/` folder**: Purpose unknown, not in design
3. **Extra objects**: 7,867 more objects than expected (possible duplicates or failed runs)

---

## Bucket 3: `jsmith-jsmith-sheetmusic-splitter-artifacts` (Artifacts Bucket)

### Purpose
Stores Lambda deployment packages and CloudFormation artifacts.

### Expected Structure (Per Design)
```
s3://jsmith-jsmith-sheetmusic-splitter-artifacts/
└── lambda/
    └── <function-name>.zip
```

### Actual Current Structure
```
s3://jsmith-jsmith-sheetmusic-splitter-artifacts/
└── lambda/
```

### Current Contents
- **Total Objects**: 1
- **Expected**: Lambda deployment ZIP files

### What's Stored Here
- Lambda function deployment packages (ZIP files)
- CloudFormation template artifacts
- **NOT used for processing artifacts** (those go in `jsmith-output/artifacts/`)

### IAM Permissions Required
- CloudFormation and Lambda services need read access
- ECS tasks do NOT access this bucket

### Lifecycle Policy
- **Expiration**: 90 days (old artifacts deleted automatically)

---

## Design vs. Reality: Key Discrepancies

### 1. Artifacts Location
**Design Intent**: Separate artifacts bucket for processing artifacts  
**Reality**: Processing artifacts are stored in `jsmith-output/artifacts/`  
**Impact**: Works fine, but not as designed

### 2. Bucket Naming
**Design Intent**: `jsmith-${StackName}-artifacts`  
**Reality**: `jsmith-jsmith-sheetmusic-splitter-artifacts`  
**Impact**: Stack name appears to be "jsmith-sheetmusic-splitter"

### 3. Input Structure
**Design Intent**: All PDFs under `SheetMusic/<Artist>/books/`  
**Reality**: Some PDFs in `books/` and `Mamas and the Papas/` at root level  
**Impact**: Ingest service may miss these PDFs

### 4. Output Duplicates
**Design Intent**: ~15,762 objects  
**Reality**: 23,629 objects  
**Impact**: Wasted storage, possible duplicate processing

---

## Data Flow Through Buckets

### Processing a Single Book

```
1. INPUT BUCKET (jsmith-input)
   └── SheetMusic/Billy Joel/books/Billy Joel - 52nd Street.pdf
                    ↓
2. ECS Task: TOC Discovery
   - Downloads PDF from input bucket
   - Processes first 20 pages
   - Writes: jsmith-output/artifacts/<book_id>/toc_discovery.json
                    ↓
3. ECS Task: TOC Parser
   - Reads: toc_discovery.json from output bucket
   - Parses TOC entries
   - Writes: jsmith-output/artifacts/<book_id>/toc_parse.json
                    ↓
4. ECS Task: Page Mapper
   - Reads: toc_parse.json from output bucket
   - Maps page numbers to PDF indices
   - Writes: jsmith-output/artifacts/<book_id>/page_mapping.json
                    ↓
5. ECS Task: Song Verifier
   - Reads: page_mapping.json from output bucket
   - Verifies song start pages
   - Writes: jsmith-output/artifacts/<book_id>/verified_songs.json
                    ↓
6. ECS Task: PDF Splitter
   - Reads: verified_songs.json from output bucket
   - Downloads PDF from input bucket
   - Splits into individual songs
   - Writes: jsmith-output/Billy Joel/books/52nd Street/<song>.pdf (×9)
   - Writes: jsmith-output/artifacts/<book_id>/output_files.json
                    ↓
7. Lambda: Manifest Generator
   - Reads: All artifacts from output bucket
   - Generates manifest
   - Writes: jsmith-output/Billy Joel/books/52nd Street/manifest.json
```

### Key Observations
1. **Input bucket is read-only** for the pipeline
2. **Output bucket is read-write** (artifacts are read by downstream tasks)
3. **Artifacts bucket is not used** by processing pipeline
4. **All intermediate data** stays in output bucket under `artifacts/`

---

## Storage Costs

### Current Usage
- **jsmith-input**: 625 objects ≈ 625 PDFs × ~10 MB = ~6.25 GB
- **jsmith-output**: 23,629 objects ≈ 12,408 songs × ~0.5 MB + artifacts = ~7-8 GB
- **jsmith-artifacts**: 1 object ≈ <1 MB

### Estimated Monthly Cost (S3 Standard, us-east-1)
- Storage: ~15 GB × $0.023/GB = **$0.35/month**
- Requests: Negligible for batch processing
- **Total**: <$1/month for storage

---

## Recommendations

### 1. Clean Up Output Bucket
- Investigate and remove duplicate objects (7,867 extra files)
- Remove `s3:/` folder (path duplication bug)
- Clarify purpose of `output/` folder or remove it

### 2. Fix Input Bucket Structure
- Move `books/` and `Mamas and the Papas/` under `SheetMusic/`
- Ensure all PDFs follow pattern: `SheetMusic/<Artist>/books/<BookName>.pdf`

### 3. Align Artifacts Storage
- **Option A**: Move processing artifacts to dedicated artifacts bucket (as designed)
- **Option B**: Update documentation to reflect current practice (artifacts in output bucket)

### 4. Implement Lifecycle Policies
- Add expiration for old artifacts (e.g., 90 days)
- Consider moving old outputs to S3 Glacier for archival

### 5. Monitor Storage Growth
- Set up CloudWatch metrics for bucket size
- Alert if storage exceeds expected thresholds

---

## Conclusion

The pipeline uses 3 buckets with a clear separation of concerns:
1. **Input**: Source PDFs (read-only)
2. **Output**: Final songs + processing artifacts (read-write)
3. **Artifacts**: Lambda deployment packages (infrastructure)

The current implementation deviates slightly from the design (artifacts in output bucket instead of separate bucket), but this works fine in practice. The main issues are organizational (duplicate files, incorrect folder structure) rather than functional.

---

**Document Version**: 1.0  
**Date**: January 29, 2026  
**Author**: Kiro AI Assistant  
**Status**: Definitive Analysis
