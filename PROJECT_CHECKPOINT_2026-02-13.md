# Project Checkpoint — 2026-02-13

## Project State: 342 books verified clean, 8,045 songs

All books processed through v3 pipeline. Boundary fixes applied to 25 books. Two books deleted (Frank Zappa Guitar Book — corrupted, Tom Lehrer Book Covers — not a real book).

---

## Core Application (`app/`)

The pipeline application. Currently used by `scripts/run_v3_single_book.py` and `scripts/run_v3_batch.py` for local orchestration. Also deployed to Lambda/ECS (but cloud infra needs updating for v3).

| File | Purpose | In Use |
|------|---------|--------|
| `app/__init__.py` | Package init | Yes |
| `app/main.py` | Application entry point | Yes (ECS) |
| `app/models.py` | Data models (BookMetadata, SongEntry, etc.) | Yes |

### `app/services/`

| File | Purpose | In Use |
|------|---------|--------|
| `bedrock_parser.py` | AWS Bedrock vision API wrapper — sends PDF page images for AI analysis | Yes |
| `holistic_page_analyzer.py` | Multi-page holistic analysis (newer approach, groups pages for context) | Modified (uncommitted) |
| `improved_page_mapper.py` | Enhanced page mapping with better offset calculation | Yes |
| `page_analyzer.py` | Per-page Bedrock vision analysis — detects song_start, toc, filler, etc. | Yes |
| `page_mapper.py` | Maps TOC entries to physical PDF pages using offset detection | Yes |
| `pdf_splitter.py` | Extracts individual song PDFs from the full book PDF | Yes |
| `quality_gates.py` | Validation checks between pipeline steps | Yes |
| `song_verifier.py` | Verifies extracted songs against TOC expectations | Yes |
| `toc_discovery.py` | Finds TOC pages in a PDF using Bedrock vision | Yes |
| `toc_parser.py` | Parses TOC content into structured song entries | Yes |
| `manifest_generator.py` | Generates output manifest JSON | Obsolete (removed from v3 pipeline) |

### `app/utils/`

| File | Purpose | In Use |
|------|---------|--------|
| `__init__.py` | Package init | Yes |
| `artist_resolution.py` | Normalizes artist names (e.g. "Various Artists" variants) | Yes |
| `cloudwatch_utils.py` | CloudWatch logging helpers | Yes (cloud only) |
| `dynamodb_ledger.py` | DynamoDB read/write for `jsmith-pipeline-ledger` (v3 schema) | Yes |
| `error_handling.py` | Exception classes and error formatting | Yes |
| `s3_utils.py` | S3 upload/download helpers | Yes |
| `sanitization.py` | Filename/path sanitization, output path generation (`v3/` prefix) | Yes |

---

## Lambda Functions (`lambda/`)

Deployed to AWS Lambda for the Step Functions pipeline. Need v3 path updates for cloud execution.

| File | Purpose | In Use |
|------|---------|--------|
| `ingest_service.py` | S3 event handler — triggers pipeline when PDF uploaded to `jsmith-input` | Needs cloud update |
| `state_machine_helpers.py` | Step Functions task dispatchers (TOC discovery, page analysis, etc.) | Needs cloud update |
| `app/` | Symlinked/copied `app/` package for Lambda deployment | Needs cloud update |

---

## ECS Task Definitions (`ecs/`)

| File | Purpose | In Use |
|------|---------|--------|
| `task_entrypoints.py` | Entry points for all 6 ECS tasks (toc_discovery through pdf_splitter) | Needs cloud update |
| `docs/` | Duplicate of `docs/` directory (analysis, issues-resolved, summaries) | Dead copy |

---

## Infrastructure (`infra/`)

| File | Purpose | In Use |
|------|---------|--------|
| `cloudformation_template.yaml` | Full CloudFormation stack (S3, DynamoDB, ECS, Step Functions, Lambda) | Reference — needs v3 update |
| `step_functions_complete.json` | Complete Step Functions state machine definition | Reference |
| `step_functions_full_test.json` | Test variant of state machine | No |
| `step_functions_simple_fixed.json` | Simplified state machine variant | No |
| `step_functions_state_machine.json` | Another state machine variant | No |
| `task-def-toc-parser.json` | ECS task definition for TOC parser | Reference |

---

## Build Artifacts (`build/`)

| File | Purpose | In Use |
|------|---------|--------|
| `lambda-deployment.zip` | Packaged Lambda deployment ZIP | Stale (pre-v3) |
| `lambda-package/` | Exploded Lambda package with all dependencies (boto3, pymupdf, numpy, etc.) | Stale (pre-v3) |

---

## V3 Pipeline Scripts (`scripts/` — active)

These are the currently-used scripts for the v3 pipeline.

| File | Purpose | In Use |
|------|---------|--------|
| `run_v3_single_book.py` | Local orchestration — runs full pipeline for one book | **Yes — primary** |
| `run_v3_batch.py` | Batch runner — processes multiple books in parallel (4 books x 6 workers) | **Yes — primary** |
| `regenerate_v3_index.py` | Generates `web/v3_book_index.html` from all artifacts | **Yes — primary** |
| `verify_all_complete.py` | Cross-checks all 342 books: artifacts, DynamoDB, metadata consistency | **Yes — primary** |
| `prerender_v3_images.py` | Pre-renders PDF pages to JPG cache at `S:/SlowImageCache/pdf_verification_v3/` | Yes |
| `verify_all_artifacts.py` | Verifies all 6 artifacts exist for every book | Yes |
| `verify_v3_comprehensive.py` | Comprehensive v3 verification with detailed reporting | Yes |
| `verify_boundaries.py` | Checks song boundary accuracy across all books | Yes |
| `verify_song_pages.py` | Verifies individual song PDF page counts | Yes |
| `boundary_review_server.py` | HTTP server for boundary review viewer | Yes |
| `generate_v3_index.py` | Older version of index generator (superseded by `regenerate_v3_index.py`) | No |
| `apply_split_exports.py` | Applies manual split corrections exported from the split editor | Yes |
| `apply_overlap_fixes.py` | Applies overlap fix decisions from verification | Yes |
| `fix_all_metadata.py` | Bulk metadata repair across all books | One-time use |
| `fix_classic_rock_splits.py` | Targeted fix for classic rock book splits | One-time use |
| `fix_elvis_splits.py` | Targeted fix for Elvis book splits | One-time use |
| `fix_four_books.py` | Targeted fix for 4 specific problem books | One-time use |
| `fix_mccartney_allthebest.py` | Targeted fix for McCartney "All The Best" | One-time use |
| `fix_overlaps_with_vision.py` | Uses Bedrock vision to resolve overlap issues | One-time use |
| `fix_s3_unicode.py` | Fixes Unicode issues in S3 keys | One-time use |
| `fix_unicode.py` | Fixes Unicode in local filenames | One-time use |
| `fix_va_artists.py` | Fixes "Various Artists" naming inconsistencies | One-time use |
| `inspect_mismatches.py` | Inspects metadata mismatches between sources | Diagnostic |
| `check_toc_discrepancies.py` | Compares TOC vs. actual song counts | Diagnostic |
| `sync_page_mappings.py` | Syncs page mapping data between local and S3 | Utility |
| `test_unicode.py` | Unicode handling test script | Test |
| `bedrock_load_test.py` | Bedrock API throughput testing | Test |

---

## V2 / Legacy Scripts (`scripts/` — mostly obsolete)

### `scripts/analysis/` (144 files)
Massive collection of analysis, verification, and data-fixing scripts from v2 era. Includes inventory builders, duplicate finders, provenance generators, match-quality analyzers, and reconciliation validators. **Almost entirely obsolete** — superseded by v3 pipeline and verification scripts.

### `scripts/one-off/` (119 files)
One-time-use scripts from v2: S3 structure checks, folder flattening, DynamoDB migrations, download helpers, verification batches, debugging scripts. **Obsolete** — all one-time work completed.

### `scripts/reconciliation/` (37 files)
V2 reconciliation tooling: folder rename decisions, S3 path fixes, manifest updates, decision execution. **Obsolete** — v3 uses human-readable paths directly.

### `scripts/reprocessing/` (14 files)
V2 reprocessing scripts: batch reprocess, fix page analysis format, sync to local. **Obsolete** — v3 pipeline handles all reprocessing.

### `scripts/aws/downloading/` (18 files)
PowerShell scripts for downloading processed results from S3 during v2. **Obsolete**.

### `scripts/aws/monitoring/` (23 files)
PowerShell scripts for monitoring Step Functions executions during v2 batch runs. **Obsolete**.

### `scripts/aws/processing/` (19 files)
PowerShell scripts for triggering v2 Step Functions executions. **Obsolete**.

### `scripts/aws/` (root — 6 files)
Deployment and ECS task registration scripts. **Need v3 update** for cloud deployment.

### `scripts/local/` (3 files)
PowerShell scripts for local file reorganization. **Obsolete** — one-time operations completed.

### `scripts/s3/` (14 files)
S3 browser builders, CORS config, duplicate consolidation, structure comparisons. **Mostly obsolete** — some S3 browser scripts may still be useful.

### `scripts/testing/` (8 files)
Test scripts for Bedrock verification, parsing, image formats. **Occasionally useful** for debugging.

### `scripts/utilities/` (6 files)
Project reorganization, S3 browser generation, git checkpoint. **Mostly obsolete**.

### `scripts/web/` (5 files)
HTML viewer fixers and data updaters for v2 web viewers. **Obsolete**.

### `scripts/utils/` (1 file)
`backup_helper.py` — backup utility. **Occasionally useful**.

### Other root-level scripts

| File | Purpose | In Use |
|------|---------|--------|
| `batch_process_books.py` | V2 batch processor | Obsolete |
| `check_all_status.py` | V2 status checker | Obsolete |
| `check_unprocessed.py` | V2 unprocessed book finder | Obsolete |
| `comprehensive_data_verification.py` | V2 data verification | Obsolete |
| `comprehensive_validation_demo.py` | V2 validation demo | Obsolete |
| `comprehensive_vision_validation.py` | V2 vision validation | Obsolete |
| `deep_verify.py` | V2 deep verification | Obsolete |
| `deploy_lambda_check_processed.py` | Lambda deployment helper | Needs v3 update |
| `deploy_page_analysis.py` | Page analysis Lambda deployer | Needs v3 update |
| `deploy_state_machine.py` | Step Functions deployer | Needs v3 update |
| `enable_s3_cors.py` | S3 CORS configuration | Utility |
| `fix_viewer_syntax.py` | HTML viewer syntax fixer | Obsolete |
| `monitor_batch.py` | V2 batch monitor | Obsolete |
| `monitor_prerender_progress.py` | Prerender progress monitor | Utility |
| `pipeline_api_server.py` | REST API server for pipeline | Unused |
| `prerender_source_songbooks.py` | V2 prerender script | Obsolete |
| `process_book_to_final.py` | V2 final processor | Obsolete |
| `quick_status.py` | V2 quick status | Obsolete |
| `retry_single_book.py` | V2 retry helper | Obsolete |
| `run_remaining_books.py` | V2 remaining books runner | Obsolete |
| `sync_all_successful_books.py` | V2 sync helper | Obsolete |
| `test_validation_broadway.py` | Broadway test case | Test |
| `update_s3_manifests.py` | V2 manifest updater | Obsolete |
| `update_state_machine_task_definitions.py` | Step Functions task def updater | Needs v3 update |
| `validate_songbook_quality.py` | V2 quality validator | Obsolete |
| `validate_with_local_llm.py` | Local LLM validation experiment | Obsolete |
| `verify_all_data_stores.py` | V2 data store verifier | Obsolete |
| `verify_and_sync.py` | V2 verify-and-sync | Obsolete |
| `vision_validation.py` | V2 vision validation | Obsolete |

---

## Web Viewers (`web/`)

### Active Viewers

| File | Purpose | In Use |
|------|---------|--------|
| `v3_book_index.html` | **Main dashboard** — 342-book index with song counts, drill-down, links to all editors | **Yes — primary** |
| `editors/v3_split_editor.html` | Visual split editor — edit song boundaries with PDF thumbnails | **Yes — primary** |
| `editors/boundary_review.html` | Boundary review — dual-strip comparison of input vs. output PDFs | **Yes — primary** |
| `viewers/v3_provenance_viewer.html` | V3 provenance — shows full pipeline lineage for a book | Yes |

### Legacy/Obsolete Viewers

| File | Purpose | In Use |
|------|---------|--------|
| `editors/manual_split_editor.html` | V2 manual split editor | Obsolete |
| `editors/manual_split_editor_integrated.html` | V2 integrated split editor | Obsolete |
| `viewers/book_lineage_viewer.html` | V2 book lineage viewer | Obsolete |
| `viewers/complete_lineage_viewer.html` | V2 complete lineage viewer | Obsolete |
| `viewers/complete_provenance_viewer.html` | V2 provenance viewer | Obsolete |
| `viewers/complete_provenance_viewer_broken.html` | Broken copy | Dead |
| `viewers/v2_provenance_viewer.html` | V2 provenance viewer | Obsolete |
| `viewers/auto_polling.js` | Auto-polling JS for v2 viewers | Obsolete |
| `viewers/ENABLE_AUTO_POLLING.txt` | Instructions for auto-polling | Obsolete |
| `complete_lineage_viewer.html` | V2 lineage viewer (root copy) | Obsolete |
| `complete_lineage_data_embedded.js` | Embedded lineage data | Obsolete |
| `comprehensive_data_report.html` | V2 data report | Obsolete |
| `match-quality-viewer.html` | V2 match quality viewer | Obsolete |
| `match-quality-viewer-enhanced.html` | V2 enhanced match viewer | Obsolete |
| `match-quality-viewer-enhanced.html.backup*` | **25 backup copies** of match viewer | Dead |
| `match-quality-data.js` | Embedded match data | Obsolete |
| `v2_data_embedded.js` | Embedded v2 data | Obsolete |
| `v2_report_standalone.html` | V2 standalone report | Obsolete |

### `web/s3-browser/` (6 files)
Interactive S3 bucket browsers built during v2. **Obsolete** — direct S3 access via CLI is used instead.

### `web/verification/`
V2 verification results (text summaries from batch verification runs). **Obsolete**.

---

## Data Files (`data/`)

### `data/v3_verification/` — Active

| File | Purpose | In Use |
|------|---------|--------|
| `boundary_verification_report.json` | Song boundary verification results | Yes |
| `categorized_issues.json` | Categorized issues (absorbed songs, overlaps, etc.) — feeds boundary_review.html | Yes |
| `overlap_analysis_results.json` | Overlap analysis between adjacent songs | Yes |
| `page_verification_report.json` | Per-page verification results | Yes |
| `v3_verification_report.json` | Full v3 verification report | Yes |
| `v3_verification_report.txt` | Text version of report | Yes |
| `inspect/` | Inspection data for individual books | Diagnostic |

### `data/verification/` — Obsolete
56 checkpoint files (`checkpoint_10.json` through `checkpoint_560.json`) plus verification reports from v2 batch verification runs.

### `data/misc/` — Mixed
Assorted test inputs, temp files, state machine definitions, and review feedback from v2 sessions. Mostly obsolete.

### Other `data/` subdirs
`analysis/`, `backups/`, `batch_executions/`, `comparisons/`, `downloads/`, `execution/`, `inventories/`, `manual_splits/`, `processing/`, `reconciliation/`, `samples/` — all v2 era data. **Obsolete**.

---

## Documentation (`docs/`)

### Still Relevant

| File | Purpose |
|------|---------|
| `v3-pipeline-design.md` | V3 pipeline architecture document |
| `PIPELINE_LEARNINGS_2026-02-05.md` | Lessons learned from v3 batch processing |
| `PROJECT_CHECKPOINT_2026-02-05.md` | Project state as of Feb 5 |
| `PROJECT_CHECKPOINT_2026-02-08.md` | Project state as of Feb 8 |
| `COMPLETE_DATA_MODEL.md` | Full data model documentation |
| `operations/BATCH_PROCESSING_README.md` | Batch processing guide |
| `operations/BOOK_REVIEW_README.md` | Book review workflow guide |
| `design/CORRECT_ALGORITHM.md` | Correct splitting algorithm description |

### Obsolete
Everything in `docs/analysis/`, `docs/issues-resolved/`, `docs/summaries/`, `docs/deployment/`, `docs/s3/`, `docs/archive/`, `docs/comparisons/`, `docs/project-status/`, `docs/updates/` — all v2 era analysis and status reports.

---

## Root-Level Files

### Config/Build

| File | Purpose | In Use |
|------|---------|--------|
| `Dockerfile` | Docker image for ECS tasks | Needs v3 update |
| `requirements.txt` | Python dependencies | Yes |
| `songbook-splitter.code-workspace` | VS Code workspace settings | Yes |
| `cors-config.json` | S3 CORS configuration | Reference |
| `s3-public-policy.json` | S3 bucket policy | Reference |

### Documentation (root)

| File | Purpose | In Use |
|------|---------|--------|
| `README.md` | Project README | Yes |
| `START_HERE.md` | Getting started guide | Yes |
| `PROJECT_CONTEXT.md` | High-level project context | Yes |
| `API_SERVER_GUIDE.md` | API server documentation | Obsolete |
| `EXECUTE_DECISIONS.md` | V2 reconciliation execution guide | Obsolete |
| `OPERATOR_RUNBOOK.md` | V2 operator runbook | Partially relevant |
| `RECONCILIATION_GUIDE.md` | V2 reconciliation guide | Obsolete |
| `RECONCILIATION_PROJECT_OVERVIEW.md` | V2 reconciliation overview | Obsolete |
| `REPROCESSING_GUIDE.md` | V2 reprocessing guide | Obsolete |
| `PROJECT_CHECKPOINT_2026-01-31.md` | Jan 31 checkpoint | Historical |

### Data Files (root — all obsolete)

| File | Purpose |
|------|---------|
| `reconciliation_decisions_*.json` (20 files) | V2 reconciliation decision files — various iterations |
| `v3_splits_594e8e0eb2c37bd0*.json` (12 files) | Split editor exports for Billy Joel - My Lives (various iterations) |
| `v3_splits_a0ebbf6ec9ecc86e_corrected.json` | Corrected splits for one book |
| `absorption_fixes_2026-02-13.json` | Boundary fix decisions from today |
| `abbey_road_holistic_analysis.json` | One-off analysis output |
| `book_reconciliation_validated.csv` | V2 reconciliation CSV |
| `dupe_books_to_reprocess.json` | V2 duplicate list |
| `reprocess_dupe_log.json` | V2 reprocess log |
| `mobilesheets_import.csv` | MobileSheets import data |
| `poor_folders_copy_list.csv` | V2 folder copy list |
| `prerender_results.json` | Prerender results |
| `reconciliation_file_operations_comparison.csv` | V2 comparison CSV |
| `reconciliation_retry_2026-02-02.json` | V2 retry data |
| `test_analysis_v2-*.json` | V2 test analysis |
| `verification_results.json` | V2 verification results |
| `vision_validation_results.json` | V2 vision validation |

### Log Files (root)

| File | Purpose |
|------|---------|
| `batch_300_progress.log` | V2 batch progress |
| `batch_progress.log` | V2 batch progress |
| `prerender_all_559_books.log` | V2 prerender log |
| `prerender_all_559_books_resume.log` | V2 prerender resume log |
| `prerender_source_songbooks.log` | V2 prerender log |
| `server.log` | HTTP server log |
| `verification_run.log` | V2 verification log |
| `vision_validation.log` | V2 vision validation log |

### Temp Files (root)

`temp_*.json`, `temp_*.py`, `nul`, `Worksongbook-splittertemp_queen_pa.json` — all temporary/debug artifacts. **Can be deleted**.

---

## Other Root-Level Directories

### `SheetMusic_FakeAndScores/` (22 folders)
Fake books and score compilations (Broadway, Movie/TV, category collections). Separate from the main 342-book collection.

### `SheetMusicIndividualSheets/` (279 folders)
Individual song sheets organized by artist. Not songbooks — these are single-song PDFs. Separate from the pipeline.

### `toc_cache/` (999 files)
Cached TOC analysis results keyed by book_id hash. Used by v2 pipeline. **Obsolete** — v3 stores TOC data as artifacts.

### `verification_batches/` (18 files)
V2 batch verification scripts and file lists. **Obsolete**.

### `temp/` directory
ExifTool installation (Image-ExifTool-13.48) and its HTML documentation. Used for PDF metadata extraction experiments. **Mostly obsolete** — only the exiftool binary is occasionally used.

### `exiftool.exe` + `exiftool_files/`
ExifTool binary and supporting files. **Occasionally used** for PDF metadata inspection.

### `logs/` directory
Subdirs: `misc/`, `processing/`, `reorganization/`, `testing/` — all v2 era logs. **Obsolete**.

### `output/` directory
V2 output manifests. **Obsolete**.

### `.kiro/` directory
Kiro AI assistant specs and steering files from initial project setup. **Historical reference only**.

---

## Tests (`tests/`)

| File | Purpose | In Use |
|------|---------|--------|
| `__init__.py` | Package init | Yes |
| `unit/test_artist_resolution.py` | Artist name resolution tests | Yes |
| `unit/test_dynamodb_ledger.py` | DynamoDB ledger tests | Yes |
| `unit/test_error_handling.py` | Error handling tests | Yes |
| `unit/test_models.py` | Data model tests | Yes |
| `unit/test_quality_gates.py` | Quality gates tests | Yes |
| `unit/test_s3_utils.py` | S3 utility tests | Yes |
| `unit/test_sanitization.py` | Sanitization tests | Yes |
| `unit/test_toc_discovery.py` | TOC discovery tests | Yes |
| `unit/test_toc_parser.py` | TOC parser tests | Yes |
| `fixtures/test_5_known_errors.txt` | Test fixture — known error cases | Yes |
| `fixtures/test-james-taylor-fire-and-rain.pdf` | Test fixture — sample PDF | Yes |

---

## Root-Level Python Scripts (non-pipeline)

| File | Purpose | In Use |
|------|---------|--------|
| `copy_to_mobilesheets.py` | Copies song PDFs to MobileSheets folder structure | Utility |
| `generate_mobilesheets_csv.py` | Generates CSV for MobileSheets import | Utility |
| `prep_mobilesheets.py` | Prepares MobileSheets data | Utility |
| `restructure_individual_sheets.py` | Reorganizes individual sheet music files | One-time use |
| `restructure_mobilesheets.py` | Restructures for MobileSheets | One-time use |

---

## Summary Statistics

| Category | Count | Status |
|----------|-------|--------|
| Core app Python files | 18 | Active |
| V3 pipeline scripts | ~15 | Active |
| Web viewers (active) | 4 | Active |
| Unit tests | 10 | Active |
| V2/legacy scripts | ~370 | Obsolete |
| V2/legacy web viewers | ~40 | Obsolete |
| V2 data/logs/temp files | ~200+ | Obsolete |
| Documentation files | ~60 | ~10 relevant, rest obsolete |
| Root-level junk (temp, logs, reconciliation) | ~60 | Can be deleted |
| Total Python files (excl. build/) | 409 | ~33 active, rest legacy |

---

## Cleanup Candidates

If you want to reduce the workspace footprint, these are safe to remove:

1. **Root temp files**: All `temp_*.json`, `temp_*.py`, `nul`, `Worksongbook-splittertemp_queen_pa.json`
2. **Root reconciliation files**: All 20 `reconciliation_decisions_*.json` files
3. **Root v3_splits files**: All 12 `v3_splits_*.json` files (applied already)
4. **Root log files**: All `*.log` files, `verification_results.json`, `vision_validation_results.json`
5. **`toc_cache/`**: 999 v2 cache files
6. **`verification_batches/`**: 18 v2 batch files
7. **`web/match-quality-viewer-enhanced.html.backup*`**: 25 backup copies
8. **`scripts/analysis/`**: 144 v2 analysis scripts
9. **`scripts/one-off/`**: 119 v2 one-off scripts
10. **`scripts/reconciliation/`**: 37 v2 reconciliation scripts
11. **`data/verification/`**: 56 v2 checkpoint files
12. **`build/lambda-package/`**: Stale pre-v3 Lambda package
13. **`ecs/docs/`**: Duplicate of `docs/` directory
14. **`logs/`**: V2 era logs
15. **`output/`**: V2 manifests
16. **`temp/`**: ExifTool installation + docs (keep `exiftool.exe` if needed)
