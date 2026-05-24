# Songbook-Splitter Content Consolidation Plan

**Goal:** Collapse 8+ scattered locations of songbook content into a single, deduplicated, well-documented final structure on Google Drive (`G:\My Drive`). Preserve project artifacts and the pipeline restoration toolkit locally. Tear down AWS footprint.

**Status when complete:** Project is "parked" - restorable to AWS in the future, currently consuming zero cloud resources. Every PDF is in exactly one place. Every working file has known provenance.

**This document does not move files.** It defines the plan. Execution requires your approval and is done by you (or by future-you with my help) one step at a time.

---

## Part 1 — Naming Standard

All filenames in the final structure follow ONE consistent standard. The pipeline already implements much of this in `app/utils/sanitization.py`; this document codifies what gets used.

### File and folder name rules

1. **ASCII only.** No accented characters, smart quotes, ampersands, plus signs, em-dashes, en-dashes.
2. **Replacement table:**
   - `&` → `And`
   - `+` → `And`
   - `'` (curly) → `'` (straight ASCII apostrophe)
   - `"` (curly) → omit entirely (don't replace with regular quote)
   - `–`, `—` (en-dash, em-dash) → `-`
   - `…` → omit
   - Diacritics (é, ü, ñ, etc.) → unaccented Latin equivalent (e, u, n)
   - Non-Latin characters → omit
3. **Whitespace:** single spaces only. No double-spaces. No tabs. No leading/trailing whitespace.
4. **Punctuation kept:** apostrophe `'` (straight), period `.`, comma `,`, parentheses `()`, hyphen `-`, brackets `[]` (only for arrangement tags).
5. **Punctuation removed:** `:`, `;`, `?`, `!`, `<`, `>`, `/`, `\`, `|`, `*`, `"`.
6. **Case:** Title Case. First letter of each word capitalized. Articles (`a`, `an`, `the`, `and`, `or`, `but`, `in`, `on`, `at`, `to`, `for`, `of`, `with`) stay lowercase EXCEPT at start of name. Roman numerals (II, III, IV, V) stay uppercase. Common acronyms (USA, UK, AM, PM, NYC) stay uppercase.
7. **Length:** max 200 characters.
8. **No leading/trailing dots or spaces** (Windows filesystem rule).

### Songbook PDF filename format

`<Artist> - <Book Title>.pdf`

- Examples:
  - `Billy Joel - Greatest Hits Vol I and II.pdf` (not "Vol I And II" — "and" is lowercase article)
  - `Billy Joel - Fantasies and Delusions.pdf` (not "Fantasies & Delusions")
  - `Various Artists - Best of 80s Rock.pdf` (not "Best Of 80s Rock")

### Split song PDF filename format

For single-artist books: `<Artist> - <Song Title>.pdf`

For Various Artists books: `<Performing Artist> - <Song Title>.pdf` (where Performing Artist is the actual song's artist, not "Various Artists")

- Examples:
  - `Billy Joel - Piano Man.pdf`
  - `Heart - Barracuda.pdf` (inside "Various Artists - Classic Rock 73 Songs/")

### Arrangement suffixes

When multiple arrangements of the same song exist within a book or artist, suffixes follow this order:

- First/primary version: no suffix → `Billy Joel - Piano Man.pdf`
- Second version: `Arr 2` → `Billy Joel - Piano Man - Arr 2.pdf`
- Third version: `Arr 3` → `Billy Joel - Piano Man - Arr 3.pdf`
- Special variants use named suffixes:
  - `Guitar Tab` → `Beatles - Yesterday - Guitar Tab.pdf`
  - `Piano Solo` → `Billy Joel - Piano Man - Piano Solo.pdf`
  - `Easy Piano` → `Beatles - Let It Be - Easy Piano.pdf`
  - `Score` → `Cheap Trick - Greatest Hits - Score.pdf`
  - `Lead Sheet` → `Billy Joel - Honesty - Lead Sheet.pdf`
  - `SATB` → `Beatles - Lullaby - SATB.pdf` (vocal arrangement)

Suffix ordering when multiple apply: `Artist - Title - Variant - Arr N.pdf`

### Folder name format

- Artist folders: `Billy Joel`, `Beatles`, `Various Artists` (Title Case, no underscores)
- Category folders: prefixed with underscore for sort-ordering at top of artist list: `_Broadway Shows`, `_Christmas Music`, etc.
- Book subfolders (under artist): book title only, without artist prefix → `My Lives` (not "Billy Joel - My Lives")
- Inside an artist folder, sheets-only collection: `_Sheets` (with underscore prefix, sorts to top among book subfolders)

---

## Part 2 — Target Final Structure

### On Google Drive (`G:\My Drive\Sheet Music\`)

```
G:\My Drive\Sheet Music\                            [SINGLE SOURCE OF TRUTH]
│
├── Billy Joel\                                     [processed artist]
│   ├── Billy Joel - 52nd Street.pdf                (source songbook at root)
│   ├── 52nd Street\                                (split songs subfolder)
│   │   ├── Billy Joel - Big Shot.pdf
│   │   ├── Billy Joel - Honesty.pdf
│   │   └── ...
│   ├── Billy Joel - Anthology.pdf
│   ├── Anthology\
│   │   └── ...
│   ├── Billy Joel - My Lives.pdf
│   ├── My Lives\
│   │   └── ...
│   ├── ... (all 16 source songbooks + split subfolders)
│   └── _Sheets\                                    (individual downloaded sheets)
│       ├── Billy Joel - A Matter of Trust.pdf      (sheets that DIDN'T come from splits)
│       ├── Billy Joel - Lullaby (Goodnight My Angel).pdf
│       └── ...
│
├── Beatles\                                        [same pattern]
│   ├── Beatles - Abbey Road.pdf
│   ├── Abbey Road\
│   │   ├── Beatles - Come Together.pdf
│   │   └── ...
│   └── _Sheets\
│       └── ...
│
├── Bryan Adams\                                    [sheet-only artist]
│   └── _Sheets\
│       ├── Bryan Adams - Everything I Do.pdf
│       └── Bryan Adams - Heaven.pdf
│   (no source songbook, no split subfolders — nothing was processed)
│
├── Cheap Trick\                                    [score-only artist (FakeAndScores routing)]
│   └── Cheap Trick - Greatest Hits - Score.pdf
│
├── ... (all 121 processed artists + ~150 sheet-only artists)
│
├── _Broadway Shows\                                [processed compilation category]
│   ├── Various Artists - Wicked.pdf
│   ├── Wicked\
│   │   ├── Stephen Schwartz - Defying Gravity.pdf
│   │   └── ...
│   └── _Sheets\
│
├── Various Artists\                                [processed compilation category]
│   ├── Various Artists - Classic Rock 73 Songs.pdf
│   ├── Classic Rock 73 Songs\
│   │   ├── Heart - Barracuda.pdf
│   │   ├── Peter Frampton - Show Me the Way.pdf
│   │   └── ...
│   └── ... (47 processed compilation books)
│
├── _Christmas Music\                               [UNPROCESSED category — books only, no splits]
│   ├── Various Artists - The Ultimate Christmas Fake Book.pdf
│   ├── Vince Guaraldi - Charlie Brown Christmas.pdf
│   └── ... (25 books)
│
├── _Classical\                                     [UNPROCESSED — books only]
│   ├── Beethoven - Complete Piano Sonatas.pdf
│   └── ... (3 books)
│
├── _Religious\                                     [UNPROCESSED — books only]
│   ├── Hal Leonard - The Hymn Fake Book.pdf
│   └── ... (11 books)
│
├── _Traditional\                                   [UNPROCESSED — books only]
│   └── ... (4 books)
│
├── _Fake Books\                                    [UNPROCESSED — fake books, kept separate]
│   ├── Various Artists - Real Book 5th Edition C.pdf
│   ├── Various Artists - Ultimate Fake Book C Edition.pdf
│   └── ... (24 books)
│
├── _Instructional and Theory\                      [UNPROCESSED — reference texts]
│   ├── Berklee Instant Keyboard.pdf
│   ├── How To Play Piano.pdf
│   └── ... (~60 files)
│
└── _Movie and TV\                                  [processed category, same pattern as artist]
    └── ... (with splits)
```

**Total content estimate after consolidation:** ~30 GB of unique PDFs on Google Drive (down from ~150+ GB across all sources due to deduplication). Local additions to `S:\aiwork\songbook-splitter\` add ~30 GB for the V1/V2/V3 page caches + ~1 GB for the new restoration kit + ~5 GB for snapshots = **~36 GB new local footprint** on top of the existing ~46 MB project code.

### MobileSheets handling (item 2 from your answers)

MobileSheets reads PDFs from a configured folder structure and uses `Artist`, `Title`, `Album` metadata. Two options:

**Option A (preferred): Point MobileSheets at the consolidated structure directly.** Test whether MobileSheets handles `<Artist> - <Title>.pdf` filenames inside `Artist\Book\` folders correctly. If yes, no second copy needed. The `prep_mobilesheets.py` script in the project embeds PDF metadata (Author/Subject/XMP) so MobileSheets can auto-import — that's the recommended approach. Run it once over the consolidated structure to embed metadata. No naming changes needed.

**Option B (fallback if Option A fails):** Maintain a parallel `G:\My Drive\_MobileSheets\` directory with the ForImport naming (no artist prefix, with arrangement numbers). Generated from the consolidated structure by a script. Pros: matches MobileSheets convention. Cons: 2× disk space, sync burden.

**Recommendation:** Try Option A first. The `prep_mobilesheets.py` route embeds metadata into the PDF files themselves and MobileSheets reads from those fields, not the filename. If that works (very likely), no duplicate hierarchy needed.

### On local disk — inside `S:\aiwork\songbook-splitter\`

The project already lives at `S:\aiwork\songbook-splitter\` after the May 2026 migration. Pipeline artifacts, page caches, AWS restoration material, and legacy snapshots all live as subfolders alongside the project's existing code/docs.

```
S:\aiwork\songbook-splitter\                       [project root - already exists]
│
│  [EXISTING — code and docs already here]
├── app\                                            (pipeline application code)
├── scripts\                                        (orchestration, verification, fixes)
├── web\                                            (dashboard and editors)
├── infra\                                          (CloudFormation, Step Functions JSON)
├── ecs\ lambda\ tests\ docs\                       (deployment + test code)
├── data\                                           (existing DynamoDB backup + v3 verification reports)
├── README.md, START_HERE.md, FILE_REFERENCE.md, etc.
│
│  [NEW — added during consolidation]
├── AWS_Restoration\                                [everything needed to put it back into AWS]
│   ├── dynamodb_backup_jsmith-pipeline-ledger_<latest-date>.json   (current snapshot)
│   ├── dynamodb_backup_jsmith-processing-ledger_<date>.json   (V2 legacy table)
│   ├── cfn-outputs.json                            (CloudFormation stack outputs at teardown)
│   ├── ecr-images.json                             (Docker image manifest)
│   ├── AWS_RESOURCES.md                            (NEW: account ID, region, ARNs, bucket names)
│   └── RESTORATION_PROCEDURE.md                    (NEW: step-by-step rebuild guide)
│
├── Pipeline_Artifacts\                             [the V3 metadata - 6 JSON files per book]
│   ├── _README.md                                  (explains the 6 files: toc_discovery, toc_parse, page_analysis, page_mapping, verified_songs, output_files)
│   ├── Billy Joel\
│   │   ├── My Lives\
│   │   │   ├── toc_discovery.json
│   │   │   ├── toc_parse.json
│   │   │   ├── page_analysis.json
│   │   │   ├── page_mapping.json
│   │   │   ├── verified_songs.json
│   │   │   └── output_files.json
│   │   └── ... (16 books for Billy Joel)
│   └── ... (343 books × 6 artifacts each = 2,058 JSON files)
│
├── Pipeline_Reports\                               [verification/processing reports]
│   ├── v3_verification_report.json                 (master quality report)
│   ├── v3_verification_report.txt
│   ├── categorized_issues.json                     (99 absorbed songs, etc.)
│   ├── boundary_verification_report.json
│   ├── overlap_analysis_results.json
│   ├── page_verification_report.json
│   ├── song_inventory.csv                          (complete song list)
│   └── inspect\                                    (manual review JPGs)
│
├── Pipeline_PageCache\                             [pre-rendered page JPGs for verification scripts]
│   ├── _README.md                                  (regen procedure via prerender_v3_images.py)
│   ├── v1\                                         (experimental V1 cache - 34 artists, partial)
│   │   └── <Artist>\<Book>\<Song>_page_N.jpg       (V1 naming: per-song)
│   ├── v2\                                         (V2 production cache - 121 artists, 17 Billy Joel books inc Rock Score)
│   │   └── <Artist>\<Book>\page_NNNN.jpg
│   └── v3\                                         (V3 production cache - 111 artists, current canonical)
│       └── <Artist>\<Book>\page_NNNN.jpg           (200 DPI, JPG q85, ~14 GB total)
│
└── Legacy_Snapshots\                               [point-in-time recovery + V1/V2 historical material]
    ├── _README.md
    ├── 2026-02-15-archive.zip                      (the 224MB Feb-15 snapshot)
    ├── 2026-02-15-archive-manifest.txt
    ├── 2026-02-15-archive-README.md
    ├── working-archive-2026-Q1.zip                 (zipped current archive/ folder)
    ├── Pre-V3-Documentation\                       (V1 Claude-based pipeline docs)
    ├── Pre-V3-Scripts\                             (batch_convert_for_claude*.py etc.)
    ├── Pre-V3-Manifests\                           (V1 _manifest.json files by artist)
    └── V2-ProcessedSongs-Unique\                   (V2 splits not in V3, after audit)
```

The page cache stays accessible to existing scripts. Two implementation options for the cache move:

**Option 1: Physical move + script updates.** Move `S:\SlowImageCache\pdf_verification*\` to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v[123]\`. Update the ~6 scripts that reference the old path (`verify_song_pages.py`, `inspect_mismatches.py`, `fix_overlaps_with_vision.py`, `prerender_v3_images.py`, `monitor_prerender_progress.py`, `boundary_review_server.py`) and the `songbook-splitter.code-workspace` file.

**Option 2: Move + symlink.** Move the caches to the new location, then leave a junction at `S:\SlowImageCache\` pointing to `S:\aiwork\songbook-splitter\Pipeline_PageCache\` so old scripts keep working unmodified. Cleaner for ops but the symlink is "magic" that future-you needs to remember.

Recommend Option 2 — less invasive, preserves working scripts.

---

## Part 3 — Complete File Lineage

Every PDF currently exists in one or more locations. Here's where each consolidates to.

### Source songbook PDFs (pre-split)

| Current location | Disposition | Notes |
|---|---|---|
| `D:\Work\songbook-splitter\SheetMusic_Input\<Artist>\<Book>.pdf` | DELETE after consolidation | Local working copy, sanitized names |
| `G:\My Drive\SheetMusic_Input\<Artist>\<Book>.pdf` | DELETE after consolidation | Cloud sync of local working copy (same as above) |
| `G:\My Drive\Sheet Music\<Artist>\Books\<Book>.pdf` | RENAME to canonical → MOVE to `G:\My Drive\Sheet Music\<Artist>\<Book>.pdf` | Currently uses original quirky names |
| `G:\My Drive\SheetMusic\<Artist>\Books\<Book>.pdf` | DELETE | Old V1 mirror |
| `D:\Work\Archive_Deletable\SheetMusic\<Artist>\<Book>.pdf` | DELETE | Duplicate of Input |
| `C:\Work\AWSMusic\SheetMusic\<Artist>\<Book>.pdf` | AUDIT for unique content, then DELETE | Has Rock Score and 2-3 others not in current Input |

**Consolidation rule:** The canonical source PDF lives at `G:\My Drive\Sheet Music\<Artist>\<Artist> - <Book>.pdf` after renaming to standard. All other copies are removed.

### Split song PDFs (post-pipeline)

| Current location | Disposition | Notes |
|---|---|---|
| `D:\Work\songbook-splitter\SheetMusic_Output\<Artist>\<Book>\<Song>.pdf` | MOVE to `G:\My Drive\Sheet Music\<Artist>\<Book>\<Song>.pdf` | Primary split output |
| `D:\Work\songbook-splitter\SheetMusic_ForImport\<Artist>\<Book>\<Song>.pdf` | DELETE (if MobileSheets Option A works) OR keep in separate location | Different naming, possible MobileSheets fallback |
| `G:\My Drive\SheetMusic_Output\<Artist>\<Book>\<Song>.pdf` | DELETE | Cloud sync of local Output |
| `G:\My Drive\SheetMusic_ForImport\<Artist>\<Book>\<Song>.pdf` | DELETE (or move to _MobileSheets if Option B) | Cloud sync of local ForImport |
| `D:\Work\Archive_Deletable\ProcessedSongs\<Artist>\` | DELETE | Empty stubs |
| `D:\Work\Archive_Deletable\ProcessedSongs_Final\<Artist>\<Song>.pdf` | AUDIT for unique songs not in V3, then DELETE | V2 pipeline output, has dupes with diff sizes |
| `D:\Work\Archive_Deletable\ProcessedSongs_Archive\<Artist>\<Book>\<Song>.pdf` | AUDIT for unique songs, then DELETE | V2 pipeline output with `-2` duplicates |
| `C:\Work\AWSMusic\ProcessedSongs\<Artist>\<Song>.pdf` | AUDIT for unique songs, then DELETE | V1 pipeline output, has unique songs (e.g., Billy Joel - Scenes from an Italian Restaurant) |

**Consolidation rule:** The canonical split PDF lives at `G:\My Drive\Sheet Music\<Artist>\<Book>\<Artist> - <Song>.pdf` after renaming to standard. Duplicates and V1/V2 outputs reviewed for content not in V3, then removed.

### Individual sheets (downloaded singles, never went through pipeline)

| Current location | Disposition | Notes |
|---|---|---|
| `G:\My Drive\Sheet Music\<Artist>\Sheets\<Song>.pdf` | RENAME to canonical → MOVE to `G:\My Drive\Sheet Music\<Artist>\_Sheets\<Artist> - <Song>.pdf` | Original master sheets collection |
| `G:\My Drive\SheetMusic\<Artist>\Sheets\<Song>.pdf` | DELETE if duplicate of master, OTHERWISE move to `_Sheets\` | Old mirror |

**Deduplication rule:** When two files have the same target name, compare byte sizes. If identical → keep one, delete other. If different → keep both with version suffix: `Billy Joel - Piano Man.pdf` and `Billy Joel - Piano Man - V2.pdf`. Use higher-quality (larger file size) as the unsuffixed primary.

**Cross-source deduplication rule:** A `_Sheets/` entry that EXACTLY matches a song already in a split subfolder is a candidate for removal — but only if the file sizes are identical. Different sizes → both kept (different arrangements/scans). The _Sheets folder is for content that didn't come from songbook splits, and most overlap should be near-duplicates from different sources.

### FakeAndScores content

| Current location | Disposition |
|---|---|
| `D:\Work\songbook-splitter\SheetMusic_FakeAndScores\_Fake Books\*.pdf` | MOVE to `G:\My Drive\Sheet Music\_Fake Books\<Book>.pdf` (rename to standard) |
| `D:\Work\songbook-splitter\SheetMusic_FakeAndScores\<Artist>\<Book> [Score].pdf` | MOVE to `G:\My Drive\Sheet Music\<Artist>\<Artist> - <Book> - Score.pdf` |
| `G:\My Drive\SheetMusic_FakeAndScores\` | DELETE (cloud sync of local) |

### V3 Pipeline metadata (the 6 JSON files per book)

| Current location | Disposition |
|---|---|
| `D:\Work\songbook-splitter\SheetMusic_Artifacts\<Artist>\<Book>\*.json` | MOVE to `S:\aiwork\songbook-splitter\Pipeline_Artifacts\<Artist>\<Book>\*.json` |
| `D:\Work\songbook-splitter\SheetMusic_Artifacts\batch_results_*.json` | MOVE to `S:\aiwork\songbook-splitter\Pipeline_Reports\` |

### Pre-rendered page image cache (S:\SlowImageCache)

The page caches were generated by `scripts/prerender_v3_images.py` using local PyMuPDF rendering (no API cost — just CPU time, ~30 min for 38K pages). They're used by `verify_song_pages.py` (perceptual hashing), `inspect_mismatches.py`, `fix_overlaps_with_vision.py`, and the `boundary_review.html` web UI. The expensive AWS Bedrock vision analysis cost (~$154 total) is captured in the artifact JSONs, NOT in these images. Caches are regenerable but slow to rebuild.

| Current location | Size | Coverage | Disposition |
|---|---|---|---|
| `S:\SlowImageCache\pdf_verification\` (V1 experimental) | small (~few hundred MB) | 34 artists, partial; abandoned per-song naming `<Song>_page_N.jpg` | MOVE to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v1\` |
| `S:\SlowImageCache\pdf_verification_v2\` (V2 production) | ~14-18 GB | 121 artists, 17 Billy Joel books (includes Rock Score not in V3); `page_NNNN.jpg` per book | MOVE to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v2\` |
| `S:\SlowImageCache\pdf_verification_v3\` (V3 current canonical) | ~14 GB | 111 artists, 16 Billy Joel books; `page_NNNN.jpg` per book at 200 DPI, JPG q85 | MOVE to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v3\` |

After move, delete the empty `S:\SlowImageCache\` parent folder.

Note: scripts in the project that reference `S:/SlowImageCache/pdf_verification_v3/` will need updating to point at `S:/Music/Pipeline_PageCache/v3/` (or vice versa — keep the old paths and put symlinks if preferred). Specific scripts to check: `verify_song_pages.py`, `inspect_mismatches.py`, `fix_overlaps_with_vision.py`, `prerender_v3_images.py`, `monitor_prerender_progress.py`, `boundary_review_server.py`. Also the VS Code workspace file `songbook-splitter.code-workspace` adds `S:/SlowImageCache` as a folder — that path needs updating too.

### Project code and config

| Current location | Disposition |
|---|---|
| `S:\aiwork\songbook-splitter\app\` | KEEP in place |
| `S:\aiwork\songbook-splitter\scripts\` | KEEP in place |
| `S:\aiwork\songbook-splitter\web\` | KEEP in place |
| `S:\aiwork\songbook-splitter\infra\` | KEEP in place — used for AWS restoration |
| `S:\aiwork\songbook-splitter\ecs\` | KEEP in place |
| `S:\aiwork\songbook-splitter\lambda\` | KEEP in place |
| `S:\aiwork\songbook-splitter\tests\` | KEEP in place |
| `S:\aiwork\songbook-splitter\docs\` | KEEP in place |
| `S:\aiwork\songbook-splitter\data\` | KEEP — contains the DynamoDB backup and verification reports |
| `S:\aiwork\songbook-splitter\.claude\`, `.git\`, etc. | KEEP in place |
| `S:\aiwork\songbook-splitter\archive\` (42 MB of stale files) | ZIP as `S:\aiwork\songbook-splitter\Legacy_Snapshots\working-archive-2026-Q1.zip` then DELETE |

### Documentation

| Current location | Disposition |
|---|---|
| Project root `README.md`, `START_HERE.md`, `PROJECT_CONTEXT.md`, `OPERATOR_RUNBOOK.md`, `FILE_REFERENCE.md`, `PROJECT_CHECKPOINT_2026-02-13.md` | KEEP in project folder |
| `D:\Work\Songbook Splitter Archive\README.md`, `RESTART_INSTRUCTIONS.md`, `archive_manifest_2026-02-15.txt` | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\` alongside the zip |
| `D:\Work\Songbook Splitter Archive\songbook-splitter-archive-minimal-2026-02-15.zip` | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\` |
| `G:\My Drive\SheetMusic\SheetMusicBookSplitter_Context.md`, `SheetMusicBookSplitter_TechnicalMethod.md`, `_SESSION_CONTINUATION_GUIDE.md`, `COMPLETE_SONGBOOK_INVENTORY.txt`, `CROSS_REFERENCE_REPORT.txt`, `processing_log.txt`, `_processing_log.txt` | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\Pre-V3-Documentation\` (these are the V1 Claude-based pipeline docs — historical interest) |
| `G:\My Drive\SheetMusic\batch_convert_for_claude.py`, `batch_convert_for_claude_v2.py` | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\Pre-V3-Scripts\` |
| `G:\My Drive\SheetMusic\_temp_images_for_claude\` (temp folder) | DELETE |
| `G:\My Drive\SheetMusic\<Artist>\Books\*_manifest.json` (V1 manifests) | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\Pre-V3-Manifests\<Artist>\` then DELETE from Drive |
| `G:\My Drive\SheetMusic\<Artist>\Books\split_from_manifest.py` (V1 splitter) | MOVE to `S:\aiwork\songbook-splitter\Legacy_Snapshots\Pre-V3-Scripts\` |

### Cleanup of Archive_Deletable

| Current location | Disposition |
|---|---|
| `D:\Work\Archive_Deletable\SheetMusic_Artifacts_v2_backup\lambda\lambda-deployment.zip` (80 MB stale lambda) | DELETE outright |
| `D:\Work\Archive_Deletable\ProcessedSongs\` (empty stubs) | DELETE |
| `D:\Work\Archive_Deletable\ProcessedSongs_Final\` (V2 splits with `nul` corruption) | AUDIT for unique songs, MOVE uniques to `S:\aiwork\songbook-splitter\Legacy_Snapshots\V2-ProcessedSongs-Unique\`, then DELETE |
| `D:\Work\Archive_Deletable\ProcessedSongs_Archive\` (V2 splits with `-2` dupes) | Same as above |
| `D:\Work\Archive_Deletable\SheetMusic\` (duplicate of current Input) | DELETE outright once Input → Drive is confirmed |

### AWS resources

| Resource | Disposition |
|---|---|
| S3 bucket `jsmith-input` | DOWNLOAD any unique content not in local, then DELETE bucket |
| S3 bucket `jsmith-output` | DOWNLOAD any unique splits not in local, then DELETE bucket |
| S3 bucket `jsmith-artifacts` | DOWNLOAD all artifacts to `S:\aiwork\songbook-splitter\Pipeline_Artifacts\` (we have local copies but verify), then DELETE bucket |
| DynamoDB `jsmith-pipeline-ledger` | Already backed up to `data\dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json` — DELETE table |
| DynamoDB `jsmith-processing-ledger` (v2 legacy) | EXPORT to `S:\aiwork\songbook-splitter\AWS_Restoration\dynamodb_backup_jsmith-processing-ledger_<date>.json` then DELETE table |
| ECR repository `jsmith-sheetmusic-splitter` | Document image tags then DELETE repository |
| CloudFormation stack `jsmith-sheetmusic-splitter` | Run `scripts/aws/cleanup.ps1` (already exists in project) |
| Lambda functions, Step Functions, ECS tasks | Cleaned up by CloudFormation stack deletion |
| CloudWatch logs | Optionally export to `S:\aiwork\songbook-splitter\AWS_Restoration\cloudwatch-logs-export.zip`, then DELETE |

---

## Part 4 — Execution Order

These phases are **independent and resumable**. Don't run one until the previous is verified clean.

### Phase 0: Preparation

1. **Build a complete file inventory** for every source location. Output: `S:\aiwork\songbook-splitter\inventory.csv` with columns: `source_path`, `size_bytes`, `sha256`, `proposed_destination`, `disposition`, `notes`. Generate this with a PowerShell script that hashes every PDF; expect ~30 minutes of I/O on the larger volumes. NOT just listing — actual SHA256s, because we need to detect content-identical files across locations.

2. **Spot-check the inventory.** Pick 5 random books, manually verify the disposition column makes sense.

3. **Create the destination skeleton** at `G:\My Drive\Sheet Music\` (empty subfolders for all artists). Don't move content yet.

4. **Create the local archive skeleton** at `S:\aiwork\songbook-splitter\` with empty subfolders matching Part 2.

5. **Test MobileSheets compatibility** before any moves. Copy 1 book (Billy Joel - My Lives + its My Lives\ split folder) to a test location in the new format. Run `prep_mobilesheets.py` to embed metadata. Open in MobileSheets and verify it imports correctly. Confirms Option A works (or proves we need Option B).

### Phase 1: Audit unique content in legacy locations

Before deleting anything in `Archive_Deletable\` or `AWSMusic\`, identify what's only there and not in current Input/Output. Output: `S:\aiwork\songbook-splitter\legacy-uniques.csv` listing every file that exists in legacy but NOT in current canonical sources, with size and proposed action.

Specifically check:
- `C:\Work\AWSMusic\SheetMusic\<Artist>\` — find PDFs not in current Input (Billy Joel - Rock Score, etc.)
- `C:\Work\AWSMusic\ProcessedSongs\<Artist>\` — find split songs whose normalized name isn't in current Output
- `D:\Work\Archive_Deletable\ProcessedSongs_Final\<Artist>\` — find songs not in current Output
- `D:\Work\Archive_Deletable\ProcessedSongs_Archive\<Artist>\` — same
- `G:\My Drive\Sheet Music\<Artist>\Sheets\` — find sheets not yet in the inventory

For each unique find, decide:
- Add to consolidated structure (if it's a song we want to keep)
- Move to `S:\aiwork\songbook-splitter\Legacy_Snapshots\` (if it's historical-interest only)
- Discard (if it's corrupted/dup with size mismatch from known-good)

### Phase 2: Build the AWS restoration package (COMPLETED 2026-05-24)

This was done before Phase 3 so we wouldn't be blocked by AWS access if anything went wrong with consolidation. Output lives at `S:\aiwork\songbook-splitter\AWS_Restoration\` (~20 MB total, ready for git commit).

**Scripts used (saved at project root):**

- `Capture-AWS-State.ps1` - main capture script (10 sections)
- `Finish-AWS-Capture.ps1` - follow-up captures (artifacts bucket, missing Lambdas, IAM roles, ECS task defs)
- `Finish-AWS-Capture-TaskDefs.ps1` - corrected ECS task definition family names (page-mapper, song-verifier, manifest-generator)
- `Cleanup-AWS-Restoration-Duplicates.ps1` - removed two failed-run timestamp sets

**Captured and verified:**

- DynamoDB: 1,249 items in jsmith-processing-ledger (V3 prod), 399 in jsmith-pipeline-ledger (V2 legacy)
- CloudFormation: 6 outputs, 29 resources all CREATE_COMPLETE
- ECR: 117 image versions, latest 2026-02-05
- S3 inventories: jsmith-input (1,051 files), jsmith-output (49,913 files), artifacts bucket (empty)
- All 6 Lambda function configurations
- All 6 ECS task definitions (toc-discovery, toc-parser, page-mapper, song-verifier, pdf-splitter, manifest-generator)
- All 4 IAM roles + 10 inline policies + 4 managed policy attachments
- VPC, all subnets, security groups
- CloudWatch log groups
- Step Functions state machine ARN (0 recent executions - project idle since Feb)

**Generated docs in AWS_Restoration/:**

- `AWS_RESOURCES.md` - resource inventory and naming conventions
- `RESTORATION_PROCEDURE.md` - step-by-step rebuild guide
- `CAPTURE_REVIEW.md` - final summary of what was captured

**Post-capture cleanup:**

- Committed to git: `git add AWS_Restoration/ Capture-AWS-State.ps1 Cleanup-AWS-Restoration-Duplicates.ps1 Finish-AWS-Capture.ps1 Finish-AWS-Capture-TaskDefs.ps1; git commit -m "Phase 2: AWS restoration package captured"`

After this commit, AWS teardown becomes safe.

This must happen BEFORE tearing down AWS, while everything is still accessible.

1. **Verify DynamoDB backup is current.** The existing `dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json` may be stale. Re-run the export:
   ```
   aws dynamodb scan --table-name jsmith-pipeline-ledger --output json > data/dynamodb_backup_jsmith-pipeline-ledger_<today>.json
   ```
2. **Export the V2 legacy DynamoDB table** if it still has data (`jsmith-processing-ledger`).
3. **Download any S3 content not already local.** Run `aws s3 sync s3://jsmith-input <local-temp-input>` and diff against current local — capture any deltas.
4. **Save CloudFormation stack outputs:** `aws cloudformation describe-stacks --stack-name jsmith-sheetmusic-splitter > S:\aiwork\songbook-splitter\AWS_Restoration\cfn-outputs.json`
5. **Save ECR image manifest:** `aws ecr describe-images --repository-name jsmith-sheetmusic-splitter > S:\aiwork\songbook-splitter\AWS_Restoration\ecr-images.json`
6. **Save Step Functions execution history sample:** capture 5 recent successful executions for reference.
7. **Write `S:\aiwork\songbook-splitter\AWS_Restoration\AWS_RESOURCES.md`** documenting:
   - AWS account ID: 227027150061
   - Region: us-east-1
   - S3 bucket names and their purposes
   - DynamoDB table names and schemas
   - IAM role ARNs needed
   - VPC, subnet, and security group IDs used (if any)
   - Bedrock model IDs used (`anthropic.claude-3-5-sonnet-20241022-v2:0`)
   - Cost estimate per restoration ($154 for original 342-book run)
8. **Write `S:\aiwork\songbook-splitter\AWS_Restoration\RESTORATION_PROCEDURE.md`** with step-by-step instructions to rebuild from scratch:
   - Prerequisite: AWS account, region, SSO configured
   - Step 1: Deploy CloudFormation stack from `infra/cloudformation_template.yaml`
   - Step 2: Build and push Docker image (`scripts/aws/deploy-docker.ps1`)
   - Step 3: Deploy Lambda functions (`scripts/aws/deploy-lambda.ps1`)
   - Step 4: Register ECS task definitions
   - Step 5: Restore DynamoDB from backup (`scripts/restore_dynamodb.py` or inline script)
   - Step 6: Upload source PDFs to S3 (sync from `G:\My Drive\Sheet Music\`)
   - Step 7: Trigger processing via Step Functions

### Phase 3: Consolidate to Google Drive

**Critical:** This is the long phase. Process ONE artist at a time, end-to-end. Verify each artist before moving to the next.

For each artist:

1. **Create artist folder** at `G:\My Drive\Sheet Music\<Artist>\` (already exists for most)
2. **Apply source songbook renames:** rename existing `Books\` content per the canonical standard, MOVE to artist root
3. **Move split subfolders** from `D:\Work\songbook-splitter\SheetMusic_Output\<Artist>\` to `G:\My Drive\Sheet Music\<Artist>\<Book>\` with renamed song files
4. **Move/dedup sheets** from `G:\My Drive\Sheet Music\<Artist>\Sheets\` to `G:\My Drive\Sheet Music\<Artist>\_Sheets\`, renaming to canonical
5. **Run `prep_mobilesheets.py`** over this artist's folder to embed PDF metadata
6. **Test MobileSheets** import for 1-2 songs from this artist
7. **Delete the OLD content** from the source locations (Books/, Sheets/, SheetMusic_Output, SheetMusic_ForImport)
8. **Log to `_CLEANUP_LOG.md`**: what was renamed, what was moved, what was deleted

After Phase 3, all 121 processed artists are consolidated. Then:

9. **Process the 7 unprocessed category folders** (Christmas Music, Classical, Religious, Traditional, Various Artists - the underscore one, Fake Books, Instructional). Just rename/move the source books — no splits.
10. **Process the 150 sheet-only artists.** Each gets just a `_Sheets\` folder with their downloaded sheets.

### Phase 4: AWS teardown

1. Confirm Phase 3 is complete and verified.
2. Confirm `S:\aiwork\songbook-splitter\AWS_Restoration\` is complete.
3. Run `scripts\aws\cleanup.ps1` — destroys CloudFormation stack, empties buckets, removes ECR.
4. Manually verify in AWS console: zero resources remaining under your account for this project.
5. Optionally: leave the AWS account itself active (in case you have other projects there).

### Phase 5: Local cleanup

1. Move `S:\aiwork\songbook-splitter\SheetMusic_Artifacts\*` to `S:\aiwork\songbook-splitter\Pipeline_Artifacts\`.
2. Move `S:\aiwork\songbook-splitter\data\v3_verification\*` to `S:\aiwork\songbook-splitter\Pipeline_Reports\`.
3. Move `S:\SlowImageCache\pdf_verification\*` to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v1\` (V1 experimental cache).
4. Move `S:\SlowImageCache\pdf_verification_v2\*` to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v2\` (V2 production cache, ~14-18 GB).
5. Move `S:\SlowImageCache\pdf_verification_v3\*` to `S:\aiwork\songbook-splitter\Pipeline_PageCache\v3\` (V3 current canonical, ~14 GB).
6. Update scripts that reference `S:/SlowImageCache/pdf_verification_v3/` to point at new location (or leave caches at `S:\SlowImageCache\` and symlink from `S:\aiwork\songbook-splitter\Pipeline_PageCache\` — simpler, decide before moving).
7. Update `songbook-splitter.code-workspace` to reference the new cache path.
8. Delete empty `S:\SlowImageCache\` parent folder once moves are done.
9. Move `D:\Work\Songbook Splitter Archive\*` to `S:\aiwork\songbook-splitter\Legacy_Snapshots\`.
10. Zip and move `S:\aiwork\songbook-splitter\archive\*` to `S:\aiwork\songbook-splitter\Legacy_Snapshots\working-archive-2026-Q1.zip`.
11. Delete `D:\Work\Archive_Deletable\` entirely after confirming Phase 1 unique-content audit is preserved.
12. Delete `C:\Work\AWSMusic\` entirely after confirming uniques are preserved.
13. Delete `D:\Work\songbook-splitter\SheetMusic_*` folders (Input, Output, ForImport, FakeAndScores, Artifacts) — content is now on G: drive or in S:\aiwork\songbook-splitter\.
14. Delete `G:\My Drive\SheetMusic_Input\`, `SheetMusic_Output\`, `SheetMusic_ForImport\`, `SheetMusic_FakeAndScores\` (these were just cloud syncs of the local working folders).
15. Delete `G:\My Drive\SheetMusic\` entirely after confirming all unique docs/scripts moved to `S:\aiwork\songbook-splitter\Legacy_Snapshots\Pre-V3-*\`.
16. Final state: `G:\My Drive\Sheet Music\` is canonical content; `S:\aiwork\songbook-splitter\` has project + restoration kit + caches.

### Phase 6: Documentation

1. Write `S:\aiwork\songbook-splitter\README.md`: top-level index of the whole archive.
2. Write `S:\aiwork\songbook-splitter\_CLEANUP_LOG.md`: complete record of every move and delete (auto-generated during Phase 3-5).
3. Write `S:\aiwork\songbook-splitter\Pipeline_Artifacts\_README.md`: explain what the 6 JSON files mean.
4. Write `S:\aiwork\songbook-splitter\Legacy_Snapshots\_README.md`: explain the V1/V2 legacy material.
5. Write `S:\aiwork\songbook-splitter\AWS_Restoration\README.md`: pointer to RESTORATION_PROCEDURE.md.
6. Update `G:\My Drive\Sheet Music\README.md` (NEW): describe the structure, naming convention, and how MobileSheets is configured.

---

## Part 5 — Risks and Open Questions

### Known risks

1. **MobileSheets compatibility unknown until tested.** Phase 0 step 5 is the gate. If Option A fails, the structure on Google Drive doesn't change — we just generate a parallel `_MobileSheets\` folder on local disk for the device to sync from.

2. **Network speed for Google Drive sync.** Moving ~30 GB through Drive desktop client is slow. Plan for hours of sync time per major batch. Consider doing the moves directly on the cloud side via Drive Web UI for large folders, then letting the client sync down.

3. **PDF metadata embedding (`prep_mobilesheets.py`) is destructive.** It writes to the PDF file directly. Test on copies before running across all 8,000+ songs. The script may fail on protected/encrypted PDFs — capture those and handle manually.

4. **Some unique content may be deeper than expected.** Phase 1's audit needs to be thorough. Specifically the `Sheets/` folders on G: drive for the 287 artists in the master library — most have content not yet in any inventory.

5. **The 2 dropped files** from earlier analysis (`Night Ranger - Best Of 2 [Jap Score]`, `Various Artists - The 60s and 70s Rock Score`): you said these were intentional drops. Confirm they should NOT be added to the new structure. If they should, they go in their respective artist folders as `<Artist> - <Title> - Score.pdf`.

### Open questions before Phase 0

1. **Article capitalization in titles** — confirm the standard. I'm proposing the common rule: lowercase articles (`a`, `an`, `the`, `and`, `or`, `but`, `in`, `on`, `at`, `to`, `for`, `of`, `with`) EXCEPT at the start of the name. So `Billy Joel - Greatest Hits Vol I and II.pdf` (lowercase "and"). If you'd rather have everything capitalized for simplicity (current pipeline behavior), say so. The pipeline as written produces `... Vol I And II.pdf` with capital "And".

2. **MobileSheets path** — the current scripts reference `G:\My Drive\SheetMusicMobileSheets\` as the destination. If we're consolidating to `G:\My Drive\Sheet Music\`, we either (a) point MobileSheets at `Sheet Music\` directly, (b) keep a separate `SheetMusicMobileSheets\` for it. Your call.

3. **Cache strategy** — Option 1 (move + update scripts) vs Option 2 (move + symlink for back-compat). Recommend Option 2.

4. **`__Blank` and `__Unsorted` folders** in `G:\My Drive\Sheet Music\` — should these be preserved (workflow folders) or deleted (cleanup)?

5. **Audit retention** — when Phase 1 finds "uniques" in legacy locations, what's the bar for "interesting enough to keep"? Old splits with the same songs but different processing artifacts? I'd default to: "if the byte content is unique and the name suggests it's a song, keep it in `S:\aiwork\songbook-splitter\Legacy_Snapshots\V2-Uniques\<Artist>\` with a manifest noting where it came from."

---

## Part 6 — Time Estimate

Rough hours, assuming 1 person doing this part-time:

- Phase 0 (Prep): 4-6 hours (most of it I/O for SHA256 inventory)
- Phase 1 (Audit): 2-3 hours
- Phase 2 (AWS restoration package): 2-3 hours
- Phase 3 (Consolidate to Drive): **12-20 hours**. Per-artist work × 121 processed artists × 5-10 min each, plus Drive sync time. The single largest phase.
- Phase 4 (AWS teardown): 30 minutes
- Phase 5 (Local cleanup): 2-3 hours
- Phase 6 (Documentation): 2-3 hours

**Total: 25-40 hours of active work, spread across 1-2 weeks.**

You can spread Phase 3 across many sessions. After Phases 0-2, each artist consolidation is independent and resumable.

---

*This plan does not move any files. Approval and execution are your decisions. I can produce scripts (with dry-run mode) for any specific phase when you're ready to execute that phase.*
