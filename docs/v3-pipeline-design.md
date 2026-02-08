# Pipeline v3: Complete Design & Migration Plan

## Table of Contents
- [Core Design Principle](#core-design-principle)
- [Current State (v2): Complete Data Inventory](#current-state-v2-complete-data-inventory)
- [v3 Design: Target Architecture](#v3-design-target-architecture)
- [DynamoDB Schema: `jsmith-pipeline-ledger`](#dynamodb-schema-jsmith-pipeline-ledger)
- [Pipeline Code Changes](#pipeline-code-changes)
- [Migration Steps](#migration-steps)
- [Known v2 Data Issues](#known-v2-data-issues)

---

## Core Design Principle

**Local and S3 must be byte-identical mirrors.** Every file must have the same name and be byte-exact on one side or the other. No exceptions except:
- **DynamoDB** — inherently AWS-only, no local mirror
- **ImageCache** — TBD, may be local-only

---

## Current State (v2): Complete Data Inventory

### Overview

559 source songbooks (562 in prerender, 3 failures). Data is spread across local filesystem, three S3 buckets, and one DynamoDB table. Paths, naming conventions, and data quality are inconsistent across locations.

---

### DATA LOCATION 1: Local Source PDFs (ORIGINALS)

**Path:** `D:/Work/songbook-splitter/SheetMusic/{Artist}/{Artist} - {Book Name}.pdf`

These are the **master copies** of all songbook PDFs. Everything else is derived from these files. They are uploaded to S3 for pipeline processing but originate here.

**Structure:**
```
SheetMusic/
├── Beatles/
│   ├── Beatles - 100 Hits For All Keyboards.pdf
│   ├── Beatles - Abbey Road.pdf
│   └── ...
├── Billy Joel/
│   ├── Billy Joel - 52nd Street.pdf
│   └── ...
└── ... (340+ artist folders)
```

---

### DATA LOCATION 2: S3 Input Bucket (Copies for Pipeline)

**Bucket:** `s3://jsmith-input/`
**Path:** `{Artist}/{Artist} - {Book Name}.pdf`

Copies of the local source PDFs uploaded to S3 so the Lambda/ECS pipeline can read them. Should be byte-identical to the local originals.

**Example:** `s3://jsmith-input/Beatles/Beatles - Abbey Road.pdf`

---

### DATA LOCATION 3: Local Processed Output

**Path:** `D:/Work/songbook-splitter/ProcessedSongs_Final/{Artist}/`

Each artist folder contains:
- **Source PDF copy** at artist level: `{Artist}/{Artist} - {Book Name}.pdf`
- **Book folders** with extracted songs: `{Artist}/{Book Name}/`

**Structure:**
```
ProcessedSongs_Final/
└── Beatles/
    ├── Beatles - Abbey Road.pdf              ← Copy of source PDF (artist level)
    ├── Beatles - 100 Hits For All Keyboards.pdf
    │
    ├── Abbey Road/                           ← Extracted songs folder
    │   ├── manifest.json                     ← Local manifest
    │   ├── Beatles - Come Together.pdf       ← Individual song
    │   ├── Beatles - Something.pdf
    │   └── ...
    │
    └── 100 Hits For All Keyboards/
        ├── manifest.json
        ├── Beatles - A Day In The Life.pdf
        └── ...
```

#### 3a. Local `manifest.json` (per book)

Present in most book folders. Contains extraction metadata.

| Field | Type | Meaning |
|---|---|---|
| `book_id` | String | Unique identifier (e.g., `v2-dc4c90d5e3d7da00`) |
| `artist` | String | Artist name |
| `book_name` | String | Book title |
| `source_path` | String | Relative path to source PDF |
| `pipeline_version` | String | `"v2"` |
| `downloaded_at` | String (ISO) | When manifest was created |
| `songs[]` | Array | Extracted songs |
| `songs[].title` | String | Song title |
| `songs[].pages` | Array | Page range `[start, end]` (often `[0,0]` — broken) |
| `songs[].file_size` | Number | Size of extracted PDF in bytes |
| `total_entries` | Number | Raw TOC entries |
| `unique_songs` | Number | Deduplicated song count |
| `downloaded_songs` | Number | Songs downloaded from S3 |
| `skipped_existing` | Number | Songs already present locally |
| `original_pdf_copied` | Boolean | Whether source PDF was copied |
| `total_songs` | Number | Final song count |
| `fixed_at` | String (ISO) | Timestamp if manifest was repaired |

#### 3b. Local `page_analysis.json` (per book — RARE)

**Only 4 books have this locally:** Beatles - Abbey Road, Billy Joel - 52nd Street, Elton John - Greatest Hits 1970-2002, Queen - Greatest Hits. Most books have this only in S3 artifacts.

| Field | Type | Meaning |
|---|---|---|
| `book_id` | String | Book identifier |
| `source_pdf_uri` | String | S3 URI of source |
| `total_pages` | Number | Total PDF page count |
| `toc_song_count` | Number | Songs found in table of contents |
| `detected_song_count` | Number | Songs detected by vision AI |
| `matched_song_count` | Number | Songs matched TOC ↔ vision |
| `calculated_offset` | Number | PDF-page-to-printed-page offset |
| `offset_confidence` | Number | Confidence (0.0–1.0) |
| `analysis_timestamp` | String (ISO) | When analysis ran |
| `warnings[]` | Array | Any warnings |
| `pages[]` | Array | Per-page analysis |
| `pages[].pdf_page` | Number | 1-based PDF page number |
| `pages[].printed_page` | Number/null | Printed page number |
| `pages[].content_type` | String | `"cover"`, `"toc"`, `"song_start"`, `"song_continuation"` |
| `pages[].detected_title` | String/null | Title detected by vision AI |
| `pages[].has_music_notation` | Boolean | Whether page has sheet music |
| `pages[].confidence` | Number | AI confidence score |
| `pages[].raw_response` | String | Raw JSON from Claude vision API |

#### 3c. Individual Song PDFs

Named `{Artist} - {Song Title}.pdf`, one per extracted song in the book folder.

---

### DATA LOCATION 4: Pre-rendered Page Images (Image Cache)

**Path:** `S:/SlowImageCache/pdf_verification_v2/{Artist}/{Book Name}/`

Organized by `{Artist}/{Book Name}` (NOT by book_id). Contains JPEG images of each PDF page: `page_0000.jpg`, `page_0001.jpg`, etc. Used for vision AI analysis.

**Example:** `S:/SlowImageCache/pdf_verification_v2/Beatles/Abbey Road/page_0000.jpg` (59 images for Abbey Road)

The count should match `pages_cached` + `pages_rendered` from `prerender_results.json`.

---

### DATA LOCATION 5: `prerender_results.json` (Master Book Registry)

**Path:** `D:/Work/songbook-splitter/prerender_results.json`

The source of truth for "what books exist." 562 entries.

| Field | Type | Meaning |
|---|---|---|
| `timestamp` | String (ISO) | When prerender was run |
| `total_books` | Number | 562 |
| `successes` | Number | 559 |
| `failures` | Number | 3 |
| `total_pages_rendered` | Number | Pages newly rendered |
| `total_pages_cached` | Number | Pages found in cache |
| `total_time_seconds` | Number | Cumulative rendering time |
| `books[]` | Array | Per-book entries |
| `books[].book_id` | String | Unique identifier |
| `books[].artist` | String | Artist name |
| `books[].book_name` | String | Book title |
| `books[].pages_rendered` | Number | Pages newly rendered |
| `books[].pages_cached` | Number | Pages from cache |
| `books[].time_seconds` | Number | Time for this book |
| `books[].status` | String | e.g., `"OK: 0 rendered, 209 cached"` |

---

### DATA LOCATION 6: S3 Output Songs

**Bucket:** `s3://jsmith-output/`
**Path:** `{Artist}/{Book Name}/Songs/{Artist} - {Song Title}.pdf`

Individual extracted song PDFs. Note the `/Songs/` subfolder — this is a **known bug** in `app/utils/sanitization.py:324`. The intended structure is `{Artist}/{Book Name}/{file}.pdf` without the `/Songs/` level.

**Example:** `s3://jsmith-output/Beatles/Abbey Road/Songs/Beatles - Come Together.pdf`

---

### DATA LOCATION 7: S3 Pipeline Manifest (Mostly Empty)

**Bucket:** `s3://jsmith-output/`
**Path:** `output/{book_id}/manifest.json`

Written by the Step Function at the end of processing. **Nearly all are empty shells** with null fields and zero costs.

| Field | Type | Meaning |
|---|---|---|
| `book_id` | String | Book identifier |
| `source_pdf` | String | S3 input URI |
| `artist` | String | Artist name |
| `book_name` | String | Includes artist prefix (e.g., `"Beatles - Abbey Road"`) |
| `processing_timestamp` | String (ISO) | When pipeline ran |
| `processing_duration_seconds` | Number/null | Usually `null` |
| `toc_discovery` | Object | Usually `{}` (empty) |
| `page_mapping` | Object | Usually `{}` (empty) |
| `verification` | Object | Usually `{}` (empty) |
| `output` | Object | Usually `{}` (empty) |
| `warnings[]` | Array | Usually empty |
| `errors[]` | Array | Usually empty |
| `cost_estimate.textract_pages` | Number | Usually `0` |
| `cost_estimate.bedrock_tokens` | Number | Usually `0` |
| `cost_estimate.estimated_cost_usd` | Number | Usually `0.0` |

---

### DATA LOCATION 8: S3 Pipeline Artifacts (The Real Data)

**Bucket:** `s3://jsmith-output/`
**Path:** `artifacts/{book_id}/`

Six JSON files produced by different pipeline stages. This is where the actual pipeline data lives.

#### 8a. `toc_discovery.json` — Raw Text Extraction

OCR/text extraction from every page of the source PDF.

| Field | Type | Meaning |
|---|---|---|
| `toc_pages[]` | Array[Number] | Which page indices are tables of contents |
| `extracted_text{}` | Map | Key = page index (string), value = full OCR text of that page |
| `confidence_scores{}` | Map | Key = page index, value = OCR confidence score (0–100) |

#### 8b. `toc_parse.json` — Parsed Table of Contents

Song list and page numbers extracted from the TOC.

| Field | Type | Meaning |
|---|---|---|
| `entries[]` | Array | Parsed TOC entries |
| `entries[].song_title` | String | Song title from TOC |
| `entries[].page_number` | Number | Printed page number from TOC |
| `entries[].artist` | String/null | Usually null (from TOC context) |
| `entries[].confidence` | Number | Parse confidence |
| `extraction_method` | String | `"bedrock_vision"` |
| `confidence` | Number | Overall confidence |
| `artist_overrides{}` | Map | Any manual artist overrides |

#### 8c. `page_analysis.json` — Vision AI Page Classification

Same structure as local `page_analysis.json` (see Location 3b above). Per-page classification of every page: cover, TOC, song_start, song_continuation. Includes detected titles, music notation flags, and raw AI responses.

#### 8d. `page_mapping.json` — Printed-to-PDF Page Mapping

Maps printed page numbers (from TOC) to actual PDF page indices.

| Field | Type | Meaning |
|---|---|---|
| `offset` | Number | Pages before content starts |
| `confidence` | Number | Mapping confidence (0.0–1.0) |
| `samples_verified` | Number | Songs used to verify offset |
| `song_locations[]` | Array | Per-song mapping |
| `song_locations[].song_title` | String | Title |
| `song_locations[].printed_page` | Number | Page from TOC |
| `song_locations[].pdf_index` | Number | Actual PDF page |
| `song_locations[].artist` | String | Artist |
| `mapping_method` | String | e.g., `"holistic_passthrough"` |

#### 8e. `verified_songs.json` — Confirmed Song Boundaries

Final verified page ranges for each song after cross-referencing TOC, page analysis, and mapping.

| Field | Type | Meaning |
|---|---|---|
| `verified_songs[]` | Array | Songs with confirmed boundaries |
| `verified_songs[].song_title` | String | Title |
| `verified_songs[].start_page` | Number | First PDF page |
| `verified_songs[].end_page` | Number | Last PDF page |
| `verified_songs[].artist` | String | Artist |

#### 8f. `output_files.json` — What Was Written to S3

Record of every file the pipeline wrote to the output bucket.

| Field | Type | Meaning |
|---|---|---|
| `output_files[]` | Array | Output records |
| `output_files[].song_title` | String | Title |
| `output_files[].artist` | String | Artist |
| `output_files[].output_uri` | String | Full S3 URI of extracted song PDF |
| `output_files[].file_size_bytes` | Number | Size of extracted PDF |
| `output_files[].page_range` | Array | `[start, end]` pages used |

---

### DATA LOCATION 9: DynamoDB — `jsmith-processing-ledger`

**1,249 total records** across three different `book_id` formats:

| Format | Count | Example |
|---|---|---|
| No `v2-` prefix (16-char hex) | 559 | `7b91b16294985e97` |
| `v2-` + 32-char hex | 442 | `v2-bce9e57c840541a3d03e0e0619747e62` |
| `v2-` + 16-char hex + dash + number | 125 | `v2-8f1f0f7cb41370f6-2` |

**34 records** have no fields at all besides `book_id` (empty skeleton entries).

**Table structure:**
- Primary key: `book_id` (String, HASH)
- GSI: `status-index` on `status` field
- Billing: PAY_PER_REQUEST

**Fields on records that have them:**

| Field | Type | Meaning | Data Quality |
|---|---|---|---|
| `book_id` | String | Primary key | 3 inconsistent formats |
| `artist` | String | Artist name | Present on most records |
| `book_name` | String | Includes artist prefix (e.g., `"Beatles - Abbey Road"`) | Present on most records |
| `status` | String | `"success"` | Always "success" when present |
| `songs_extracted` | Number | Song count | **685 of 1,215 show `9`** (placeholder) |
| `cost_usd` | Number | Processing cost | **Placeholder `0.5`** |
| `processing_duration_seconds` | Number | Duration | **Placeholder `300`** |
| `processing_timestamp` | Number | Unix timestamp | Present on most |
| `source_pdf_uri` | String | S3 input path | Present on most |
| `manifest_uri` | String | S3 manifest path | Points to mostly-empty manifests |
| `step_function_execution_arn` | String | AWS execution ID | Present on most |

---

### DATA LOCATION 10: S3 Artifacts Bucket (Lambda Only)

**Bucket:** `s3://jsmith-jsmith-sheetmusic-splitter-artifacts/`

Contains only `lambda/lambda-deployment.zip` (83.9 MB). **No songbook data.** Despite the name, pipeline artifacts are in `s3://jsmith-output/artifacts/`.

---

### Pipeline Data Flow (v2)

```
Local SheetMusic/ (ORIGINALS)
    │
    ├─→ Upload script ─→ s3://jsmith-input/ (copies for pipeline)
    │                         │
    │                         └─→ Step Function Pipeline:
    │                               1. toc_discovery.json   → OCR all pages, find TOC
    │                               2. toc_parse.json       → Parse TOC into song list
    │                               3. page_analysis.json   → Vision AI classifies pages
    │                               4. page_mapping.json    → Map printed → PDF pages
    │                               5. verified_songs.json  → Confirm song boundaries
    │                               6. output_files.json    → Split PDFs written to S3
    │                               (stored in s3://jsmith-output/artifacts/{book_id}/)
    │                               │
    │                               ├─→ Song PDFs → s3://jsmith-output/{Artist}/{Book}/Songs/
    │                               ├─→ Manifest  → s3://jsmith-output/output/{book_id}/manifest.json
    │                               └─→ DynamoDB  → jsmith-processing-ledger
    │
    ├─→ Pre-render ─→ S:/SlowImageCache/ (page images by Artist/BookName)
    │
    └─→ Download script ─→ ProcessedSongs_Final/ (local output + manifest)
```

---

## v3 Design: Target Architecture

### File Structure

```
D:/Work/songbook-splitter/
├── SheetMusic_Input/{Artist}/{Artist} - {Book}.pdf
├── SheetMusic_Output/{Artist}/{Book}/{Artist} - {Song}.pdf
└── SheetMusic_Artifacts/{Artist}/{Book}/
        ├── toc_discovery.json
        ├── toc_parse.json
        ├── page_analysis.json
        ├── page_mapping.json
        ├── verified_songs.json
        └── output_files.json
```

### S3 Structure

All S3 paths include a `v3/` schema version prefix to isolate from legacy data.

| Bucket | S3 Path | Contents |
|---|---|---|
| `jsmith-input` | `v3/{Artist}/{Artist} - {Book}.pdf` | Source PDF copies |
| `jsmith-output` | `v3/{Artist}/{Book}/{Artist} - {Song}.pdf` | Extracted songs only |
| `jsmith-artifacts` | `v3/{Artist}/{Book}/{artifact}.json` | Pipeline artifacts (6 per book) |

**Note:** `jsmith-artifacts` is a NEW bucket replacing `jsmith-jsmith-sheetmusic-splitter-artifacts`. The `lambda/` deployment zip also lives here (outside the `v3/` prefix).

### Local ↔ S3 Mirror Mapping

| Local | S3 | Sync Command |
|---|---|---|
| `SheetMusic_Input/` | `s3://jsmith-input/v3/` | `aws s3 sync SheetMusic_Input/ s3://jsmith-input/v3/` |
| `SheetMusic_Output/` | `s3://jsmith-output/v3/` | `aws s3 sync s3://jsmith-output/v3/ SheetMusic_Output/` |
| `SheetMusic_Artifacts/` | `s3://jsmith-artifacts/v3/` | `aws s3 sync s3://jsmith-artifacts/v3/ SheetMusic_Artifacts/` |

### What Changed From v2

| Aspect | v2 (Current) | v3 (New) |
|---|---|---|
| Input folder | `SheetMusic/` | `SheetMusic_Input/` |
| Output folder | `ProcessedSongs_Final/` | `SheetMusic_Output/` |
| Artifacts folder | None locally (4 exceptions) | `SheetMusic_Artifacts/` |
| S3 schema prefix | None | `v3/` on all buckets |
| Output S3 path | `{Artist}/{Book}/Songs/{file}` | `v3/{Artist}/{Book}/{file}` |
| Artifact S3 bucket | `jsmith-output/artifacts/{book_id}/` | `jsmith-artifacts/v3/{Artist}/{Book}/` |
| Artifacts bucket name | `jsmith-jsmith-sheetmusic-splitter-artifacts` | `jsmith-artifacts` |
| Artifact folder naming | by `book_id` (machine) | by `{Artist}/{Book}/` (human-readable) |
| S3 manifest | `jsmith-output/output/{book_id}/manifest.json` | Removed |
| Source copy location | Inside book folder (wrong) | At artist level: `{Artist}/{Artist} - {Book}.pdf` |
| DynamoDB table | `jsmith-processing-ledger` (1,249 messy records) | `jsmith-pipeline-ledger` (fresh, per-step tracking) |
| DynamoDB data quality | Placeholders (`9` songs, `$0.50`, `300s`) | Actual values |
| Restart capability | None — full re-run required | Resume from any failed step |

### Pipeline Data Flow (v3)

```
SheetMusic_Input/ (ORIGINALS)
    │
    ├─→ aws s3 sync ─→ s3://jsmith-input/v3/ (copies for pipeline)
    │                         │
    │                         └─→ Step Function Pipeline:
    │                               1. toc_discovery.json   → OCR all pages
    │                               2. toc_parse.json       → Parse TOC
    │                               3. page_analysis.json   → Vision AI (resumable)
    │                               4. page_mapping.json    → Map pages
    │                               5. verified_songs.json  → Confirm boundaries
    │                               6. output_files.json    → Split PDFs
    │                               │
    │                               ├─→ Artifacts → s3://jsmith-artifacts/v3/{Artist}/{Book}/
    │                               ├─→ Song PDFs → s3://jsmith-output/v3/{Artist}/{Book}/
    │                               └─→ DynamoDB  → jsmith-pipeline-ledger (per-step updates)
    │
    ├─→ aws s3 sync ←── s3://jsmith-output/v3/     → SheetMusic_Output/
    └─→ aws s3 sync ←── s3://jsmith-artifacts/v3/  → SheetMusic_Artifacts/
```

---

## DynamoDB Schema: `jsmith-pipeline-ledger`

### Table Configuration

- **Primary Key:** `book_id` (String, HASH)
- **GSI:** `status-index` on `status`
- **Billing:** PAY_PER_REQUEST

### Top-Level Fields

| Field | Type | Purpose |
|---|---|---|
| `book_id` | String (PK) | Single consistent format |
| `artist` | String | Artist name |
| `book_name` | String | Book title |
| `pipeline_version` | String | `"v3"` |
| `status` | String (GSI) | `"pending"`, `"in_progress"`, `"success"`, `"failed"` |
| `current_step` | String | Which step is active or failed at |
| `source_pdf_uri` | String | `s3://jsmith-input/v3/{Artist}/{Artist} - {Book}.pdf` |
| `source_pdf_hash` | String | MD5 of original PDF |
| `source_pdf_size` | Number | File size in bytes |
| `source_pdf_pages` | Number | Total page count |
| `songs_extracted` | Number | Final actual count (null until complete) |
| `total_cost_usd` | Number | Sum of all step costs |
| `total_duration_sec` | Number | Sum of all step durations |
| `created_at` | String (ISO) | Record creation time |
| `updated_at` | String (ISO) | Last modification time |
| `execution_arn` | String | Step Function execution ARN |
| `error_message` | String | Top-level error if failed |

### Per-Step Tracking (`steps` Map)

Each step in the `steps` map tracks its own progress for restart capability.

```json
{
  "steps": {
    "toc_discovery": {
      "status": "success",
      "started_at": "2026-02-10T14:00:00Z",
      "completed_at": "2026-02-10T14:00:45Z",
      "duration_sec": 45,
      "cost_usd": 0.02,
      "pages_processed": 59,
      "toc_pages_found": 1,
      "error": null
    },
    "toc_parse": {
      "status": "success",
      "started_at": "2026-02-10T14:00:45Z",
      "completed_at": "2026-02-10T14:00:48Z",
      "duration_sec": 3,
      "cost_usd": 0.01,
      "songs_found": 17,
      "extraction_method": "bedrock_vision",
      "error": null
    },
    "page_analysis": {
      "status": "success",
      "started_at": "2026-02-10T14:00:48Z",
      "completed_at": "2026-02-10T14:05:30Z",
      "duration_sec": 282,
      "cost_usd": 0.47,
      "pages_completed": 59,
      "pages_total": 59,
      "songs_detected": 18,
      "songs_matched": 17,
      "error": null
    },
    "page_mapping": {
      "status": "success",
      "started_at": "2026-02-10T14:05:30Z",
      "completed_at": "2026-02-10T14:05:32Z",
      "duration_sec": 2,
      "cost_usd": 0.00,
      "offset": 1,
      "confidence": 1.0,
      "songs_mapped": 17,
      "error": null
    },
    "verified_songs": {
      "status": "success",
      "started_at": "2026-02-10T14:05:32Z",
      "completed_at": "2026-02-10T14:05:35Z",
      "duration_sec": 3,
      "cost_usd": 0.01,
      "songs_verified": 17,
      "error": null
    },
    "output_split": {
      "status": "success",
      "started_at": "2026-02-10T14:05:35Z",
      "completed_at": "2026-02-10T14:06:10Z",
      "duration_sec": 35,
      "cost_usd": 0.00,
      "files_written": 17,
      "files_total": 17,
      "total_bytes": 4500722,
      "error": null
    }
  }
}
```

### Restart Logic

The pipeline checks `steps.{step_name}.status` before running each step:

| Step Status | Action |
|---|---|
| `"success"` | Skip — already done |
| `"failed"` | Retry from beginning of step (or resume point) |
| `"running"` | Crashed mid-step — resume from progress marker |
| `"pending"` | Run from beginning |

**Key resume points:**
- `page_analysis.pages_completed` — resume vision AI from next page (avoids re-analyzing hundreds of pages)
- `output_split.files_written` — resume splitting from next song (avoids re-splitting already-written files)

---

## Pipeline Code Changes

### Critical Fixes

| File | Line(s) | Change |
|---|---|---|
| `app/utils/sanitization.py` | 324 | Remove `/Songs/` from output path: `f"{artist}/{book}/Songs/{file}"` → `f"{artist}/{book}/{file}"` |
| `ecs/task_entrypoints.py` | 66, 195, 273, 350, 438, 517, 579, 768 | Write artifacts to `jsmith-artifacts` bucket with `v3/{Artist}/{Book}/` path instead of `jsmith-output` with `artifacts/{book_id}/` |
| `ecs/task_entrypoints.py` | 646-661 | Read artifacts from new bucket/path |
| `ecs/task_entrypoints.py` | 683 | Remove S3 manifest write |
| `ecs/task_entrypoints.py` | 692 | Remove `manifest_uri` from DynamoDB update |
| `app/services/page_analyzer.py` | 536-537 | Write to artifacts bucket; add `pages_completed` tracking for resume |
| `lambda/state_machine_helpers.py` | 159-182 | Update DynamoDB writes to new table/schema; remove `manifest_uri` |
| `app/utils/dynamodb_ledger.py` | Full rewrite | New schema with per-step tracking |

### Environment Variables

| Variable | v2 Value | v3 Value |
|---|---|---|
| `OUTPUT_BUCKET` | `jsmith-output` | `jsmith-output` (unchanged) |
| `ARTIFACTS_BUCKET` | *(new)* | `jsmith-artifacts` |
| `SCHEMA_VERSION` | *(new)* | `v3` |
| `DYNAMODB_TABLE` | `jsmith-processing-ledger` | `jsmith-pipeline-ledger` |

### Scripts Requiring Path Updates (~25 files)

All scripts that reference `artifacts/{book_id}/`, `output/{book_id}/manifest.json`, or `{Artist}/{Book}/Songs/` need updating. Most are analysis/reconciliation scripts that will be rebuilt for v3:

- `scripts/analysis/` — lineage, provenance, validation scripts
- `scripts/reconciliation/` — execute_decisions, flatten_songs, fix scripts
- `scripts/reprocessing/` — batch_reprocess, download, sync scripts
- `scripts/` — verify_and_sync, verify_all_data_stores, deep_verify, etc.

### HTML Viewers Requiring Updates (3 files)

- `web/complete_lineage_viewer.html`
- `web/comprehensive_data_report.html`
- `web/match-quality-viewer-enhanced.html`

---

## Migration Steps

Execute in this order:

### Phase 1: Backup & Prepare

1. **Backup existing artifacts bucket locally:**
   ```bash
   aws s3 sync s3://jsmith-jsmith-sheetmusic-splitter-artifacts/ SheetMusic_Artifacts_v2_backup/
   ```

2. **Create new `jsmith-artifacts` S3 bucket:**
   ```bash
   aws s3 mb s3://jsmith-artifacts --region us-east-1
   ```

3. **Copy Lambda zip to new bucket:**
   ```bash
   aws s3 cp s3://jsmith-jsmith-sheetmusic-splitter-artifacts/lambda/lambda-deployment.zip s3://jsmith-artifacts/lambda/lambda-deployment.zip
   ```

4. **Create `jsmith-pipeline-ledger` DynamoDB table:**
   ```bash
   aws dynamodb create-table \
     --table-name jsmith-pipeline-ledger \
     --attribute-definitions \
       AttributeName=book_id,AttributeType=S \
       AttributeName=status,AttributeType=S \
     --key-schema AttributeName=book_id,KeyType=HASH \
     --global-secondary-indexes \
       'IndexName=status-index,KeySchema=[{AttributeName=status,KeyType=HASH}],Projection={ProjectionType=ALL}' \
     --billing-mode PAY_PER_REQUEST \
     --region us-east-1
   ```

5. **User creates local folders and pre-loads input:**
   ```
   mkdir SheetMusic_Input SheetMusic_Output SheetMusic_Artifacts
   # Copy/move source PDFs into SheetMusic_Input/{Artist}/{Artist} - {Book}.pdf
   ```

### Phase 2: Code Changes

6. **Apply all pipeline code fixes** (sanitization.py, task_entrypoints.py, page_analyzer.py, dynamodb_ledger.py, state_machine_helpers.py)

7. **Update environment variables** in ECS task definitions / Lambda config

8. **Deploy updated Lambda/ECS**

### Phase 3: Execute

9. **Upload input PDFs to S3:**
   ```bash
   aws s3 sync SheetMusic_Input/ s3://jsmith-input/v3/
   ```

10. **Run v3 pipeline** on all 559 books

11. **Sync results to local:**
    ```bash
    aws s3 sync s3://jsmith-output/v3/ SheetMusic_Output/
    aws s3 sync s3://jsmith-artifacts/v3/ SheetMusic_Artifacts/
    ```

### Phase 4: Verify & Clean Up

12. **Verify:** Every local file matches S3 byte-for-byte

13. **Retire old resources** (when confident v3 is good):
    - Delete `jsmith-jsmith-sheetmusic-splitter-artifacts` bucket
    - Clean `jsmith-output/artifacts/` and `jsmith-output/output/` prefixes
    - Clean `jsmith-input/` root-level (non-v3) data
    - Optionally delete `jsmith-processing-ledger` table

---

## Known v2 Data Issues

These are documented for reference. All will be resolved by the v3 re-run.

| Issue | Detail |
|---|---|
| DynamoDB record count | 1,249 records instead of 559/562 — includes v1 entries and skeletons |
| DynamoDB `songs_extracted` | 685 of 1,215 records show `9` (placeholder/default value) |
| DynamoDB `cost_usd` | Placeholder `0.5` on most records |
| DynamoDB `processing_duration_seconds` | Placeholder `300` on most records |
| DynamoDB empty shells | 34 records with only `book_id`, no other fields |
| DynamoDB `book_id` formats | 3 inconsistent formats across records |
| S3 `/Songs/` subfolder | Pipeline writes to `{Artist}/{Book}/Songs/` instead of `{Artist}/{Book}/` |
| S3 manifests empty | `output/{book_id}/manifest.json` files have null fields, zero costs |
| S3 artifacts by book_id | Artifacts stored by `{book_id}/` — not human-browsable |
| Local page_analysis rare | Only 4 of 562 books have `page_analysis.json` locally |
| Local manifest page ranges | `songs[].pages` often shows `[0, 0]` instead of actual ranges |
