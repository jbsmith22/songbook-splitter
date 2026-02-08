# Songbook Splitter - Complete Reconciliation Project

**Last Updated**: 2026-02-03
**Status**: In Progress - Building Complete Provenance Map
**Total Songbooks**: 559 source PDFs

---

## Project Goal

Create a complete, authoritative mapping of all 559 songbooks from source PDF → local folders → S3 storage, including:
- Full lineage and provenance tracking
- Metadata verification and validation
- Cached image availability
- TOC entries vs actual files comparison
- Page count verification
- Complete audit trail

**Key Principle**: Local files are the source of truth. S3 has old runs and duplicates - we match to local filesystem as authoritative.

---

## Directory Structure

### Source PDFs
```
d:\Work\songbook-splitter\SheetMusic\
  ├── {Artist}\
  │   └── {Artist} - {Songbook} [format].pdf
  └── Various Artists\
      └── Various Artists - {Songbook}.pdf
```
- **Total**: 559 source PDF files
- **Format**: Artist folders containing songbook PDFs

### Processed Songs (Local Output)
```
d:\Work\songbook-splitter\ProcessedSongs\          # Active processing
d:\Work\songbook-splitter\ProcessedSongs_Archive\   # Completed/archived books
  ├── {Artist}\
  │   └── {Artist} - {Songbook}\
  │       ├── manifest.json
  │       └── {Artist} - {Song Title}.pdf
  ├── _broadway Shows\
  │   └── Various Artists - {Show}\
  └── _movie And Tv\
      └── Various Artists - {Title}\
```

**Naming Convention** (CRITICAL):
- Regular artists: `{Artist}\{Artist} - {Songbook}\`
- Various Artists: `Various Artists\Various Artists - {Songbook}\`
- Broadway: `_broadway Shows\Various Artists - {Show}\`
- Movie/TV: `_movie And Tv\Various Artists - {Title}\`

### S3 Storage
```
s3://jsmith-output/
  ├── {Artist}/
  │   └── {Artist} - {Songbook}/
  │       └── {Artist} - {Song Title}.pdf
  ├── archive/completed/
  │   └── {Artist}/
  │       └── {Artist} - {Songbook}/
  ├── artifacts/{book_id}/
  │   ├── toc_discovery.json
  │   ├── toc_parse.json
  │   ├── page_mapping.json
  │   ├── verified_songs.json
  │   └── output_files.json
  └── output/{book_id}/
      └── manifest.json
```

### Image Cache (Verification)
```
S:\SlowImageCache\pdf_verification\
  └── {Artist}\
      └── {Book}\
          └── {Song}_page_{N}.jpg
```
- **Note**: Only exists for subset of books flagged for verification
- **Not all books cached**: Only ~30 artists have cached images

---

## Key Data Files

### 1. Complete Page Lineage (PRIMARY SOURCE)
**File**: `data/analysis/complete_page_lineage.json`
**Generated**: 2026-01-29
**Contains**:
```json
{
  "generated_at": "2026-01-29T14:46:30",
  "summary": {
    "total_books": 253,
    "books_with_toc": 132,
    "books_without_toc": 121,
    "total_songs": 4401
  },
  "books": [
    {
      "artist": "Carole King",
      "book_name": "Carole King - Tapestry",
      "book_dir": "c:\\Work\\AWSMusic\\ProcessedSongs\\...",
      "has_toc": true,
      "toc_entries": [
        {"title": "song name", "toc_page": 9}
      ],
      "extracted_songs": [
        {"title": "song name", "page_start": 7, "page_end": 12, "page_count": 6}
      ],
      "local_songs": [
        {"filename": "Artist - Song.pdf", "page_count": 6}
      ],
      "gaps": [],
      "mismatches": [
        {"song": "song name", "expected_pages": 6, "actual_pages": 5}
      ],
      "status": "complete"
    }
  ]
}
```

**Purpose**: Original processing data with TOC entries, page ranges, extraction details, and verification results.

### 2. TOC Cache
**Location**: `d:\Work\songbook-splitter\toc_cache\{book_id}.json`
**Format**:
```json
{
  "book_id": "9518734e91bae95e",
  "toc": {
    "entries": [
      {"song_title": "...", "page_number": 9, "confidence": 0.9}
    ],
    "extraction_method": "bedrock_vision"
  },
  "output": {
    "output_files": [
      {
        "song_title": "...",
        "output_uri": "s3://...",
        "file_size_bytes": 3936747,
        "page_range": [7, 13]
      }
    ]
  }
}
```

**Purpose**: TOC extraction results from AWS Bedrock vision API. Contains song list with page numbers and output file details.

### 3. DynamoDB Processing Ledger
**Table**: `jsmith-processing-ledger`
**Key Fields**:
- `book_id` (primary key)
- `source_pdf_uri`: S3 URI of original source PDF
- `local_output_path`: Relative path in ProcessedSongs
- `s3_output_path`: S3 path for output files
- `processing_status`: Status of processing job
- `created_date`: Processing timestamp

**Purpose**: Authoritative record of which source PDF created which output folder.

### 4. Provenance Mapping CSV
**File**: `data/analysis/provenance_complete_mapping.csv`
**Columns**: `source_pdf`, `local_folder`, `s3_folder`, `book_id`, `status`
**Status Values**:
- `VERIFIED`: Matched via DynamoDB provenance (524 books)
- `MATCHED_MANUAL`: Matched by exact name but no DynamoDB record (14 books)
- `FOUND_LOCAL`: Found in filesystem but no source PDF or DynamoDB (15 books)
- `NO_MAPPING`: Source PDF exists but no output folders found (6 books)

**Current Stats**:
- 559 total source PDFs
- 553 mapped (98.9%)
- 6 unmapped

---

## Interactive Viewers

### 1. Complete Lineage Viewer
**File**: `web/viewers/complete_lineage_viewer.html` (4.2MB with embedded data)
**Features**:
- Browse all books by artist
- View TOC entries with page numbers
- See extracted songs with page ranges
- Identify gaps and mismatches
- Filter and search capabilities
- Badges for split songs, gaps, TOC presence

**Data Source**: Embeds `complete_page_lineage.json`

### 2. Verification Review Pages
**Location**: `web/verification/verification_results/*.html`
**Features**:
- Display page-by-page JPG images from S3 cache
- Visual verification of extraction quality
- References images from `S:\SlowImageCache\pdf_verification\`

**Note**: Only created for subset of books flagged during verification runs.

### 3. Match Quality Viewer
**File**: `web/match-quality-viewer-enhanced.html`
**Purpose**: Reconciliation of S3 folders vs local folders (separate from this lineage project)

---

## Case Study: Carole King - Tapestry

This book exemplifies the complete lineage we want to establish for all 559 books.

### Source
- **PDF**: `SheetMusic/Carole King/Carole King - Tapestry.pdf`
- **Exists**: ✅ Yes

### DynamoDB
- **book_id**: `9518734e91bae95e`
- **source_pdf_uri**: Points to original S3 upload
- **local_output_path**: `Carole King/Carole King - Tapestry`
- **s3_output_path**: `archive/completed/Carole King/Carole King - Tapestry`
- **Status**: `VERIFIED`

### TOC Cache
- **File**: `toc_cache/9518734e91bae95e.json`
- **Extraction**: AWS Bedrock vision API (confidence 0.9)
- **TOC Entries**: 12 songs listed
- **First TOC page**: Page 9

### Expected Songs (from TOC)
12 songs total:
1. i feel the earth move (page 9)
2. so far away (page 15)
3. it's too late (page 20)
4. home again (page 24)
5. beautiful (page 29)
6. way over yonder (page 36)
7. you've got a friend (page 45)
8. where you lead (page 53)
9. will you love me tomorrow? (page 59)
10. smackwater jack (page 60)
11. tapestry (page 65)
12. (you make me feel like) a natural woman (page 73)

### Extracted Songs (from processing)
9 songs in extraction list (3 missing: beautiful, it's too late, you've got a friend)

### Actual Files Present
**Local**: `ProcessedSongs_Archive/Carole King/Carole King - Tapestry/`
- 12 PDF files ✅ (all TOC songs present)
- manifest.json ✅

**S3**: `s3://jsmith-output/archive/completed/Carole King/Carole King - Tapestry/`
- 12 PDF files ✅ (identical to local)

### Artifacts
**S3 Location**: `s3://jsmith-output/artifacts/9518734e91bae95e/`
- toc_discovery.json: ❌ Reconstructed (no original)
- toc_parse.json: ❌ Reconstructed (no original)
- page_mapping.json: ❌ Reconstructed (no original)
- verified_songs.json: ❌ Reconstructed (no original)
- output_files.json: ❌ Reconstructed (no original)

### Manifest
**S3 Location**: `s3://jsmith-output/output/9518734e91bae95e/manifest.json`
- Contains: book_name, source_pdf, songs list, paths
- Songs: 12 entries with page ranges and output paths

### Page Mismatches
6 songs have page count discrepancies between expected (from extraction) and actual (from files):
- so far away: expected 6 pages, actual 5 pages
- home again: expected 15 pages, actual 5 pages
- way over yonder: expected 12 pages, actual 7 pages
- where you lead: expected 5 pages, actual 4 pages
- tapestry: expected 8 pages, actual 7 pages
- (you make me feel like) a natural woman: expected 6 pages, actual 7 pages

### Cached Images
- TOC images: ❌ Not cached separately
- Page images: ❌ Not in S:\SlowImageCache\pdf_verification\
- Original PDF: ✅ Contains all TOC pages (viewable by opening source PDF)

### Comparison Result
✅ **COMPLETE**: All 12 expected songs are present as files
✅ **SYNCED**: Local and S3 are identical
⚠️ **MISMATCHES**: 6 songs have page count discrepancies
❌ **NO CACHED IMAGES**: No verification images generated

---

## Reconciliation Status by Category

### VERIFIED (524 books - 93.7%)
- Have DynamoDB records
- Source PDF → local folder → S3 folder lineage established
- **Source of truth**: DynamoDB `source_pdf_uri` field

### MATCHED_MANUAL (14 books - 2.5%)
- No DynamoDB record
- Matched by exact filename normalization
- Local folders exist in ProcessedSongs
- S3 marked as `LOCAL_ONLY`

### FOUND_LOCAL (15 books - 2.7%)
- Found by filesystem scan
- No DynamoDB record
- No source PDF match
- Includes 5 Beatles Anthology page splits
- Status: **Incomplete processing** (no manifests, not in S3)

### NO_MAPPING (6 books - 1.1%)
- Source PDF exists
- No local folder found
- No DynamoDB record
- Books: Elvis Presley, Eric Clapton, Mamas & Papas, Tom Waits, 2 Broadway shows

---

## Known Issues and Constraints

### 1. Multiple Songs Not in Extraction List
**Issue**: Some TOC songs are missing from `extracted_songs` but ARE present as files
**Example**: Carole King - 3 songs (beautiful, it's too late, you've got a friend)
**Cause**: Likely manually added or supplementary processing run
**Impact**: Metadata incomplete but files complete

### 2. Page Count Mismatches
**Issue**: Expected page count (from extraction) ≠ Actual page count (from files)
**Frequency**: 185 books have mismatches
**Cause**: Cover pages, blank pages, formatting differences
**Impact**: Need verification to determine if songs are complete

### 3. Reconstructed Artifacts
**Issue**: Many artifacts have note "Reconstructed from actual files"
**Cause**: Original processing artifacts lost or moved
**Impact**: Missing original timestamps, intermediate processing data

### 4. S3 Has Duplicates and Old Runs
**Issue**: S3 contains multiple versions of some books
**Constraint**: Use local filesystem as authoritative source
**Approach**: Match S3 to local, ignore unmatched S3 folders

### 5. No Cached Images for Most Books
**Issue**: Only ~30 artists have images in `S:\SlowImageCache\`
**Cause**: Verification images only generated for flagged books
**Impact**: Cannot do visual verification for most books

### 6. Beatles Anthology Splits
**Issue**: 5 Beatles Anthology folders in FOUND_LOCAL
**Status**: Incomplete - no manifests, not in S3, no DynamoDB records
**Files**: temp_anthology_pages/ contains PNG page images
**Action Needed**: Complete processing or remove

---

## Verification Checklist (Per Book)

For each of the 559 songbooks, establish:

### ✅ Source Provenance
- [ ] Source PDF exists in SheetMusic/
- [ ] Source PDF path recorded
- [ ] Source PDF filesize recorded

### ✅ DynamoDB Record
- [ ] book_id identified
- [ ] source_pdf_uri matches source PDF
- [ ] processing_status confirmed
- [ ] local_output_path verified
- [ ] s3_output_path verified

### ✅ Local Files
- [ ] Local folder exists (ProcessedSongs or ProcessedSongs_Archive)
- [ ] Folder follows naming convention
- [ ] manifest.json exists
- [ ] manifest.json contains book_id
- [ ] List of all song PDF files
- [ ] Song file sizes recorded
- [ ] Song page counts extracted

### ✅ S3 Files
- [ ] S3 folder identified
- [ ] List of all song PDF files in S3
- [ ] S3 files match local files (by name and size)
- [ ] Manifest exists at output/{book_id}/manifest.json
- [ ] Artifacts exist at artifacts/{book_id}/

### ✅ TOC Data
- [ ] has_toc flag from complete_page_lineage.json
- [ ] TOC entries list (expected songs with page numbers)
- [ ] TOC cache file exists (toc_cache/{book_id}.json)
- [ ] TOC extraction method recorded

### ✅ Extraction Data
- [ ] extracted_songs list from complete_page_lineage.json
- [ ] Page ranges for each extracted song
- [ ] Expected page counts

### ✅ File Comparison
- [ ] local_songs list with actual page counts
- [ ] Compare TOC entries vs extracted_songs (identify missing)
- [ ] Compare TOC entries vs local_songs (identify missing files)
- [ ] Compare expected page counts vs actual page counts
- [ ] Identify gaps in page coverage
- [ ] Flag mismatches for review

### ✅ Cached Images
- [ ] Check for cached images in S:\SlowImageCache\pdf_verification\
- [ ] Record image availability status
- [ ] Note if verification images needed

### ✅ Status Classification
- [ ] Assign overall status: COMPLETE | INCOMPLETE | MISSING | NEEDS_REVIEW
- [ ] Document any issues or anomalies
- [ ] Flag for manual review if needed

---

## File Rename Mapping Logic

**CRITICAL CONSTRAINT**: Maintain 1:1 relationship between:
- One source PDF → One local folder
- One local folder → One source PDF
- One local folder → One S3 folder (best match)

### Matching Algorithm Priority

1. **DynamoDB Provenance (Highest Priority)**
   - Match via book_id
   - Use source_pdf_uri → local_output_path → s3_output_path
   - STATUS: `VERIFIED`

2. **Exact Filename Match**
   - Normalize both filenames: `re.sub(r'[^a-z0-9]', '', text.lower())`
   - Match source PDF filename to local folder name
   - STATUS: `MATCHED_MANUAL`

3. **Filesystem Discovery**
   - Scan ProcessedSongs and ProcessedSongs_Archive
   - Find folders not matched above
   - STATUS: `FOUND_LOCAL`

4. **Unmatched Sources**
   - Source PDFs with no local folder
   - STATUS: `NO_MAPPING`

### Rename Detection

When detecting renames:
- Compare normalized filenames
- Check file sizes for song PDFs
- Verify page counts match
- Confirm artist context
- **Never map multiple sources to same folder**
- **Never map one source to multiple folders**

---

## Scripts and Tools

### Analysis Scripts
**Location**: `scripts/analysis/`

- `verify_provenance_mappings.py`: Build provenance map from DynamoDB
- `match_local_only_folders.py`: Match LOCAL_ONLY folders by exact name
- `find_unmapped_local_folders.py`: Filesystem scan for unmatched folders
- `compare_expected_vs_actual.py`: Compare TOC entries vs actual files
- `trace_songbook_lineage.py`: Complete lineage trace for single book
- `detailed_songbook_analysis.py`: Deep dive into artifacts and metadata

### Naming Fix Scripts
- `comprehensive_naming_audit.py`: Audit all folders for naming compliance
- `fix_all_naming_issues.py`: Rename folders to match convention
- `execute_category_folder_renames.py`: Fix Broadway/Movie category folders
- `update_dynamodb_and_manifests.py`: Update records after renames

### Web Viewers
- `web/viewers/complete_lineage_viewer.html`: Interactive lineage browser
- `web/verification/verification_results/*.html`: Visual verification pages

---

## Next Steps: Complete Reconciliation

### Phase 1: Data Collection (Week 1)
1. Extract complete lineage for all 559 books from `complete_page_lineage.json`
2. Query DynamoDB for all book_id records
3. Scan local filesystem for all folders (ProcessedSongs + ProcessedSongs_Archive)
4. Query S3 for all folders (use paginator for complete list)
5. Load all TOC cache files
6. Load all manifests (local and S3)

### Phase 2: Mapping and Matching (Week 1-2)
1. Build master mapping table with all data sources
2. Apply matching algorithm (DynamoDB → Exact → Discovery)
3. Identify rename candidates (careful 1:1 verification)
4. Flag duplicates and conflicts
5. Generate comprehensive status report

### Phase 3: Verification (Week 2-3)
1. For each book, run verification checklist
2. Compare TOC entries vs actual files
3. Verify page counts
4. Check for gaps and mismatches
5. Confirm local/S3 sync status
6. Document cached image availability

### Phase 4: Issue Resolution (Week 3-4)
1. Address NO_MAPPING books (6 remaining)
2. Complete FOUND_LOCAL books (15 incomplete)
3. Resolve page count mismatches (185 books)
4. Fix missing extraction entries
5. Update reconstructed artifacts where possible

### Phase 5: Final Audit (Week 4)
1. Generate complete provenance database
2. Create summary statistics dashboard
3. Document all anomalies and resolutions
4. Archive results for future reference
5. Update all viewers with final data

---

## Output Deliverables

### 1. Master Provenance Database
**Format**: SQLite or JSON
**Schema**:
```json
{
  "book_id": "...",
  "source_pdf": {
    "path": "...",
    "exists": true,
    "size_bytes": 0
  },
  "dynamodb": {
    "source_pdf_uri": "...",
    "processing_status": "...",
    "created_date": "..."
  },
  "local": {
    "folder_path": "...",
    "exists": true,
    "manifest_present": true,
    "song_count": 0,
    "songs": [...]
  },
  "s3": {
    "folder_path": "...",
    "exists": true,
    "manifest_present": true,
    "artifacts_present": true,
    "song_count": 0,
    "songs": [...]
  },
  "toc": {
    "has_toc": true,
    "entry_count": 0,
    "entries": [...],
    "cache_file_present": true
  },
  "verification": {
    "status": "COMPLETE|INCOMPLETE|MISSING|NEEDS_REVIEW",
    "all_expected_files_present": true,
    "local_s3_synced": true,
    "page_count_matches": false,
    "gaps_present": false,
    "cached_images_available": false,
    "issues": [...]
  }
}
```

### 2. Summary Statistics Report
- Total books processed: 559
- Complete books: X
- Incomplete books: X
- Books with all expected files: X
- Books with page mismatches: X
- Books with cached images: X
- Books needing review: X

### 3. Issue Register
- Document for each book with issues
- Categorized by issue type
- Priority ranking
- Resolution notes

### 4. Updated Interactive Viewer
- Enhanced lineage viewer with verification status
- Filterable by status, issues, image availability
- Drilldown to individual book details
- Export capabilities

---

## Important Notes

### Authority Hierarchy
1. **Local filesystem** = Primary source of truth
2. **DynamoDB** = Authoritative for provenance/lineage
3. **complete_page_lineage.json** = Authoritative for TOC/extraction data
4. **S3** = Backup/archive (may have duplicates and old runs)

### Data Consistency Rules
- If local and S3 differ, trust local
- If DynamoDB and filesystem differ, investigate but lean toward DynamoDB for provenance
- If metadata and actual files differ, investigate (both might be wrong)
- Never assume - always verify

### Naming Convention Enforcement
- All folders MUST follow the established naming pattern
- Renames must update: local folder, S3 folder, DynamoDB, manifest
- Document all renames in audit trail

---

## Contact and References

**Project Directory**: `d:\Work\songbook-splitter\`
**S3 Bucket**: `s3://jsmith-output/`
**DynamoDB Table**: `jsmith-processing-ledger`
**Image Cache**: `S:\SlowImageCache\pdf_verification\`

**Key Scripts**: `scripts/analysis/`
**Key Data Files**: `data/analysis/`
**Web Viewers**: `web/viewers/`

**Last Reconciliation**: 2026-02-02 (archived 292 PERFECT folders)
**Current Status**: 248 folders remaining for reconciliation

---

## Change Log

- **2026-02-03**: Created comprehensive reconciliation overview
- **2026-02-02**: Archived 292 PERFECT folders to ProcessedSongs_Archive
- **2026-01-31**: Fixed 53 folder naming issues (39 artist + 14 category)
- **2026-01-29**: Generated complete_page_lineage.json with 253 books
- **2026-01-28**: Created verification review pages with cached images
