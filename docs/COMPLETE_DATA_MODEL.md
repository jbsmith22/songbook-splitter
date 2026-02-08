# Complete Data Model for a Songbook

## Data Sources and Artifacts for Each Songbook

### 1. SOURCE - Original PDF
**Location:** `s3://jsmith-input/SheetMusic/{Artist}/{Book}.pdf`
- File path
- File size
- Page count
- Upload timestamp

### 2. DynamoDB - Processing Ledger
**Table:** `jsmith-processing-ledger`
**Key:** `book_id`

Fields:
- `book_id` - Unique identifier
- `source_pdf_uri` - S3 path to original
- `artist` - Artist name
- `book_name` - Book name
- `status` - success/failure/manual_review
- `processing_stage` - Current stage
- `songs_extracted` - Count of songs
- `started_at` - Timestamp
- `completed_at` - Timestamp
- `execution_arn` - Step Function execution ARN
- `error_message` - If failed
- `cost_estimate` - Processing cost

### 3. S3 Artifacts - Processing Results
**Location:** `s3://jsmith-output/artifacts/{book_id}/`

#### 3a. toc_discovery.json
- `pages` - Array of candidate TOC pages
- Each page:
  - `page_number`
  - `confidence_score`
  - `reasoning`
  - `image_s3_key` - Cached page image

#### 3b. toc_parse.json
- `toc_pages_used` - Which pages were parsed
- `songs` - Array of extracted songs from TOC
- Each song:
  - `title`
  - `page_number`
  - `confidence`
- `parsing_method` - How TOC was parsed

#### 3c. page_analysis.json
- `pages` - Analysis of every page
- Each page:
  - `page_number`
  - `content_type` - song_start/song_continuation/error/non_song/toc
  - `song_title` - If detected
  - `confidence`
  - `reasoning`
  - `image_s3_key` - Cached page image

#### 3d. page_mapping.json
- `songs` - Mapped page ranges
- Each song:
  - `song_title`
  - `start_page`
  - `end_page`
  - `source` - toc/page_analysis/manual
  - `confidence`

#### 3e. verified_songs.json
- `verified_songs` - Final verified list
- Each song:
  - `song_title`
  - `artist` - May differ from book artist
  - `start_page`
  - `end_page`
  - `source`
  - `verification_method`

#### 3f. output_files.json
- `output_files` - Generated PDFs
- Each file:
  - `song_title`
  - `artist`
  - `file_path` - S3 URI
  - `page_range` - Array [start, end]
  - `file_size_bytes`

### 4. S3 Output - Generated Files
**Locations:**
- `s3://jsmith-output/output/{book_id}/manifest.json`
- `s3://jsmith-output/{Artist}/{Book}/Songs/{song}.pdf`

#### 4a. manifest.json (in output folder)
- `book_id`
- `source_pdf`
- `artist`
- `book_name`
- `processing_timestamp`
- `toc_discovery` - Summary
- `page_mapping` - Summary
- `verification` - Summary
- `output` - Summary

#### 4b. Individual Song PDFs
- Multiple locations possible
- Referenced in output_files.json

### 5. Local - Downloaded Files
**Location:** `d:\Work\songbook-splitter\ProcessedSongs_Final\{Artist}\{Book}\`

#### 5a. manifest.json (local)
- `book_id`
- `artist`
- `book_name`
- `source_path`
- `pipeline_version`
- `downloaded_at`
- `songs` - Array
- Each song:
  - `title`
  - `pages` - Array
  - `file_size`
- `total_entries`
- `unique_songs`
- `downloaded_songs`
- `skipped_existing`

#### 5b. Individual Song PDFs
- `{Artist} - {Song Title}.pdf`

### 6. Provenance Tracking
**Location:** `data/analysis/v2_provenance_data.js`

Per book:
- `source_pdf` - Path info
- `mapping` - book_id, status
- `toc_info` - song_count, confidence
- `verification` - actual_songs, status
- `output_info` - song_count, local_folder
- `processing` - timestamps

### 7. Step Function Execution
**AWS Step Functions:** State machine execution

- Execution ARN
- Start time
- End time
- Input payload
- Output payload
- Execution history (all state transitions)

---

## Data Flow

```
Source PDF (S3 Input)
    ↓
DynamoDB (Record Start)
    ↓
TOC Discovery → toc_discovery.json + cached images
    ↓
TOC Parse → toc_parse.json
    ↓
Page Analysis → page_analysis.json + cached images
    ↓
Page Mapping → page_mapping.json
    ↓
Verification → verified_songs.json
    ↓
PDF Splitting → output_files.json + Song PDFs (S3)
    ↓
Manifest Generation → manifest.json (S3)
    ↓
DynamoDB (Record Success)
    ↓
Download to Local → manifest.json + Song PDFs (local)
    ↓
Provenance Tracking → v2_provenance_data.js
```

---

## Complete Data Inventory for ONE Songbook

**Minimum of 13 separate data artifacts per book:**
1. Source PDF (input)
2. DynamoDB record
3. toc_discovery.json
4. toc_parse.json
5. page_analysis.json
6. page_mapping.json
7. verified_songs.json
8. output_files.json
9. manifest.json (S3 output folder)
10. Song PDFs in S3 (N files)
11. manifest.json (local)
12. Song PDFs local (N files)
13. Provenance entry

**Plus:**
- Cached page images (in S3)
- Step Function execution record
- CloudWatch logs
