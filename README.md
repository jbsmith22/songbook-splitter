# SheetMusic Book Splitter

**Status**: ✅ **PRODUCTION COMPLETE** | 342 books processed, 9,055 songs extracted, MobileSheets import ready

An intelligent sheet music processing pipeline that automatically splits compilation books into individual song PDFs using AWS Bedrock vision AI, OCR analysis, and automated boundary detection.

## Quick Stats (February 2026)

### ✅ Processing Complete
- **342 books** processed across **121 artists**
- **9,055 songs** extracted and verified
- **Zero metadata mismatches** after comprehensive verification
- **77 absorbed songs** recovered through boundary review tools
- **100% coverage** - all source books processed

### Data Locations
- **Input**: `SheetMusic_Input/` - Original PDF books (master copies)
- **Output**: `SheetMusic_Output/` - Individual song PDFs
- **Artifacts**: `SheetMusic_Artifacts/` - Processing metadata (6 artifacts per book)
- **Import**: `SheetMusic_ForImport/` - Organized for MobileSheets import
- **S3 Storage**: All data backed up to AWS S3 (v3/ prefix structure)
- **DynamoDB**: `jsmith-pipeline-ledger` - 342 processing records

---

## Architecture

### V3 Pipeline (Local Processing)

```
Input PDF → [6-Stage Pipeline] → Individual Song PDFs + Metadata
             ├─ TOC Discovery (Bedrock Vision AI)
             ├─ TOC Parser (Bedrock structured output)
             ├─ Holistic Page Analysis (6 parallel workers)
             ├─ Page Mapping (offset detection)
             ├─ Boundary Verification (visual review tools)
             └─ PDF Splitter (per-song extraction)
```

### Processing Stages

1. **TOC Discovery** - Identify table of contents pages using Bedrock vision
2. **TOC Parser** - Extract song titles and page numbers with AI
3. **Holistic Page Analysis** - Classify every page (song start, continuation, TOC, etc.) using vision AI
4. **Page Mapping** - Detect page offset and map TOC references to actual pages
5. **Boundary Verification** - Visual tools to review and fix song boundaries
6. **PDF Splitting** - Extract individual song PDFs with metadata

### Key Features
- **Vision AI**: AWS Bedrock Claude for page classification and TOC extraction
- **Parallel Processing**: 6 concurrent Bedrock workers per book
- **Boundary Review**: Interactive web viewer for fixing absorbed songs
- **Arrangement Detection**: Auto-detects Guitar Tab, Solo, Piano Solo versions
- **Duplicate Handling**: Smart arrangement numbering (Arr 2, Arr 3, etc.)
- **Unicode Support**: Handles special characters in titles and artists
- **Web Viewers**: Dynamic HTML tools for verification and editing

---

## Project Structure

```
├── app/                          # Core application code
│   ├── services/                 # Processing services
│   │   ├── toc_discovery.py      # ✅ Bedrock vision TOC finder
│   │   ├── toc_parser.py         # ✅ AI-powered TOC extraction
│   │   ├── holistic_page_analyzer.py  # ✅ Vision-based page classifier
│   │   ├── page_mapper.py        # ✅ Offset detection
│   │   ├── pdf_splitter.py       # ✅ Song extraction
│   │   └── bedrock_parser.py     # ✅ Bedrock API wrapper
│   └── utils/                    # Utilities
│       ├── s3_utils.py           # S3 sync operations
│       ├── dynamodb_ledger.py    # Processing state tracking
│       ├── sanitization.py       # Filename sanitization
│       └── artist_resolution.py  # Artist name normalization
├── scripts/                      # Processing and verification scripts
│   ├── run_v3_single_book.py     # ✅ Process one book (full pipeline)
│   ├── run_v3_batch.py           # ✅ Batch processing (4 books parallel)
│   ├── verify_all_complete.py   # ✅ Comprehensive verification
│   ├── verify_boundaries.py     # ✅ Detect absorbed songs
│   ├── boundary_review_server.py # ✅ Visual boundary review tool
│   ├── regenerate_v3_index.py   # ✅ Update web index
│   ├── prerender_v3_images.py   # ✅ Generate thumbnail cache
│   └── prepare_mobilesheets_import.py  # ✅ MobileSheets export
├── web/                          # Web viewers
│   ├── v3_book_index.html        # ✅ Browse all books
│   ├── v3_provenance_viewer.html # ✅ Detailed provenance view
│   ├── editors/
│   │   ├── v3_split_editor.html  # ✅ Adjust song boundaries
│   │   └── boundary_review.html  # ✅ Review absorbed songs
├── SheetMusic_Input/             # Original PDF books (master copies)
├── SheetMusic_Output/            # Extracted songs (9,055 PDFs)
├── SheetMusic_Artifacts/         # Processing metadata (342 books)
├── SheetMusic_ForImport/         # MobileSheets import structure
└── data/v3_verification/         # Verification data and reports
```

---

## Usage

### Process a Single Book

```bash
python scripts/run_v3_single_book.py --artist "Billy Joel" --book "My Lives"
```

Options:
- `--dry-run` - Show what would be processed without executing
- `--force-step <name>` - Force re-run a specific step (cascades downstream)
- `--concurrency <N>` - Number of parallel workers (default: 6)

### Batch Processing

```bash
# Process all unprocessed books (4 at a time)
python scripts/run_v3_batch.py --all

# Process specific books
python scripts/run_v3_batch.py --artist "Beatles" --parallel 4
```

### Verify Data Integrity

```bash
# Comprehensive verification (checks all metadata cross-references)
python scripts/verify_all_complete.py

# Check for absorbed songs (boundary issues)
python scripts/verify_boundaries.py

# Output: categorized_issues.json with detailed findings
```

### Review and Fix Boundaries

```bash
# Start visual boundary review tool
python scripts/boundary_review_server.py

# Opens http://localhost:8000/editors/boundary_review.html
# - Shows input PDF thumbnails vs extracted songs side-by-side
# - Highlights absorbed songs with orange "!" markers
# - Export corrections to apply to verified_songs.json
```

### Generate MobileSheets Import Structure

```bash
# Creates SheetMusic_ForImport/ with organized structure
python scripts/prepare_mobilesheets_import.py

# Output structure: <Artist>/<Book>/<Song>.pdf
# - Automatic arrangement detection (Guitar Tab, Solo, etc.)
# - Smart duplicate numbering (Yesterday - Arr 2, etc.)
# - Handles Various Artists books correctly
```

---

## Web Tools

### Book Index Viewer
- **URL**: `file:///web/v3_book_index.html`
- Browse all 342 books with stats and thumbnails
- Filter by artist, search by title
- Direct links to provenance and split editor

### Provenance Viewer
- **URL**: `file:///web/v3_provenance_viewer.html?artist=X&book=Y`
- Detailed view of processing results
- All 6 artifacts visualized
- Song list with page ranges and verification status

### Split Editor
- **URL**: `file:///web/editors/v3_split_editor.html?artist=X&book=Y`
- Interactive song boundary adjustment
- PDF thumbnail strips with page-level metadata
- Export corrected boundaries to JSON

### Boundary Review
- **URL**: `file:///web/editors/boundary_review.html`
- Review 40 books with absorbed songs
- Parallel view: input PDF vs extracted songs
- Identify missing songs and over-long splits

---

## Data Architecture

### V3 Storage Layout

| Type | Local Path | S3 Path |
|------|-----------|---------|
| **Input** | `SheetMusic_Input/{Artist}/{Artist} - {Book}.pdf` | `s3://jsmith-input/v3/{Artist}/...` |
| **Output** | `SheetMusic_Output/{Artist}/{Book}/{Artist} - {Song}.pdf` | `s3://jsmith-output/v3/{Artist}/{Book}/...` |
| **Artifacts** | `SheetMusic_Artifacts/{Artist}/{Book}/*.json` | `s3://jsmith-artifacts/v3/{Artist}/{Book}/...` |

### Artifacts (6 per book)

1. **toc_discovery.json** - TOC pages found by Bedrock vision
2. **toc_parse.json** - Song titles and page numbers extracted
3. **page_analysis.json** - Per-page classification results
4. **page_mapping.json** - Page offset and song assignments
5. **verified_songs.json** - Final song boundaries and metadata
6. **output_files.json** - Generated PDF file paths and sizes

### DynamoDB Schema

Table: `jsmith-pipeline-ledger`

```json
{
  "book_id": "594e8e0eb2c37bd0",
  "artist": "Billy Joel",
  "book_name": "My Lives",
  "status": "completed",
  "steps": {
    "toc_discovery": {"status": "completed", "timestamp": "..."},
    "toc_parse": {"status": "completed", "timestamp": "..."},
    "page_analysis": {"status": "completed", "timestamp": "..."},
    "page_mapping": {"status": "completed", "timestamp": "..."},
    "pdf_splitter": {"status": "completed", "timestamp": "..."}
  },
  "total_songs": 70,
  "total_pages": 430,
  "processing_time": 1182.9
}
```

---

## Processing Statistics

### Performance (Billy Joel - My Lives Example)
- **430 pages** → **70 songs**
- **TOC Discovery**: 85s (vision analysis)
- **TOC Parser**: 20.5s (AI extraction)
- **Page Analysis**: 1,152.9s (6 parallel workers, 19.3 min)
- **PDF Splitter**: 9.5s
- **Total**: 19.7 minutes

### Batch Processing (Feb 9, 2026)
- **Run 1**: 80 books in ~80 min (SSO token expiration)
- **Run 2**: 229 books in 4.7 hrs (all successful)
- **Config**: 4 parallel books × 6 workers = 24 concurrent Bedrock calls
- **Median time**: ~4 min/book
- **Throttling ceiling**: ~50 concurrent API calls

### Boundary Fixes Applied
- **25 books** required boundary corrections
- **77 absorbed songs** recovered using boundary review viewer
- **Method**: Visual review of input vs output thumbnail strips
- **Result**: Zero metadata mismatches after fixes

---

## AWS Resources

### S3 Buckets
- `jsmith-input` - Source PDF books (v3/ prefix)
- `jsmith-output` - Extracted song PDFs (v3/ prefix)
- `jsmith-artifacts` - Processing metadata (v3/ prefix)

### DynamoDB
- `jsmith-pipeline-ledger` - V3 processing records (342 books)
- `jsmith-processing-ledger` - V2 legacy records (1,249 books, preserved)

### Cost Analysis
- **Per book**: ~$0.45 (mostly Bedrock vision API calls)
- **342 books**: ~$154 total
- **Bedrock**: $0.40/book (400 page classifications × $0.001/image)
- **S3/DynamoDB**: $0.05/book (storage + operations)

---

## MobileSheets Import

### Folder Structure
```
SheetMusic_ForImport/
├── Beatles/
│   ├── 100 Hits For All Keyboards/
│   │   ├── Yesterday.pdf
│   │   ├── Eleanor Rigby.pdf
│   │   └── ...
│   ├── Revolver _guitar Tab_/
│   │   ├── Eleanor Rigby - Guitar Tab.pdf
│   │   └── ...
│   └── All Songs 1962-1974/
│       ├── Yesterday - Arr 2.pdf
│       ├── Eleanor Rigby - Arr 2.pdf
│       └── ...
└── Various Artists/
    └── Classic Rock 73 Songs/
        ├── Dream On.pdf  (by Aerosmith)
        ├── BABA O'RILEY.pdf  (by The Who)
        └── ...
```

### Naming Conventions
- **Single version**: `Song Title.pdf`
- **Main arrangement**: `Song Title.pdf` (first occurrence, no suffix)
- **Additional standard**: `Song Title - Arr 2.pdf`, `Arr 3.pdf`, etc.
- **Guitar Tab**: `Song Title - Guitar Tab.pdf`
- **Piano Solo**: `Song Title - Piano Solo.pdf`
- **Easy Piano**: `Song Title - Easy Piano.pdf`

### Statistics
- **9,055 songs** ready for import
- **121 artists**
- **395 books**
- **3,355 songs** with arrangement suffixes
- **100% coverage** - all source songs accounted for

---

## Known Issues & Resolutions

### ✅ Resolved
1. **Unicode Handling** - Fixed S3 key encoding for special characters
2. **Trailing Periods** - Updated sanitization to remove trailing dots
3. **Page Offset Detection** - Improved algorithm with confidence scoring
4. **Absorbed Songs** - Created boundary review tools to identify and fix
5. **Duplicate Titles** - Implemented smart arrangement numbering
6. **Various Artists** - Correctly uses song-level artist from metadata
7. **Case Sensitivity** - Added fuzzy matching for filename lookups

### Known Limitations
1. **Manual Review Required** - Some complex TOCs need human verification
2. **Bedrock Rate Limits** - Max ~50 concurrent calls before throttling
3. **SSO Token Expiration** - Batch runs >80 min need token refresh
4. **Disk Space** - Local sync requires ~15 GB for all song PDFs

---

## Development

### Requirements
- Python 3.12
- AWS CLI with SSO configured
- ~20 GB free disk space
- Bedrock access (us-east-1 region)

### Key Dependencies
```
boto3>=1.26.0          # AWS SDK
PyMuPDF>=1.24.0        # PDF manipulation
Pillow>=10.0.0         # Image processing
anthropic>=0.18.0      # Bedrock Claude API
```

### Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS SSO
aws sso login --profile default

# Verify Bedrock access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"messages":[{"role":"user","content":"test"}],"anthropic_version":"bedrock-2023-05-31","max_tokens":10}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

---

## Future Enhancements

- [ ] Cloud deployment (ECS/Step Functions for fully automated processing)
- [ ] Web dashboard for monitoring and manual review
- [ ] Support for handwritten sheet music
- [ ] Automatic key signature detection
- [ ] Chord chart extraction
- [ ] Integration with music notation software (MuseScore, Finale)
- [ ] Mobile app for on-the-go access

---

## License

MIT License

## Author

Built with AWS Bedrock, Python, and lots of sheet music ♪

## Support

For issues or questions, check:
- `data/v3_verification/` for verification reports
- DynamoDB ledger for processing status
- CloudWatch logs (if using AWS)
- Web viewers for visual debugging
