# File Reference — Songbook Splitter

Every file remaining in the active workspace, described in detail.

---

## Core Application — `app/`

The pipeline application code. Used by both local orchestration (`scripts/run_v3_single_book.py`) and cloud execution (ECS/Lambda).

### `app/__init__.py`
Package init. Single docstring: "SheetMusic Book Splitter - Main application package". No executable code.

### `app/main.py`
ECS container entry point. Reads `TASK_TYPE` environment variable and dispatches to the matching handler in `ecs/task_entrypoints.py`. Supports 7 task types: `toc_discovery`, `toc_parser`, `page_analysis`, `page_mapper`, `song_verifier`, `pdf_splitter`, `manifest_generator`.

### `app/models.py`
Dataclass definitions for all pipeline data structures with JSON serialization. Key classes:
- `TOCEntry` — single TOC line (title, page number, optional artist, confidence)
- `SongLocation` — mapped song position (printed page → PDF index)
- `VerifiedSong` — song after verification with page range adjustments
- `PageRange` — extraction range (start/end pages, 0-based)
- `OutputFile` — output PDF metadata (S3 URI, file size, page range)
- `TOCDiscoveryResult`, `TOCParseResult`, `PageMapping`, `Manifest` — phase result containers

### `app/services/bedrock_parser.py`
AWS Bedrock (Claude) integration for LLM-based TOC parsing. `BedrockParserService` sends TOC page images to Claude 3.5 Sonnet via the vision API (4000 input / 2000 output token limits) to extract structured song entries. Falls back to text-based LLM parsing when vision fails. Handles per-song artist extraction for Various Artists books. Includes `MockBedrock` for local testing.

### `app/services/holistic_page_analyzer.py`
Multi-phase vision-based page analysis that scans all PDF pages to detect song starts and boundaries. `HolisticPageAnalyzer` runs a 5-phase process: (1) full page scan with parallel Bedrock vision workers, (2) match detected song starts to TOC entries, (3) calculate page offset, (4) fallback matching for unmatched songs, (5) assign final boundaries. Workers use exponential backoff retry for Bedrock throttling. **Currently has uncommitted modifications.**

### `app/services/improved_page_mapper.py`
Enhanced page mapper that uses `page_analysis.json` artifact as primary data source. `ImprovedPageMapperService.build_page_mapping_from_analysis()` reads previously-detected song starts, verifies each with strict vision checks (requires title + music notation), and searches nearby pages (±N) when verification fails. Falls back to full vision-based scanning when no page_analysis artifact exists.

### `app/services/page_analyzer.py`
Per-page Bedrock vision analysis service. `PageAnalyzerService.analyze_book()` runs three phases: (1) analyze every page individually with Claude vision (classify as song_start, song_continuation, toc, filler, etc.; extract printed page numbers and detected titles), (2) calculate page offset from calibration points, (3) compute song boundaries from offset + TOC. Produces `page_analysis.json` — the most expensive and time-consuming pipeline step (~1 Bedrock call per page).

### `app/services/page_mapper.py`
Original page mapper using pre-rendered images and vision verification. `PageMapperService` renders all PDF pages to PNG, then searches through images for each song title using Bedrock vision. Calculates offsets from found matches and handles Various Artists detection. More thorough but slower than `improved_page_mapper.py`.

### `app/services/pdf_splitter.py`
Final output generation. `PDFSplitterService.split_pdf()` takes verified song page ranges and extracts them from the source PDF using PyMuPDF page insertion (preserves vector graphics — no re-rendering). Resolves per-song artists, generates sanitized filenames, and writes individual song PDFs to both S3 and local filesystem.

### `app/services/quality_gates.py`
Pipeline checkpoint validation. Three gates:
- `check_toc_quality_gate()` — requires ≥10 TOC entries (bypassable for short books)
- `check_verification_quality_gate()` — requires ≥95% song verification success
- `check_output_quality_gate()` — requires ≥90% extraction success, supports partial output

Returns `QualityGateResult` with pass/fail status, metric value, threshold, and details. `aggregate_quality_gates()` combines multiple results into overall status.

### `app/services/song_verifier.py`
Verification layer that confirms vision-detected song starts. `SongVerifierService.verify_song_starts()` checks each song's first page for: (1) musical staff lines via horizontal line detection in rendered images, (2) title text match via PyMuPDF text extraction. If verification fails, searches ±N nearby pages. Produces final adjusted page ranges via `adjust_page_ranges()`.

### `app/services/toc_discovery.py`
Pipeline stage 1 — locates Table of Contents pages. `TOCDiscoveryService.discover_toc()` renders each page to a PIL image, scores TOC likelihood using Bedrock vision, and selects pages above threshold (including consecutive pages). Extracts text via AWS Textract OCR. Includes `MockTextract` for local mode.

### `app/services/toc_parser.py`
Pipeline stage 2 — parses OCR text into structured song entries. `TOCParser.parse_toc()` tries Bedrock LLM first, then falls back to deterministic regex parsing with 5 patterns: (1) dots separator (`Song Title ... 42`), (2) page-first (`42. Song Title`), (3) parentheses artist (`Song (Artist) ... 42`), (4) hyphen artist (`Song - Artist ... 42`), (5) multiple spaces (`Song    42`). Also extracts per-song artist overrides for Various Artists books.

### `app/utils/__init__.py`
Package init exporting public API: 6 sanitization functions and 5 artist resolution functions.

### `app/utils/artist_resolution.py`
Artist name normalization. Key functions:
- `is_various_artists()` — detects "Various Artists", "VA", "Assorted" and other indicators
- `resolve_artist()` — returns song-level artist for VA books, book-level artist otherwise
- `normalize_artist_name()` — normalizes featuring notation, ampersands, slashes to filesystem-safe format
- `extract_artist_from_toc_entry()` — pulls artist from TOC lines using parentheses/hyphen patterns

### `app/utils/cloudwatch_utils.py`
CloudWatch metrics and structured JSON logging. `CloudWatchUtils` emits custom metrics (processing time, success rate, cost per book, errors). `StructuredLogger` produces JSON log lines with correlation IDs for tracing. Includes `MockCloudWatch` for local mode. Only active during cloud execution.

### `app/utils/dynamodb_ledger.py`
DynamoDB state tracking for `jsmith-pipeline-ledger` table (v3 schema). `DynamoDBLedger` provides:
- `generate_book_id()` — SHA256 hash from S3 URI
- `check_already_processed()` — idempotency check (skip if status='success')
- `record_processing_start/complete()` — lifecycle tracking
- `update_step()` — per-step progress (toc_discovery, toc_parse, page_analysis, page_mapping, song_verification, pdf_splitting)

Uses `Decimal(str(value))` for all floats (DynamoDB requirement). Includes `MockDynamoDB` for local mode.

### `app/utils/error_handling.py`
Error resilience framework. Custom exception hierarchy: `PipelineError` → `TOCExtractionError`, `PageMappingError`, `VerificationError`, `SplittingError`, `QualityGateError`. Provides:
- `retry_with_backoff()` — decorator with exponential backoff
- `handle_aws_throttling()` — specific retry for AWS ThrottlingException
- `GracefulDegradation` — context manager for fallback behavior
- `ErrorAggregator` — collects errors during batch operations without halting

### `app/utils/s3_utils.py`
Abstracted storage layer. `S3Utils` wraps S3 operations with local filesystem fallback for development. Key methods: `list_pdfs()`, `download_file()`, `upload_file()`, `write_bytes()`, `read_bytes()`. Transparently routes to S3 or local paths based on configuration, enabling the same pipeline code to run locally or in AWS.

### `app/utils/sanitization.py`
Filename and path generation for Windows/S3 compatibility. Key functions:
- `sanitize_filename()` — removes `<>:"/\|?*`, control chars, normalizes Unicode NFC, limits to 200 chars
- `generate_output_path()` — creates S3 key: `v3/{BookArtist}/{BookName}/{Artist} - {Title}.pdf`
- `sanitize_artist_name/song_title/book_name()` — type-specific sanitization with title casing
- `to_title_case()` — preserves Roman numerals (Vol. II, Part III)

### `app/utils/README.md`
Documentation for the sanitization module. Covers all function signatures with examples, design decisions (200-char limit rationale, NFC normalization choice, hyphen replacement), and test instructions.

---

## Lambda Functions — `lambda/`

AWS Lambda handlers for the Step Functions state machine. Need v3 path updates before cloud re-deployment.

### `lambda/ingest_service.py`
S3 event handler triggered when a PDF is uploaded to `jsmith-input` with `v3/` prefix. Scans the bucket for unprocessed books, generates book IDs via SHA256, checks DynamoDB ledger to skip already-processed books, and starts Step Functions executions for new ones.

### `lambda/state_machine_helpers.py`
Four Lambda handlers for Step Functions orchestration:
- `check_processed_handler()` — idempotency check before processing starts
- `record_start_handler()` — creates DynamoDB ledger entry with status "in_progress"
- `record_success_handler()` — updates ledger with final song count, cost, duration
- `record_failure_handler()` / `record_manual_review_handler()` — captures errors and quality gate rejections

Handles `Decimal` type conversions for DynamoDB float fields.

### `lambda/app/services/page_analyzer.py`
Copy of `app/services/page_analyzer.py` included in the Lambda deployment package. Required because Lambda packages need all dependencies co-located. Should be kept in sync with the main copy.

---

## ECS Task Definitions — `ecs/`

### `ecs/task_entrypoints.py`
Entry point dispatcher for 6 containerized ECS Fargate tasks. Each function downloads the source PDF from S3, executes its processing service, and writes artifacts to `jsmith-artifacts` with v3 human-readable paths (`v3/{Artist}/{Book}/`). Tasks:
1. `toc_discovery_task()` — find and OCR table of contents pages
2. `toc_parser_task()` — parse TOC text into song entries
3. `page_analysis_task()` — vision-analyze all pages
4. `page_mapper_task()` — map TOC entries to PDF pages
5. `song_verifier_task()` — verify song boundaries
6. `pdf_splitter_task()` — extract individual song PDFs

---

## Infrastructure — `infra/`

### `infra/cloudformation_template.yaml`
Complete CloudFormation stack defining all AWS resources: S3 buckets (jsmith-input, jsmith-output, jsmith-artifacts), DynamoDB table (jsmith-processing-ledger with status GSI), ECS cluster + Fargate task definitions, Lambda functions (6), Step Functions state machine, IAM roles (execution + task), ECR repository, and CloudWatch configuration. Region: us-east-1, Account: 227027150061.

### `infra/step_functions_complete.json`
Complete Step Functions state machine definition with all 6 processing stages, error handling, retry logic, and parallel task orchestration. Reference for cloud deployment.

### `infra/step_functions_full_test.json`
Test variant of the state machine with additional logging and debugging states. Used during initial deployment validation.

### `infra/step_functions_simple_fixed.json`
Simplified state machine with fewer stages for rapid iteration testing. Subset of the complete definition.

### `infra/step_functions_state_machine.json`
Another state machine variant. Used as input for `deploy_state_machine.py` deployment script.

### `infra/task-def-toc-parser.json`
Sample ECS task definition JSON for the TOC parser task. Template for registering other task definitions.

---

## V3 Pipeline Scripts — `scripts/`

### Primary Pipeline

#### `scripts/run_v3_single_book.py`
**Main local orchestration script.** Runs the full 6-step pipeline for one book: TOC discovery → TOC parse → page analysis → page mapping → song verification → PDF splitting. Checks S3 for existing artifacts before each step and skips if present (stop/start capability). Supports `--dry-run` and `--force-step <name>` (cascades to downstream steps). Updates DynamoDB per-step tracking. Usage: `py scripts/run_v3_single_book.py --artist "Billy Joel" --book "My Lives"`.

#### `scripts/run_v3_batch.py`
**Batch runner for processing multiple books in parallel.** Uses `ThreadPoolExecutor` with configurable concurrency (default: 4 parallel books × 6 Bedrock workers = 24 concurrent calls). Auto-skips already-processed books by checking S3 artifacts. Supports `--all` to process everything, or `--artist`/`--book` filters. **Has uncommitted modifications.**

#### `scripts/regenerate_v3_index.py`
**Generates the web dashboard** (`web/v3_book_index.html`) by scanning all `SheetMusic_Artifacts/{Artist}/{Book}/` directories. Reads all 6 artifact files per book, extracts song counts from 4 sources (output files, TOC, vision detection, local disk), and produces a searchable HTML table with expandable drill-down rows showing all song titles, mismatch highlighting, and links to the provenance viewer, boundary review editor, and split editor.

### Verification Tools

#### `scripts/verify_all_complete.py`
**Primary verification script.** Cross-checks all 342 books across 11 dimensions: 6 artifacts exist locally, song counts match between verified_songs/output_files/page_mapping, page ranges are contiguous with no overlaps, DynamoDB entries exist with correct metadata. Reports mismatches at the field level.

#### `scripts/verify_all_artifacts.py`
Verifies all 6 V3 artifacts exist in both local filesystem and S3. Pre-fetches S3 inventory for efficiency. Checks JSON validity, cross-references song counts between artifacts, verifies output PDFs exist locally and in S3, and confirms DynamoDB entries are present.

#### `scripts/verify_v3_comprehensive.py`
Ultra-detailed 5-phase verification: (1) build S3 inventory, (2) per-book checks with schema validation for each artifact type, (3) cross-artifact consistency (no overlaps, no gaps, correct page ranges), (4) global checks (orphan detection, unprocessed input detection), (5) generate reports. The most thorough verification script.

#### `scripts/verify_boundaries.py`
Cross-references `page_analysis.json` (Bedrock vision results) with `verified_songs.json` to check boundary accuracy. Verifies: first page of each song has `content_type: song_start`, detected titles match expected titles, middle pages are `song_continuation`, no songs are cut short. Supports optional Ollama vision verification.

#### `scripts/verify_song_pages.py`
Physical page verification using perceptual hashing. Renders each extracted song PDF page and the corresponding source book page at 72 DPI, computes pHash (perceptual hash) with a 15-unit threshold, and flags mismatches. Uses `ProcessPoolExecutor` for parallel rendering and the pre-rendered image cache at `S:/SlowImageCache/pdf_verification_v3/`.

### Web Server

#### `scripts/boundary_review_server.py`
Local HTTP server (Python `http.server`) powering the boundary review web UI. Provides API endpoints:
- `POST /api/preview-fix` — preview what a boundary adjustment would produce
- `POST /api/apply-fix` — apply the fix: re-extract song PDFs with PyMuPDF, update `verified_songs.json`, `output_files.json`, `page_mapping.json`, upload to S3, sync locally

### Correction Tools

#### `scripts/apply_split_exports.py`
Applies manually-corrected splits exported from the v3 split editor. Replaces `verified_songs.json` with the corrected version, deletes old output PDFs from both local and S3, re-extracts songs from the source PDF using PyMuPDF, updates `output_files.json`, and uploads everything to S3. Used after manual boundary editing sessions.

#### `scripts/apply_overlap_fixes.py`
Applies overlap corrections from `data/v3_verification/overlap_analysis_results.json`. Updates page ranges in `verified_songs.json` and `output_files.json`, re-extracts only the affected song PDFs using PyPDF2, and uploads corrected files to S3.

### One-Time Fix Scripts

These were used to fix specific data issues and have already been applied. Kept for reference.

#### `scripts/fix_all_metadata.py`
Bulk metadata repair. Corrects DynamoDB `artist`, `book_name`, and `source_pdf_uri` fields to match artifact folder names. Fixes S3 input key casing. Syncs `output_files.json` file sizes with actual local file sizes.

#### `scripts/fix_classic_rock_splits.py`
Fixes "Classic Rock 73 Songs": splits 3 over-merged songs, adds 2 missing songs, removes 1 bogus entry, renames files to include performing artist names. Hardcoded split/merge/delete list.

#### `scripts/fix_elvis_splits.py`
Fixes "Elvis Presley / The Compleat": splits 2 concatenated songs ("Baby I Don't Care" → adds "Don't", "Love Me" → adds "Love Me Tender"). Directly modifies song arrays.

#### `scripts/fix_four_books.py`
Deletes 2 invalid books (Tom Lehrer/Book Covers, John Denver/Back Home Again), removes phantom songs from Neil Young/Decade, and re-splits Pink Floyd/Anthology from a corrected export file.

#### `scripts/fix_mccartney_allthebest.py`
Fixes "Paul McCartney / All The Best": applies corrected splits, re-extracts changed songs, deletes removed songs from S3 and local, updates artifacts.

#### `scripts/fix_overlaps_with_vision.py`
Diagnostic script that identifies page overlaps across all books, loads cached images from the image cache, sends overlap pages to Bedrock Claude vision to determine correct song boundaries, and generates recommendations saved to `overlap_analysis_results.json`.

#### `scripts/fix_s3_unicode.py`
Fixes corrupted Unicode in 8 specific S3 song PDFs (Paradise Café, Déjà Vu, etc.). Uploads correct local versions, deletes corrupted S3 keys. Hardcoded file list.

#### `scripts/fix_unicode.py`
Fixes non-ASCII characters in song titles across the collection. Renames local files and S3 objects, updates `output_files.json` and `verified_songs.json` via explicit title mapping.

#### `scripts/fix_va_artists.py`
Fixes "Various Artists" song filenames to use actual performing artists (e.g., "Classic Rock 73 Songs": Heart, Peter Frampton, etc.). Updates metadata and renames files in both local and S3. Uses hardcoded `ARTIST_DATA` dict.

### Diagnostic Scripts

#### `scripts/inspect_mismatches.py`
Visual inspection of page mismatches flagged by `verify_song_pages.py`. Loads the song PDF and cache image side-by-side, computes dHash/pHash distances, and saves comparison JPGs to `data/v3_verification/inspect/` for human review.

#### `scripts/check_toc_discrepancies.py`
Finds books with mismatches between TOC entry count, verified_songs count, and output_files count. Uses fuzzy title matching (20-char prefix + substring checks) to reduce false positives from minor title variations.

### Utility Scripts

#### `scripts/prerender_v3_images.py`
Pre-renders all 342 books to the JPG image cache at `S:/SlowImageCache/pdf_verification_v3/`. Renders at 200 DPI, JPG quality 85%, one file per page (`page_NNNN.jpg`). Uses `ThreadPoolExecutor` and skips already-cached pages. ~38,000 pages, ~6.7 GB total.

#### `scripts/sync_page_mappings.py`
Regenerates `page_mapping.json` from `verified_songs.json` for books where boundary fixes were applied via the web UI. Recalculates printed page numbers using offset: `printed_page = pdf_index + offset + 1`.

#### `scripts/enable_s3_cors.py`
Configures CORS on S3 buckets to allow browser-based access from the web viewers. One-time setup utility.

#### `scripts/monitor_prerender_progress.py`
Monitors the progress of the `prerender_v3_images.py` script by counting cached images vs. expected total pages. Displays per-book completion status.

### Test & Performance Scripts

#### `scripts/test_unicode.py`
Unit tests for Unicode character cleaning: mojibake pattern detection, double-encoded UTF-8 recovery, NFKD normalization, accent stripping.

#### `scripts/bedrock_load_test.py`
Bedrock API throughput testing. Ramps concurrent vision calls (1→2→4→8→12→16→20), measures RPM/RPS, latency p50/p90, token usage, and identifies the optimal parallelism ceiling. Found: 24 concurrent is optimal, throttling starts at ~50.

### Cloud Deployment Scripts

#### `scripts/deploy_lambda_check_processed.py`
Deploys updated `check-processed` Lambda function with `force_reprocess` flag support. Creates a ZIP from `lambda/state_machine_helpers.py` and pushes via `boto3`.

#### `scripts/deploy_page_analysis.py`
Deploys the page analysis ECS task definition and updates the Step Functions state machine to include the PageAnalysis step. Extracts network config from existing state machine. Requires Docker image already pushed to ECR.

#### `scripts/deploy_state_machine.py`
Deploys updated Step Functions state machine definition from `infra/step_functions_state_machine.json`. Substitutes ARN placeholders with values from the current deployment.

#### `scripts/update_state_machine_task_definitions.py`
Updates Step Functions state machine to use latest ECS task definition revisions. Fixes Docker image pull issues by ensuring `:latest` tag instead of pinned SHA256 digests.

### `scripts/utils/backup_helper.py`
Backup utility providing helper functions for saving/restoring artifact files during fix operations.

### `scripts/testing/`

#### `scripts/testing/test_bedrock_verification.py`
Tests Bedrock vision API responses for song start detection. Sends sample page images and verifies the response format and accuracy.

#### `scripts/testing/test_correct_offset.py`
Tests page offset calculation logic with known test cases. Verifies that printed page → PDF page mapping produces correct offsets.

#### `scripts/testing/test_image_formats.py`
Tests image format handling (PNG, JPG, TIFF) for Bedrock vision API compatibility. Verifies format conversion and size constraints.

#### `scripts/testing/test_known_errors.py`
Tests pipeline behavior on known error cases from `tests/fixtures/test_5_known_errors.txt`. Verifies error handling and graceful degradation.

#### `scripts/testing/test_parsing.py`
Tests TOC text parsing with various formatting patterns. Exercises all 5 regex patterns plus Bedrock fallback.

#### `scripts/testing/test_specific_pdfs.py`
Tests pipeline against specific problem PDFs that previously caused failures. Regression testing for edge cases.

#### `scripts/testing/test_verification_setup.py`
Tests the verification infrastructure: image cache availability, hash comparison thresholds, and rendering configuration.

#### `scripts/testing/start_review_server.ps1`
PowerShell launcher for the split detection Flask server. Installs Flask/Flask-CORS if missing, then starts `split_detection_server.py`.

#### `scripts/testing/check_ollama_performance.ps1`
Tests local Ollama LLM performance for offline vision analysis. Experimental — Ollama was evaluated but Bedrock was chosen for production.

### `scripts/aws/`

#### `scripts/aws/deploy.ps1`
Deploys the full CloudFormation stack (`jsmith-sheetmusic-splitter`) from `infra/cloudformation_template.yaml`. Configures VPC, subnet, and container image parameters. Waits for stack creation and displays outputs.

#### `scripts/aws/deploy-docker.ps1`
4-step Docker deployment: (1) ECR login, (2) build Docker image from Dockerfile, (3) tag for ECR, (4) push to `227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest`.

#### `scripts/aws/deploy-lambda.ps1`
6-step Lambda deployment: (1) clean old package, (2) create package directory, (3) copy Lambda + app code, (4) install pip dependencies, (5) create ZIP, (6) upload to S3 and update all 6 Lambda functions.

#### `scripts/aws/cleanup.ps1`
**Destructive** — tears down all AWS resources. Empties S3 buckets, deletes CloudFormation stack, removes ECR repository. Requires typing "DELETE" to confirm.

#### `scripts/aws/register-all-tasks.ps1`
Registers 5 ECS Fargate task definitions (toc-parser, page-mapper, song-verifier, pdf-splitter, manifest-generator) with inline JSON task definitions. Uses hardcoded IAM role ARNs.

#### `scripts/aws/register-ecs-tasks.ps1`
Same as above but fetches IAM role ARNs from CloudFormation stack outputs, with fallback to constructed ARNs. More robust version.

#### `scripts/aws/register-ecs-tasks-simple.ps1`
Simplest version — clones the existing toc-discovery task definition as a template, modifies the task name and TASK_TYPE, and registers each variant. No hardcoded ARNs.

---

## Web Viewers — `web/`

### `web/v3_book_index.html`
**Main dashboard.** Generated by `scripts/regenerate_v3_index.py`. Displays all 342 books in a searchable, sortable table with: artist, book name, page count, 4 song count columns (output, TOC, vision, disk), and action buttons (Provenance, Review, Split). Expandable rows show all song titles from each source with mismatch highlighting. Dark theme with cyan accents.

### `web/editors/v3_split_editor.html`
**Visual split editor.** Loads a book's source PDF via PDF.js, renders page thumbnails at 0.15 scale, and displays song boundaries as color-coded regions. Users can drag split points, add/remove songs, and export corrected `verified_songs.json` for application via `apply_split_exports.py`. Supports auto-loading from URL parameters (`?artist=...&book=...`). **Has uncommitted modifications.**

### `web/editors/boundary_review.html`
**Boundary review tool.** Dual-strip viewer showing input PDF thumbnails (top row) alongside extracted song PDF thumbnails (bottom row) for side-by-side comparison. Color-codes pages by song, marks uncovered pages in red, and highlights absorbed songs with orange warnings. Loads data from artifact JSONs and renders PDFs with PDF.js. Supports URL-parameter book loading and works with `boundary_review_server.py` for applying fixes.

### `web/viewers/v3_provenance_viewer.html`
**Processing lineage viewer.** Shows complete pipeline history for a book: source PDF URI, each processing step with timestamps and duration, all 6 artifacts with contents, song list with page mappings, and verification results with confidence metrics. Loaded via URL parameters.

---

## Data — `data/`

### `data/v3_verification/boundary_verification_report.json`
Results from `verify_boundaries.py`. Per-book boundary accuracy: which songs have correct first-page classification, title match rates, and absorbed song detections. Used to identify the 99 songs across 40 books with absorption issues.

### `data/v3_verification/categorized_issues.json`
Issues categorized by type: `absorbed_song` (99 songs), `overlap` (songs sharing pages), `gap` (missing page coverage), `title_mismatch`. Grouped by artist/book with specific page numbers and detected vs. expected titles. Feeds the boundary review viewer's `PROBLEM_BOOKS` array.

### `data/v3_verification/overlap_analysis_results.json`
Bedrock vision analysis of overlapping pages. For each overlap, contains the vision model's determination of which song the page actually belongs to, with confidence scores. Generated by `fix_overlaps_with_vision.py`.

### `data/v3_verification/page_verification_report.json`
Per-page perceptual hash verification results from `verify_song_pages.py`. Records hash distances between extracted song pages and source book pages, flagging any above the 15-unit threshold.

### `data/v3_verification/v3_verification_report.json`
Master verification summary. Stats: 343 books checked, 342 clean, 438 input PDFs in S3, 2,058 artifacts, 8,002 output songs, zero size/page mismatches. The definitive quality report.

### `data/v3_verification/v3_verification_report.txt`
Text version of the verification report for quick terminal viewing.

### `data/v3_verification/inspect/`
Side-by-side comparison JPGs from `inspect_mismatches.py` for the small number of flagged page mismatches. Each pair shows `{book}_{song}_source.jpg` and `{book}_{song}_song.jpg` for visual confirmation.

---

## Documentation — `docs/`

### `docs/v3-pipeline-design.md`
Comprehensive v3 architecture document. Covers the migration from v2 (book_id-based paths) to v3 (human-readable `v3/{Artist}/{Book}/` paths). Maps all data locations, describes the 6-artifact system, DynamoDB v3 schema, and v3 storage principles.

### `docs/COMPLETE_DATA_MODEL.md`
Full data model documentation covering all JSON artifact schemas, DynamoDB table structure, S3 path conventions, and the relationships between data stores.

### `docs/PIPELINE_LEARNINGS_2026-02-05.md`
Lessons learned from the v3 batch processing runs (Feb 9, 2026). Covers: optimal concurrency settings, SSO token expiration gotchas, disk space management, Bedrock throttling behavior, and retry strategies.

### `docs/PROJECT_CHECKPOINT_2026-02-05.md`
Project state snapshot as of February 5, 2026. Captured during the v3 pipeline development phase.

### `docs/PROJECT_CHECKPOINT_2026-02-08.md`
Project state snapshot as of February 8, 2026. Captured just before the batch processing runs.

### `docs/operations/BATCH_PROCESSING_README.md`
Guide for running batch processing: how to use `run_v3_batch.py`, concurrency settings (4 books × 6 workers), SSO token refresh, monitoring progress, and handling failures.

### `docs/operations/BOOK_REVIEW_README.md`
Guide for reviewing processed books: generating reports, identifying extraction failures (FEW_SONGS, LOW_EXTRACTION_RATE, ARTIST_MISMATCH), and the reprocessing workflow.

### `docs/design/CORRECT_ALGORITHM.md`
Algorithm design document explaining why the ±3 page search approach fails and why systematic page-by-page vision verification is required. Documents the two-phase approach: (1) pre-render all pages to PNG, (2) use vision AI to find each song sequentially.

### `docs/design/PNG_PRERENDER_IMPLEMENTATION.md`
Design document for the page pre-rendering optimization. Covers DPI selection (200), format choice (JPG 85%), caching strategy, and the `S:/SlowImageCache/` storage architecture.

---

## Tests — `tests/`

### `tests/__init__.py`
Package init. Empty.

### `tests/unit/test_sanitization.py`
Tests for `app/utils/sanitization.py`. Validates: Windows-invalid character removal (`<>:"/\|?*`), control character stripping, Unicode NFC normalization, length limiting (200 chars), leading/trailing whitespace and dot handling, output path format compliance.

### `tests/unit/test_toc_parser.py`
Tests for `app/services/toc_parser.py`. Exercises all 5 regex patterns: Pattern 1 (dots), Pattern 2 (page-first), Pattern 3 (parentheses artist), Pattern 4 (hyphen artist), Pattern 5 (spaces). Verifies correct title/page/artist extraction.

### `tests/unit/test_toc_discovery.py`
Tests for `app/services/toc_discovery.py`. Verifies TOC page identification scoring, consecutive page selection logic, and text extraction handling.

### `tests/unit/test_artist_resolution.py`
Tests for `app/utils/artist_resolution.py`. Covers Various Artists detection, artist normalization, featuring notation handling, and per-song artist extraction from TOC lines.

### `tests/unit/test_dynamodb_ledger.py`
Tests for `app/utils/dynamodb_ledger.py`. Verifies book ID generation, idempotency checks, processing state transitions, and per-step tracking. Uses `MockDynamoDB`.

### `tests/unit/test_error_handling.py`
Tests for `app/utils/error_handling.py`. Covers retry with backoff behavior, graceful degradation fallback, error aggregation, and AWS throttling handling.

### `tests/unit/test_models.py`
Tests for `app/models.py`. Verifies dataclass construction, JSON serialization/deserialization, and field validation for all model types.

### `tests/unit/test_quality_gates.py`
Tests for `app/services/quality_gates.py`. Verifies threshold enforcement, bypass conditions (short books), partial output support, and gate aggregation logic.

### `tests/unit/test_s3_utils.py`
Tests for `app/utils/s3_utils.py`. Covers S3 operations, local mode fallback, PDF listing, and file upload/download.

### `tests/fixtures/test_5_known_errors.txt`
Text fixture listing 5 known error cases used for regression testing in `test_known_errors.py`.

### `tests/fixtures/test-james-taylor-fire-and-rain.pdf`
Sample PDF fixture used for integration testing of the PDF splitting pipeline.

---

## Root-Level Files

### `Dockerfile`
Python 3.12-slim container for ECS tasks. Installs system dependencies: `poppler-utils` (PDF rendering), `qpdf` (PDF manipulation), `libgl1` + `libglib2.0-0` (image processing). Sets `PYTHONPATH=/app` and installs pip requirements.

### `requirements.txt`
Python dependencies: `boto3` (AWS SDK), `PyMuPDF` (PDF manipulation), `Pillow` (image processing), `numpy` (numerical). Testing: `pytest`, `pytest-cov`, `hypothesis`. Development: `black`, `flake8`, `mypy`.

### `songbook-splitter.code-workspace`
VS Code workspace adding two folders: project root (`.`) and the remote image cache at `S:/SlowImageCache` for browsing pre-rendered page images.

### `README.md`
Project overview. Documents the 6-stage AWS pipeline, infrastructure, deployment procedures, and cost estimates (~$0.045/book). Shows 96.4% completion (note: this is outdated — actual completion is 100% at 342 books).

### `START_HERE.md`
Bootstrap document. Emphasizes using `py` not `python`. Links to status files, describes 342 verified books / 8,045 songs, and documents the v3 storage layout.

### `PROJECT_CONTEXT.md`
High-level project context. Describes the AWS serverless architecture, v3 DynamoDB schema, and the key learning that TOC page numbers are printed pages not PDF indices.

### `OPERATOR_RUNBOOK.md`
Operations guide with morning/weekly checklists, CloudWatch monitoring procedures, DynamoDB queries, cost tracking, troubleshooting steps, and AWS resource identifiers (region us-east-1, account 227027150061). Partially outdated — references v2 operations.

### `PROJECT_CHECKPOINT_2026-02-13.md`
Today's comprehensive workspace inventory. Lists all files with purpose and status. Preceded the archive cleanup.

### `copy_to_mobilesheets.py`
Copies extracted song PDFs from output directories to Google Drive (`G:\My Drive\SheetMusicMobileSheets`) preserving artist/album structure. Generates semicolon-separated CSV for MobileSheets batch import with title, artist, album, collection, and file path fields.

### `generate_mobilesheets_csv.py`
Standalone CSV generator. Scans local folder structures and creates MobileSheets-compatible import files. Extracts metadata from path structure (`Artist/Songbook/Song.pdf`), categorizes Broadway/movie/soundtrack content.

### `prep_mobilesheets.py`
Advanced MobileSheets prep. Embeds PDF metadata using exiftool (writes Artist, Title, Album to PDF Author/Subject/XMP fields) before copying to Google Drive, so MobileSheets can auto-import metadata.

---

## Summary

| Directory | Files | Purpose |
|-----------|-------|---------|
| `app/` | 18 | Core pipeline application (services + utilities) |
| `lambda/` | 3 | AWS Lambda handlers for Step Functions |
| `ecs/` | 1 | ECS Fargate task entry point |
| `infra/` | 6 | CloudFormation + Step Functions definitions |
| `scripts/` | 46 | Pipeline runners, verification, fixes, deployment |
| `web/` | 4 | Dashboard, editors, and viewers |
| `data/` | 8 | V3 verification reports and inspection images |
| `docs/` | 9 | Architecture, operations, and design docs |
| `tests/` | 12 | Unit tests and fixtures |
| Root | 10 | Config, README, MobileSheets utilities |
| **Total** | **117** | |
