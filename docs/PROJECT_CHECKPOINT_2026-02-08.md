# Project Checkpoint: 2026-02-08

## Summary

Completed the v3 pipeline code migration. All pipeline code has been updated to use the new v3 architecture: dedicated artifacts bucket, human-readable paths with `v3/` prefix, new DynamoDB ledger schema with per-step tracking, and manifest generation removed. The library was also cleaned up (fakebooks/scores separated, input curated to 439 PDFs). No pipeline re-run yet -- this checkpoint captures the code-complete state before first v3 execution.

---

## V3 Architecture Overview

### Core Design Principle
**Local and S3 must be byte-identical mirrors.** Every file must have the same name and be byte-exact on both sides.

### Storage Layout

| Location | Local Path | S3 Path |
|---|---|---|
| **Input** (source PDFs) | `SheetMusic_Input/{Artist}/{Artist} - {Book}.pdf` | `s3://jsmith-input/v3/{Artist}/{Artist} - {Book}.pdf` |
| **Output** (song PDFs only) | `SheetMusic_Output/{Artist}/{Book}/{Artist} - {Song}.pdf` | `s3://jsmith-output/v3/{Artist}/{Book}/{Artist} - {Song}.pdf` |
| **Artifacts** (pipeline JSON) | `SheetMusic_Artifacts/{Artist}/{Book}/{artifact}.json` | `s3://jsmith-artifacts/v3/{Artist}/{Book}/{artifact}.json` |
| **DynamoDB** | N/A (AWS-only) | `jsmith-pipeline-ledger` table |

### Key V3 Decisions
- All S3 paths prefixed with `v3/` for namespace isolation from legacy v2 data
- Artifacts use human-readable `{Artist}/{Book}/` paths, not `artifacts/{book_id}/`
- `book_id` embedded inside every artifact JSON for cross-referencing
- Output bucket is clean: song PDFs only (no artifacts, no manifests)
- Dedicated artifacts bucket (`jsmith-artifacts`) replaces writing to `jsmith-output`
- Manifest generation removed entirely; artifacts bucket holds all metadata
- Per-step DynamoDB tracking enables restart from any failed step

---

## AWS Infrastructure Created

### S3 Bucket: `jsmith-artifacts`
- **Created:** 2026-02-08
- **Purpose:** Dedicated bucket for pipeline artifacts (v3)
- **Contents:** Empty (awaiting first v3 pipeline run)
- **Replaces:** Artifacts previously written to `s3://jsmith-output/artifacts/{book_id}/`

### DynamoDB Table: `jsmith-pipeline-ledger`
- **Created:** 2026-02-08
- **Status:** ACTIVE
- **Primary Key:** `book_id` (String, HASH)
- **GSI:** `status-index` on `status`
- **Billing:** PAY_PER_REQUEST
- **Contents:** Empty (awaiting first v3 pipeline run)
- **Replaces:** `jsmith-processing-ledger` (1,249 records, v2 schema)

### V2 Backup
- `SheetMusic_Artifacts_v2_backup/lambda/lambda-deployment.zip` (~80MB)
- Synced from `s3://jsmith-jsmith-sheetmusic-splitter-artifacts/`

---

## Local Folder Structure

```
D:/Work/songbook-splitter/
├── SheetMusic/                        ← Original master copies (559 PDFs, untouched)
├── SheetMusic_Input/                  ← Curated v3 input (439 PDFs, 125 artist folders)
├── SheetMusic_Output/                 ← Empty, awaiting v3 pipeline run
├── SheetMusic_Artifacts/              ← Empty, awaiting v3 pipeline run
├── SheetMusic_Artifacts_v2_backup/    ← Backup of old artifacts bucket
├── SheetMusic_FakeAndScores/          ← 55 fakebooks/scores separated from pipeline
├── SheetMusicIndividualSheets/        ← Pre-existing individual sheet music
├── ProcessedSongs_Final/              ← V2 output (keeping as reference)
└── ProcessedSongs_Archive/            ← Archived perfect folders from reconciliation
```

### Input Library Curation (439 from 559)
- Removed 55 fakebooks and scores → `SheetMusic_FakeAndScores/`
- Removed 24 unsplit fakebooks from `_Fake Books/` → same folder
- Fixed `Herman's Hermits` apostrophe in folder name
- User manually cleaned filenames (`_PVG Book_` suffixes, etc.)
- Final count: **439 PDFs** across **125 artist folders**

---

## Pipeline Code Changes (7 files)

### 1. `app/utils/sanitization.py`
- **Line 324:** Removed `/Songs/` from output path
- `{artist}/{book}/Songs/{file}` → `{artist}/{book}/{file}`
- Root cause fix for the `/Songs/` subfolder bug (previously worked around by `flatten_songs_folders.py`)

### 2. `ecs/task_entrypoints.py` (major rewrite)
- Added `S3_SCHEMA_PREFIX = "v3"` constant
- Added `get_artifact_bucket()` helper → reads `ARTIFACTS_BUCKET` env var, default `jsmith-artifacts`
- Added `get_artifact_prefix(artist, book_name)` → builds `v3/{sanitized_artist}/{sanitized_book}`
- **All 6 task functions updated:**
  - `toc_discovery_task` — artifacts → `jsmith-artifacts`, v3 paths
  - `toc_parser_task` — artifacts → `jsmith-artifacts`, v3 paths
  - `song_verifier_task` — both holistic + legacy paths updated
  - `pdf_splitter_task` — output_files.json artifact updated
  - `page_mapper_task` — both holistic + legacy paths updated
  - `page_analysis_task` — all 3 artifact writes updated, TOC read updated
- **Manifest generator task completely removed** (function + dispatcher entry)
- All artifact JSON files now embed `book_id` for cross-referencing

### 3. `app/services/page_analyzer.py` (Lambda handler)
- Lines 535-566: Artifact writes → `jsmith-artifacts` with `v3/{artist}/{book}/` prefix
- Added `ARTIST`, `BOOK_NAME`, `ARTIFACTS_BUCKET` env var reads
- Embeds `book_id` in result JSON

### 4. `lambda/app/services/page_analyzer.py` (duplicate Lambda copy)
- Same changes as #3 (this is a separate copy under `lambda/`)

### 5. `app/utils/dynamodb_ledger.py`
- Default table: `sheetmusic-processing-ledger` → `jsmith-pipeline-ledger`
- `LedgerEntry` dataclass: new v3 fields (`pipeline_version`, `current_step`, `steps`, `created_at`, `updated_at`, `source_pdf_hash`, `source_pdf_size`, `source_pdf_pages`, `total_cost_usd`, `total_duration_sec`)
- Removed: `processing_timestamp`, `step_function_execution_arn`, `manifest_uri`, `cost_usd`, `processing_duration_seconds`, `ttl`
- `record_processing_start()`: writes `pipeline_version: "v3"`, `status: "in_progress"`, `current_step: "toc_discovery"`, `created_at`/`updated_at` ISO timestamps, empty `steps: {}`
- `record_processing_complete()`: removed `manifest_uri` param, uses v3 field names (`total_duration_sec`, `total_cost_usd`)
- **New method:** `update_step(book_id, step_name, step_data, current_step)` for per-step tracking

### 6. `lambda/state_machine_helpers.py`
- Default table: `sheetmusic-processing-ledger` → `jsmith-pipeline-ledger`
- Added `from datetime import datetime` import
- `record_start_handler`: writes v3 schema (`pipeline_version`, `created_at`, `updated_at`, `steps: {}`, `current_step`)
- `record_success_handler`: uses `total_duration_sec`, `total_cost_usd` (removed `manifest_uri`, `processing_timestamp`)
- `record_failure_handler`: uses `updated_at`, accepts `current_step` parameter
- `record_manual_review_handler`: uses `updated_at`, accepts `current_step`, status → `"failed"`

### 7. `lambda/ingest_service.py`
- `INPUT_BUCKET`: `sheetmusic-input` → `jsmith-input`
- `INPUT_PREFIX`: `SheetMusic/` → `v3/`
- `DYNAMODB_TABLE`: `sheetmusic-processing-ledger` → `jsmith-pipeline-ledger`
- `discover_pdfs()`: v2 pattern `SheetMusic/<Artist>/books/*.pdf` → v3 pattern `v3/<Artist>/<Artist> - <Book>.pdf`

---

## DynamoDB V3 Schema

```json
{
  "book_id": "a1b2c3d4e5f67890",          // PK, SHA256[:16] of S3 URI
  "artist": "Beatles",
  "book_name": "Abbey Road",
  "pipeline_version": "v3",
  "status": "in_progress",                 // GSI: pending | in_progress | success | failed
  "current_step": "page_analysis",
  "source_pdf_uri": "s3://jsmith-input/v3/Beatles/Beatles - Abbey Road.pdf",
  "source_pdf_hash": "d41d8cd98f00b204...",
  "source_pdf_size": 15234567,
  "source_pdf_pages": 59,
  "songs_extracted": null,                  // Set on success
  "total_cost_usd": 0.51,
  "total_duration_sec": 370,
  "execution_arn": "arn:aws:states:...",
  "error_message": null,
  "created_at": "2026-02-10T14:00:00Z",
  "updated_at": "2026-02-10T14:06:10Z",
  "steps": {
    "toc_discovery": { "status": "success", "started_at": "...", "completed_at": "...", "duration_sec": 45 },
    "toc_parse": { "status": "success", "songs_found": 17, "extraction_method": "bedrock_vision" },
    "page_analysis": { "status": "in_progress", "pages_completed": 30, "pages_total": 59 }
  }
}
```

---

## What Still Needs Doing (Pre-Run)

### Required Before First V3 Run
1. **Upload input PDFs to S3** — `aws s3 sync SheetMusic_Input/ s3://jsmith-input/v3/` (439 PDFs)
2. **Update Step Functions definition** — Remove manifest generator step, add v3 env vars (ARTIST, BOOK_NAME, ARTIFACTS_BUCKET) to all task definitions
3. **Update ECS task definitions** — Add ARTIFACTS_BUCKET env var, update container image
4. **Update Lambda environment variables** — DYNAMODB_TABLE, INPUT_BUCKET, INPUT_PREFIX
5. **Build and deploy** — New Docker image for ECS tasks, new Lambda deployment package

### Nice to Have
- Clean up old v2 scripts that reference `artifacts/{book_id}/` paths (36 scripts in `scripts/`)
- Delete old DynamoDB table `jsmith-processing-ledger` after v3 is proven
- Delete old artifacts from `s3://jsmith-output/artifacts/` after v3 is proven
- Remove `flatten_songs_folders.py` workaround (root cause fixed)

---

## V2 Data Preserved (Not Deleted)

| Data | Location | Status |
|---|---|---|
| V2 source PDFs | `SheetMusic/` (559 PDFs) | Untouched |
| V2 artifacts | `s3://jsmith-output/artifacts/{book_id}/` | Preserved |
| V2 output songs | `s3://jsmith-output/{Artist}/{Book}/Songs/` | Preserved |
| V2 DynamoDB | `jsmith-processing-ledger` (1,249 records) | Preserved |
| V2 local output | `ProcessedSongs_Final/` | Preserved |
| V2 lambda artifacts | `SheetMusic_Artifacts_v2_backup/` | Local backup |

---

## Known V2 Data Issues (Reference)

These issues exist in the old v2 data and will not be carried forward to v3:
- DynamoDB: 1,249 records (should be ~559) — includes old v1 entries and skeleton records
- DynamoDB: 685 records show `songs_extracted: 9` (placeholder)
- DynamoDB: 34 empty shell records
- DynamoDB: 3 different book_id formats
- S3 manifests at `output/{book_id}/manifest.json` are empty shells
- `/Songs/` subfolder bug in output paths (now fixed)
