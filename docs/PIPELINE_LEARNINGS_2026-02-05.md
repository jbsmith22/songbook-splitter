# V2 Pipeline Learnings and Issues
**Date**: February 5, 2026
**Analysis Complete**: Comprehensive review of all 71 V2_PROCESSED books

---

## Critical Finding: V2 SplitAndUpload Stage Failure

**ALL 71 V2_PROCESSED books have zero S3 output PDFs.**

The V2 pipeline successfully ran the analysis stages but FAILED to produce output:
- S3 `verified_songs.json`: 0 songs for all books
- S3 `output/` folder: Only manifest.json, no PDFs

**Local Files Source**: The local song PDFs in `ProcessedSongs_Final/` came from multiple sources:
1. **V1 Pipeline**: Some files came from `ProcessedSongs/` folder (dated Jan 26, 2026)
2. **Unknown Process**: Additional files were created on Feb 4, 2026 23:53
   - These files have suspicious characteristics (17 files with identical size 483781 bytes)
   - They claim to be different songs but all on pages [39,39]
   - May indicate a bug in PDF extraction

The "V2_PROCESSED" status is misleading - books have V2 analysis artifacts but V1/unknown output files.

### ProcessedSongs vs ProcessedSongs_Final Comparison

Example: Beatles - Anthology 2 page_01_-_40
- V1 (ProcessedSongs): 9 files, dated Jan 26
- Final (ProcessedSongs_Final): 26 files, mixed dates
- Common files: 5 (with slightly different filenames - apostrophe handling)
- Only in Final: 21 files (source unclear, possible duplicate extractions)

---

## Page Analysis Error Rates

### Summary Statistics
| Category | Count |
|----------|-------|
| Total books analyzed | 71 |
| Books with >50% error rate | 27 (38%) |
| Books with 0% error rate | 10 (14%) |
| Median error rate | ~45% |

### High Error Rate Books (>50%)

| Book | Error Rate | Detected Songs | Actual Songs |
|------|------------|----------------|--------------|
| Beatles - Anthology 2 page_73_-112 | 79.5% | 1 | 1 |
| Beatles - Anthology 3 _page 37 - 79 | 76.7% | 2 | 2 |
| Beatles - Rubber Soul | 76.5% | 4 | 4 |
| Beatles - Anthology 3 page_80_-_111 | 72.7% | 4 | 4 |
| Beatles - Sgt Pepper's | 71.4% | 4 | 4 |
| Avril Lavigne - The Best Damn Thing | 69.9% | 7 | 7 |
| Beatles - White Album 1 Guitar | 69.9% | 6 | 6 |
| America - Greatest Hits | 67.8% | 12 | 13 |
| Bee Gees - Anthology | 66.2% | 12 | 11 |
| Ben Folds - Songs For The Silverman | 66.0% | 5 | 5 |
| ...and 17 more books | >50% | - | - |

### Best Performing Books (0% error rate)

1. Beatles - Abbey Road (18 songs)
2. Beatles - All Songs 1962-1974 (209 songs)
3. Beatles - Anthology (209 songs)
4. Beatles - Songbook (209 songs)
5. Billy Joel - 52nd Street (9 songs)
6. Billy Joel - Keyboard Book (15 songs)
7. Billy Joel - Rock Score (8 songs)
8. Billy Joel - Turnstiles (9 songs)
9. Elton John - Greatest Hits 1970-2002 (35 songs)
10. Queen - Greatest Hits (7 songs)

---

## TOC Parsing Failure

**ALL 71 books have `toc_songs: 0`** - meaning the TOC parsing stage NEVER successfully extracted song lists from any book.

The pipeline fell back to page analysis for all books, which:
1. Has higher error rates on poor quality scans
2. Misses songs when pages have analysis errors
3. Can produce false positives (OCR errors, lyrics as titles)

**Root Cause**: The TOC discovery and parsing stages are not working effectively. They find TOC page candidates but fail to extract structured song information.

---

## Song Detection Issues

### Mismatches Between Detected and Actual

| Book | Detected | Actual | Issue |
|------|----------|--------|-------|
| Beatles - Anthology 2 page_01_-_40 | 10 | 26 | +16 from V1? |
| Beatles - Anthology 3 page_01_-_36 | 8 | 26 | +18 from V1? |
| Beatles - Fake Songbook | 449 | 192 | Lead sheet overcounting |
| Beatles - Beatlemania | 53 | 56 | Missing 3 |
| ACDC - Anthology | 12 | 16 | Missing 4 |
| Beatles - 100 Hits | 96 | 92 | Minor mismatch |

### Known Garbage Entries (Already Fixed)
- Bee Gees - Anthology: Removed 3 garbage entries (lyrics fragments)
- Beatles Anthology splits: Removed ~10 garbage entries total

---

## V1 vs V2 Data Provenance Issue

The local files have unclear provenance:
1. Some folders contain V1 pipeline output (old-style book IDs like `beatles-anthology-1`)
2. Some folders were populated by manual copying
3. Manifests were rebuilt from existing files without proper page metadata
4. The `-2` suffix books in DynamoDB indicate reprocessing attempts

**Evidence of V1 Files**:
- File timestamps predate V2 processing
- S3 has old-style book ID folders (e.g., `beatles-anthology-2-page-01-40/`)
- Local manifests show `skipped_existing: N` indicating files already existed

---

## Recommendations for V2.1 Pipeline

### 1. Fix SplitAndUpload Stage
The stage is failing silently. Need to:
- Add proper error handling and logging
- Verify PDF extraction before marking complete
- Upload output PDFs to S3 before recording completion

### 2. Improve TOC Parsing
Current TOC parsing has 0% success rate:
- Review Claude prompts for TOC extraction
- Add fallback patterns for common TOC formats
- Consider OCR preprocessing for scanned TOCs

### 3. Reduce Page Analysis Errors
Error rate correlates with:
- Scan quality (older scans have higher errors)
- Page complexity (guitar tabs, handwritten annotations)
- Image resolution

Mitigations:
- Pre-process images (denoise, enhance contrast)
- Use Claude's "low" detail mode for initial screening
- Add retry logic for failed pages

### 4. Better Song Title Extraction
Page analysis is extracting lyrics as song titles:
- Validate titles against known patterns
- Filter short/fragmentary titles
- Cross-reference with TOC when available

### 5. Data Provenance Tracking
Add metadata to track:
- Pipeline version that created each file
- Source artifacts used for extraction
- Processing timestamp at file level

---

## Files Generated by This Analysis

| File | Purpose |
|------|---------|
| `data/analysis/page_analysis_review_all_books.json` | Error rates for all 71 books |
| `data/analysis/pipeline_completion_check.json` | S3 vs local comparison |
| `docs/PIPELINE_LEARNINGS_2026-02-05.md` | This document |

---

## Next Steps

1. **Debug SplitAndUpload**: Investigate why V2 isn't producing output files
2. **Reprocess with V2.1**: Once fixed, reprocess all 71 books
3. **TOC Enhancement**: Improve TOC parsing to reduce dependence on page analysis
4. **Quality Audit**: Review local files for books with high error rates
5. **Reconciliation**: Properly map V1 outputs to V2 metadata

---

*Analysis performed by Claude Code on February 5, 2026*
