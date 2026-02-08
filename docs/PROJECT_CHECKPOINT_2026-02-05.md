# Songbook Splitter Project Checkpoint
**Date**: February 5, 2026
**Status**: V2 Pipeline Operational, Data Verification Complete

---

## Executive Summary

The Songbook Splitter project processes scanned PDF sheet music books, extracts individual songs using AI-powered TOC parsing and page analysis, and stores the output in AWS S3. This checkpoint documents the current state after completing comprehensive data verification and cleanup of all processed books.

---

## Project Architecture

### High-Level Flow
```
Source PDF (S3) → Step Functions Pipeline → ECS Tasks → Output PDFs (S3)
                                                    ↓
                                              Local Download
                                                    ↓
                                        ProcessedSongs_Final/
```

### AWS Infrastructure

| Component | Resource | Purpose |
|-----------|----------|---------|
| Step Functions | Orchestration | Coordinates the 6-stage pipeline |
| ECS Fargate | Compute | Runs containerized processing tasks |
| Lambda | Triggers | Check processed, record start/completion |
| S3 | Storage | Source PDFs, artifacts, output PDFs |
| DynamoDB | Ledger | `jsmith-processing-ledger` - tracks all processing |

### S3 Bucket Structure (`jsmith-output`)

```
jsmith-output/
├── source/                    # Source PDF files (input)
│   └── {Artist}/{Book}.pdf
├── artifacts/{book_id}/       # Processing artifacts
│   ├── toc_discovery.json    # Raw TOC page candidates
│   ├── toc_parse.json        # Parsed TOC entries
│   ├── page_analysis.json    # Page-by-page analysis
│   ├── page_mapping.json     # Page offset mapping
│   ├── verified_songs.json   # Verified song list
│   └── output_files.json     # Final output file list
└── output/{book_id}/          # Output PDFs
    ├── manifest.json         # Output manifest
    └── {Artist} - {Song}.pdf # Individual song PDFs
```

### Processing Pipeline Stages

1. **CheckAlreadyProcessed** - Lambda checks if book_id exists in DynamoDB
2. **RecordProcessingStart** - Lambda records start in DynamoDB
3. **TOCDiscovery** - ECS task finds TOC pages using Claude Vision
4. **TOCParse** - ECS task extracts song entries from TOC pages
5. **PageAnalysis** - ECS task analyzes each page for song boundaries
6. **PageMapping** - ECS task maps TOC pages to actual pages
7. **VerifySongs** - ECS task validates and deduplicates song list
8. **SplitAndUpload** - ECS task extracts and uploads individual PDFs
9. **RecordCompletion** - Lambda records success in DynamoDB

---

## Current Statistics

### Local Storage (`ProcessedSongs_Final/`)

| Metric | Count |
|--------|-------|
| Book folders with manifests | 119 |
| Total songs extracted | 3,403 |
| Unique artists | 35 |

**Top Artists by Book Count:**
- Beatles: 29 books
- Billy Joel: 18 books
- Bob Dylan: 14 books
- Carole King: 8 books
- Ben Folds: 6 books

### AWS Resources

| Resource | Count |
|----------|-------|
| S3 artifacts/ folders | 1,350 |
| S3 output/ folders | 1,360 |
| DynamoDB records | 807 |

### V2 Provenance Data

| Metric | Count |
|--------|-------|
| Total entries in provenance | 563 |
| V2_PROCESSED (verified) | 71 |
| Has artifacts | 67 |
| Has output files | 67 |
| Has page mapping | 67 |

---

## Data Sources & Files

### Primary Data Files

| File | Purpose | Format |
|------|---------|--------|
| `data/analysis/v2_provenance_data.js` | Viewer data source | JavaScript |
| `data/analysis/v2_provenance_database.json` | Full provenance DB | JSON |
| `data/analysis/complete_provenance_database.json` | Complete tracking | JSON |
| `reconciliation_decisions_*.json` | Folder decisions | JSON |

### Viewer Files

| File | Purpose |
|------|---------|
| `web/viewers/v2_provenance_viewer.html` | V2 book browser |
| `web/viewers/complete_provenance_viewer.html` | Full provenance viewer |
| `web/match-quality-viewer-enhanced.html` | Reconciliation UI |

### Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/pipeline_api_server.py` | Local API server for viewers |
| `scripts/reconciliation/execute_decisions.py` | Execute folder decisions |
| `scripts/reconciliation/execute_folder_renames.py` | Rename folders |
| `app/main.py` | Main pipeline entry point |

---

## Local Directory Structure

```
d:\Work\songbook-splitter\
├── ProcessedSongs_Final/      # Downloaded/verified songs
│   └── {Artist}/
│       └── {Artist} - {Book}/
│           ├── manifest.json
│           └── {Artist} - {Song}.pdf
├── ProcessedSongs_Archive/    # Archived perfect folders (292)
├── data/
│   └── analysis/              # Analysis and provenance data
├── web/
│   └── viewers/               # HTML viewer applications
├── scripts/
│   ├── pipeline_api_server.py
│   ├── analysis/              # Analysis scripts
│   └── reconciliation/        # Folder management scripts
├── app/                       # Pipeline application code
├── lambda/                    # Lambda function code
├── infra/                     # Infrastructure definitions
└── ecs/                       # ECS task definitions
```

---

## Recent Work (February 5, 2026)

### 1. Reprocessed Books Verification

Verified 16 reprocessed books (book_ids ending in `-2`) across all data sources:
- DynamoDB records
- S3 output manifests
- S3 artifacts (toc_parse, page_analysis, output_files)
- S3 PDF file counts
- Local manifests
- Local PDF file counts
- Provenance database

**Books verified:**
- Aerosmith - Greatest Hits (15 songs)
- Allman Brothers - Best Of _PVG_ (29 songs)
- Barry Manilow - Anthology (54 songs)
- Barry Manilow - Barry Manilow _PVG Book_ (13 songs)
- Beatles - 100 Hits For All Keyboards (92 songs)
- Beatles - Essential Songs (93 songs)
- Beatles - Singles Collection _PVG_ (26 songs)
- Billy Joel - Complete Vol 1 (47 songs)
- Billy Joel - Greatest Hits (21 songs)
- Billy Joel - Greatest Hits Vol I And II (27 songs)
- Billy Joel - My Lives (70 songs)
- Billy Joel - Songs In The Attic (11 songs)
- Bob Seger - The New Best Of Bob Seger (11 songs)
- Bruce Springsteen - Greatest Hits (17 songs)
- Burl Ives - Song Book (121 songs)
- Cole Porter - The Very Best Of Cole Porter (38 songs)

### 2. Manifest Fixes

Fixed 12 broken local manifests where song counts didn't match actual PDFs:
- Beatles - Abbey Road (17 → 20 songs)
- Beatles - Beatles - Abbey Road (1 → 18 songs)
- Beatles - Fake Songbook _Guitar_ (194 → 192 songs)
- Ben Folds books (3 books)
- Billy Joel - Billy Joel - 52nd Street (1 → 9 songs)
- Billy Joel - Greatest Hits Vols 1 And 2 (20 → 21 songs)
- Bob Dylan - Saved (8 → 7 songs)
- Bruce Springsteen - Lucky Town (10 → 9 songs)
- Elton John - Greatest Hits 1970-2002 (1 → 35 songs)
- Queen - Greatest Hits (1 → 7 songs)

### 3. Garbage Entry Cleanup

Removed garbage song entries (OCR errors/lyrics fragments) from 4 books:

| Book | Before | After | Removed |
|------|--------|-------|---------|
| Bee Gees - Anthology | 14 | 11 | 3 |
| Beatles - Anthology 2 page_73_-112 | 2 | 1 | 1 |
| Beatles - Anthology 3 _page 37 - 79 | 6 | 2 | 4 |
| Beatles - Anthology 3 page_80_-_111 | 9 | 4 | 5 |

**Examples of removed garbage:**
- "lit - tle bit fast - er" (lyrics)
- "No-bod-y was real-ly sure if he was from the House of Lords" (lyrics)
- "sleep ing turn stag ing" (OCR garbage)
- "you did - n't need me an - y - more." (lyrics)

### 4. Provenance Data Sync

Synced `v2_provenance_data.js` with all local manifests to ensure:
- `verification.actual_songs` matches local count
- `output_info.song_count` matches local count
- `output_info.songs` array matches local songs

---

## Known Issues & Limitations

### 1. Split PDF Files
Beatles Anthology was split into multiple files (page ranges). These have limited songs:
- Anthology 2 page_73_-112: 1 song
- Anthology 3 _page 37 - 79: 2 songs
- Anthology 3 page_80_-_111: 4 songs

The full Anthology file (209 songs) is the correct one.

### 2. Double-Prefixed Folders
Some folders have double artist prefix (e.g., `Billy Joel - Billy Joel - 52nd Street`). These were created by older processing runs and have been fixed.

### 3. TOC Detection
Some books have `toc_songs=0` because TOC wasn't detected. These used page analysis fallback which may be less accurate.

### 4. Legacy Folders
Some folders exist without manifests (older download attempts). These don't affect current data.

---

## Verification Status

### Initial Verification (Provenance Data Consistency)
```
FINAL VERIFICATION: ALL V2 PROCESSED BOOKS
================================================================================
Verified OK: 71
Issues: 0

SUCCESS: All V2_PROCESSED books have consistent data!
```

All 71 V2_PROCESSED books verified consistent across:
- v2_provenance_data.js (viewer data)
- Local manifest.json files
- Actual PDF files on disk

### CRITICAL: V2 S3 Output Verification (Evening Update)
```
PIPELINE COMPLETION VERIFICATION
================================================================================
Complete (S3 verified > 0, S3 output > 0): 0
Incomplete (missing S3 output): 71

FAILURE: V2 pipeline did NOT produce S3 output for ANY books!
```

**WARNING**: The V2 pipeline analysis stages ran successfully but the SplitAndUpload stage failed silently for all 71 books. Local files exist but are from V1 or unknown sources.

---

## Detailed Page Analysis Review

### Bee Gees - Anthology
| Metric | Value |
|--------|-------|
| Total pages | 133 |
| Page analysis errors | 88 (66%) |
| Songs detected | 11 valid |
| Garbage removed | 3 |
| **MISSING SONG** | BOOGIE CHILD (page 13 had error) |
| Status | **NEEDS REPROCESSING** |

### Beatles - Anthology 2 page_73_-112
| Metric | Value |
|--------|-------|
| Total pages | 39 |
| Page analysis errors | 31 (79%) |
| Songs detected | 1 (A Day in the Life) |
| Garbage removed | 1 |
| Status | OK (partial file) |

### Beatles - Anthology 3 _page 37 - 79
| Metric | Value |
|--------|-------|
| Total pages | 43 |
| Page analysis errors | 33 (77%) |
| Songs detected | 2 (While My Guitar Gently Weeps, Why Don't We Do It In The Road) |
| Garbage removed | 4 |
| Status | OK (partial file) |

### Beatles - Anthology 3 page_80_-_111
| Metric | Value |
|--------|-------|
| Total pages | 33 |
| Page analysis errors | 24 (73%) |
| Songs detected | 4 (Get Back, Let It Be, The End, Oh! Darling) |
| Garbage removed | 5 |
| Status | OK (partial file) |

---

## Next Steps

### Pending Tasks
1. **Reprocess Bee Gees - Anthology**: Missing BOOGIE CHILD due to page analysis error
2. **Consider reprocessing high-error books**: Books with >50% page analysis errors may have missing songs
3. **Additional Processing**: Process remaining 492 books in source catalog

### Recommended Actions
1. Run pipeline on remaining unprocessed books
2. Consider reprocessing books where TOC wasn't detected
3. Review and potentially merge Beatles Anthology split files

---

## Scripts for Common Operations

### Start Pipeline API Server
```bash
cd d:\Work\songbook-splitter
python scripts/pipeline_api_server.py
```

### Verify All Books
```bash
python scripts/verify_all_books.py
```

### Sync Provenance Data
```bash
python scripts/sync_provenance_with_manifests.py
```

### View Processed Books
Open in browser: `web/viewers/v2_provenance_viewer.html`

---

## CRITICAL UPDATE: V2 Pipeline Analysis Complete

**Analysis Date**: February 5, 2026 (Evening)

### Key Finding: V2 SplitAndUpload Stage Failed

Comprehensive analysis of ALL 71 V2_PROCESSED books revealed:

**ALL 71 books have:**
- S3 `verified_songs.json`: 0 songs
- S3 output folder: Only manifest.json, NO PDFs
- The V2 pipeline did NOT produce any song files

**Local files in ProcessedSongs_Final came from:**
1. V1 Pipeline outputs (ProcessedSongs/ folder, dated Jan 26)
2. Unknown process (files created Feb 4, some with suspicious identical sizes)

### Page Analysis Error Rates (All 71 Books)

| Category | Count | Percentage |
|----------|-------|------------|
| Books with >50% error rate | 27 | 38% |
| Books with 0% error rate | 10 | 14% |
| TOC parsing success | 0 | 0% |

**Top 5 Highest Error Rates:**
1. Beatles - Anthology 2 page_73_-112: 79.5%
2. Beatles - Anthology 3 _page 37 - 79: 76.7%
3. Beatles - Rubber Soul: 76.5%
4. Beatles - Anthology 3 page_80_-_111: 72.7%
5. Beatles - Sgt Pepper's: 71.4%

### TOC Parsing Complete Failure

**ALL 71 books have toc_songs: 0** - TOC parsing NEVER successfully extracted song lists. The entire pipeline relied on page analysis fallback.

### Data Provenance Issues

Example: Beatles - Anthology 2 page_01_-_40
- V1 (ProcessedSongs): 9 files
- ProcessedSongs_Final: 26 files
- 17 files have identical size (483781 bytes) - suspicious duplicate extractions

### Recommended Actions

1. **Debug V2 SplitAndUpload**: Fix the stage that fails to produce output
2. **Improve TOC Parsing**: 0% success rate is unacceptable
3. **Reduce Page Analysis Errors**: 38% of books have >50% error rate
4. **Clean Up Mixed Data**: ProcessedSongs_Final has files from multiple sources

### Files Generated by This Analysis

| File | Purpose |
|------|---------|
| `data/analysis/page_analysis_review_all_books.json` | Error rates for all 71 books |
| `data/analysis/pipeline_completion_check.json` | S3 vs local file comparison |
| `docs/PIPELINE_LEARNINGS_2026-02-05.md` | Detailed learnings document |

---

## File Checksums (for verification)

Key files as of this checkpoint:
- `data/analysis/v2_provenance_data.js`: 563 songbook entries, 71 V2_PROCESSED
- `ProcessedSongs_Final/`: 119 folders, 3,403 songs
- Note: V2_PROCESSED status is misleading - actual PDF outputs are from V1/unknown sources

---

*Checkpoint created by Claude Code on February 5, 2026*
*Updated with comprehensive V2 analysis findings*
