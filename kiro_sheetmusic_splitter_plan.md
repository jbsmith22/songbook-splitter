# SheetMusic Book Splitter (AWS + Kiro) – Spec-Driven Kickstart Plan

This document is designed to be pasted directly into **Amazon Kiro** to generate specs, code, infrastructure, and tests.  
Kiro is an agentic coding service built on **Amazon Bedrock** and supports **spec-driven coding**, steering files, and agent hooks. citeturn0search0turn0search5

---

## 0) Paste-this prompt for Kiro (single message)

**Copy/paste everything between the lines into Kiro:**

---

You are my principal engineer. Build an end-to-end, production-ready pipeline that splits piano/vocal/guitar songbooks (PDFs) into per-song PDFs using Table of Contents (TOC) guidance. The pipeline must “just work” across 500+ PDFs with minimal human intervention and must be debuggable.

### Hard requirements
1. Input PDFs live in an S3 bucket under: `s3://<INPUT_BUCKET>/SheetMusic/<Artist>/books/*.pdf` (flat folder).
2. Output must be written to: `s3://<OUTPUT_BUCKET>/SheetMusicOut/<ResolvedArtist>/books/<BookName>/<ResolvedArtist>-<SongTitle>.pdf`
3. Must support “Various Artists” and books where the output artist may differ per song (default to folder artist; override if TOC indicates a different artist).
4. Must prioritize TOC-driven splitting:
   - Find TOC pages (usually near front, sometimes multiple TOCs like “By Album” and “Alphabetically”).
   - Parse TOC into structured list of `{song_title, printed_page_number, optional_artist, section}`.
   - Determine mapping from printed page numbers to PDF page indices (offset can change; handle front matter and multiple numbering segments).
   - Verify song starts near predicted indices and adjust ±N pages when necessary.
5. Must handle weird fonts, mixed content, lyrics/instructions, and page numbers robustly.
6. Must provide **auditability**:
   - Save all intermediate artifacts (TOC images, TOC extracted text/blocks, model prompts/responses, page-number crops, verification evidence).
   - Produce per-book `manifest.json` with offsets, confidences, and final split ranges.
7. Must be cost-controlled: assume total run under $1,000 for ~500 PDFs is acceptable; implement guardrails and metrics.
8. Must be resumable and idempotent: reruns should skip already-completed outputs unless inputs changed.

### Preferred AWS services
- S3 for storage
- Step Functions for orchestration
- Textract for text extraction (use DetectDocumentText by default; use AnalyzeDocument with Queries only when needed)
- Bedrock (Claude) only as a *fallback parser* for TOC extraction/cleanup, not for whole-book OCR
- DynamoDB for state/ledger (optional but recommended)
- CloudWatch logs/metrics + alarms
- ECS Fargate or Lambda for compute (choose based on PDF size limits and performance)

### Implementation constraints
- Avoid manual upload/copy/paste per PDF. The pipeline must crawl S3 prefixes.
- The PDF splitting must preserve vector content if possible; if rasterization is required for a given PDF, do it only for affected pages and record it.
- Use Python 3.12, boto3, and a container-friendly PDF toolkit (PyMuPDF / poppler / qpdf) inside ECS/Lambda.
- Output filenames must be sanitized for Windows and S3 safety.

### Deliverables
1. A repo with:
   - `/infra/` IaC (CDK or Terraform) for S3, Step Functions, IAM, optional DynamoDB, and compute.
   - `/app/` Python code for the worker(s).
   - `/docs/` including an operator runbook and cost model.
   - `/tests/` unit tests + at least 1 integration test against a sample book.
2. A spec package (requirements, design, tasks) suitable for Kiro spec-driven coding.
3. A “local dry-run mode” that can run against a small set of PDFs with mocked AWS calls.

### Quality gates
- TOC extraction must be accepted only if entry count >= configurable minimum (default 10) OR the book is explicitly marked “short”.
- If TOC extraction fails, fall back to a secondary strategy:
  - detect song title pages via header-band text + music-staff detection + repeated patterns
  - still produce outputs, but mark manifest `method=fallback` and require review
- Never silently output obviously-bad splits (e.g., song length 1 page repeatedly, or >40 pages, unless verified).

### Start now
Generate:
1) requirements.md (EARS-style where helpful), 2) design.md (architecture + data flow), 3) tasks.md (phased plan with checkboxes),
then implement incrementally: first a “single-book” path, then a “batch crawler” path.

---

---

## 1) Recommended architecture

### 1.1 High-level data flow
1. **Ingest**
   - Discover PDFs under `SheetMusic/<Artist>/books/` in INPUT_BUCKET.
   - Emit one Step Functions execution per book (or batch in chunks).
2. **TOC discovery (cheap pass)**
   - Render first *N* pages to images (N default 30, configurable).
   - Run Textract DetectDocumentText on those pages only.
   - Score pages for “TOC-likeness” using text-layout heuristics (see §2).
3. **TOC parse**
   - Preferred: deterministic parser using Textract blocks + column clustering.
   - Fallback: Bedrock Claude parses Textract-extracted text/blocks into strict JSON schema.
4. **Page-number mapping**
   - For sampled TOC entries, search likely PDF pages and run Textract on *cropped footer regions* to read printed page numbers.
   - Fit an offset model (constant or piecewise).
5. **Song-start verification**
   - For each TOC entry, verify around predicted index:
     - Check staff-lines presence (simple image heuristic) AND
     - OCR a top-band crop for title and fuzzy match to TOC title.
   - Snap within ±k pages.
6. **Split + write**
   - Create page ranges by sorted start pages; split original PDF into per-song PDFs.
   - Write to OUTPUT_BUCKET and optionally sync to a local output directory.
7. **Manifest + metrics**
   - Write `manifest.json` per book, plus run-level `SUMMARY.json`.
   - Emit CloudWatch metrics: TOC success rate, average songs/book, error counts, average Textract pages processed.

### 1.2 Orchestration options
- **Step Functions Standard** recommended for long-running, resumable jobs.
- Use **ECS Fargate** for worker tasks when PDFs can be large and you need more memory/time than Lambda comfortably provides.
- Lambda is fine for orchestration and lightweight steps (listing, small parsing).

---

## 2) The “this should work” heuristics (TOC and mapping)

### 2.1 TOC candidate scoring (from Textract blocks)
A page is TOC-like if:
- It contains anchor words: “Contents”, “Table of Contents”, “Alphabetical”, “By Album”, “Index”.
- It has many lines ending in integers (page numbers).
- Line count is high, average line length is moderate, and text is mostly not lyrics (lyrics tends to be long lines).
- X-positions cluster into 2–3 columns:
  - left column: title text
  - right column: trailing page numbers
- **Exclude** pages with strong music-staff evidence when rasterized (optional fast filter):
  - many long horizontal lines in parallel bands.

### 2.2 Deterministic TOC parsing
Given Textract LINE blocks with geometry:
- Cluster lines into columns via x-min (left) and x-max (right).
- Extract candidates matching regex like:
  - `^(?P<title>.+?)\s+(?P<page>\d{1,4})$`
- Normalize title:
  - strip dots/leaders
  - collapse whitespace
  - drop “(reprise)” etc only if configured

### 2.3 When to call Bedrock Claude (fallback only)
Call Claude only when:
- deterministic parser yields < 10 entries, or
- parsed pages are inconsistent, or
- multi-section TOC requires additional structure.

Use strict JSON schema; validate output; retry once if invalid/truncated.

### 2.4 Offset mapping (printed page → PDF index)
The offset may be:
- constant across most of book, or
- piecewise (front matter roman numerals vs arabic numbers, etc.)

Algorithm:
1. Sample K entries across TOC (e.g., 10).
2. For each entry printed_page p:
   - candidate pdf_index = toc_anchor_pdf_index + (p - toc_anchor_printed_page) + guess_offset
   - search ±S pages (S e.g., 5) for footer number p via Textract on bottom crop
3. Fit either:
   - constant offset (robust median), or
   - piecewise segments if residuals show a step-change.

---

## 3) Output rules (your required layout)

### 3.1 Output location
`SheetMusicOut/<ResolvedArtist>/books/<BookName>/<ResolvedArtist>-<SongTitle>.pdf`

- BookName: derived from input PDF filename (without extension), sanitized.
- SongTitle: sanitized; keep human-readable.
- ResolvedArtist:
  - default to folder artist
  - allow override if TOC explicitly states artist per entry (for Various Artists).

### 3.2 Idempotency
Define a deterministic “book hash”:
- SHA256 of PDF bytes (or ETag/versionId if using versioned bucket)
- plus pipeline version string

Store in DynamoDB:
- partition key: `book_id = <artist>/<bookname>`
- attributes: `pdf_hash`, `status`, `manifest_s3_uri`, `updated_at`

Skip if same hash + status=COMPLETED unless `--force`.

---

## 4) Observability + debugging (non-negotiable)
You cannot fix what you cannot see.

For every book, persist:
- `_artifacts/toc/`:
  - toc page images
  - textract raw JSON for toc pages
  - parsed toc JSON
  - bedrock prompt+response (if used)
- `_artifacts/mapping/`:
  - sampled footer crops
  - textract raw JSON for footer crops
  - fitted offset model details
- `_artifacts/verify/`:
  - title-band crops for each song start
  - fuzzy match scores
- `manifest.json` at the book output root.

Emit CloudWatch structured logs + metrics:
- toc_detected (bool)
- toc_entry_count
- offset_model_type
- mapping_confidence
- songs_emitted
- average_song_pages
- errors_by_type

---

## 5) Security + IAM (do it right once)
Minimal IAM:
- Worker role:
  - read INPUT_BUCKET prefix
  - write OUTPUT_BUCKET prefix
  - invoke Textract
  - invoke Bedrock runtime
  - write logs/metrics
  - optional DynamoDB state table access
- KMS:
  - use SSE-S3 or SSE-KMS for buckets
- Do not store raw content in prompts beyond what is required (prefer Textract outputs).

Kiro includes privacy/security considerations and is built on Bedrock. citeturn0search0

---

## 6) Cost controls (stay under $1k)
- Process only first N pages to find TOC (default 30).
- For mapping, crop + OCR only footers for a sample (default 10–15 pages).
- For verification, OCR only title-band crops (cheap).
- Limit Bedrock calls to:
  - at most 2 TOC pages per book, and only if deterministic parse fails.

Textract pricing varies by API (DetectDocumentText vs AnalyzeDocument/Queries). Use DetectDocumentText by default and promote to Queries only when necessary. citeturn0search0turn0search5

(You’ll fill in exact price math in the POC using the current AWS pricing page and your average pages/book.)

---

## 7) Implementation phases (tasks.md guidance)

### Phase 1: Single-book POC (local runner + AWS calls)
- Input: one book PDF already uploaded to S3.
- Implement:
  - render first 30 pages to images
  - detect TOC pages
  - deterministic TOC parse
  - offset mapping via footer crops
  - split to per-song PDFs
  - write outputs + manifest
- Add “golden” assertions:
  - toc_entry_count >= 10
  - output_songs >= 10
  - no >40-page songs unless verified

### Phase 2: Batch orchestrator
- List all PDFs under prefix
- Start Step Functions executions
- DynamoDB state for resumability
- Concurrency controls (limit to avoid Textract throttling)

### Phase 3: Various Artists intelligence
- Extend TOC parse to capture “Artist – Title” patterns.
- Optionally:
  - if entry has no explicit artist, infer from surrounding section heading (“Billy Joel”) or from book folder.
- Add safe fallback: mark unknown artist as folder artist.

### Phase 4: Quality + operator tooling
- A “review dashboard” (simple HTML or CSV) listing:
  - books with low confidence
  - books that used fallback path
  - suspicious song length distributions

---

## 8) Repo structure template

- `README.md` (how to run)
- `infra/`
  - CDK or Terraform
  - Step Functions definition
- `app/`
  - `worker/` (ECS/Lambda handler)
  - `toc.py`, `mapping.py`, `splitter.py`, `sanitize.py`, `manifest.py`
- `tests/`
  - unit tests for parsing/mapping/sanitize
  - one integration test with a sample book
- `docs/`
  - operator runbook
  - cost model spreadsheet (optional)

---

## 9) Acceptance tests (the “it WORKS” criteria)
Per book:
- ≥ 90% of TOC entries produce a song PDF.
- ≥ 95% of produced song PDFs start on the correct page (as verified by title-band OCR match).
- No duplicate outputs overwriting each other (unique naming; collisions resolved deterministically).
Batch:
- Pipeline runs unattended across 500 PDFs.
- Failures are isolated (one bad book doesn’t kill batch).
- Re-run resumes and skips completed books.

---

## 10) Notes about Kiro usage
Kiro supports spec-driven coding and can generate requirements/design/tasks artifacts, then implement step-by-step. citeturn0search0  
AWS documentation also indicates “Amazon Q Developer CLI has been rebranded to Kiro,” and Kiro can be administered through the Kiro console. citeturn0search5

---

## 11) Fill-in placeholders (you provide in Kiro once)
- `<INPUT_BUCKET>`
- `<OUTPUT_BUCKET>`
- `<AWS_REGION>`
- `<BEDROCK_MODEL_ID>` (Claude model you’re approved to use in Bedrock)
- Concurrency limit target (start conservative: 5–10 parallel books)

---

## 12) What to ask Kiro after the first spec generation
1) “Implement Phase 1 as a single-book CLI: `python -m app.run_one --s3-uri ...`”
2) “Add a unit test for TOC parsing with a mocked Textract response.”
3) “Add Step Functions + ECS deployment and a batch runner.”
4) “Add quality gating and a summary report CSV.”

---

End of plan.
