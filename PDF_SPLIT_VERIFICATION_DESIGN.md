# PDF Split Verification System Design

## Overview

Verify that each individual split PDF file (~14,000 song PDFs across 541 books) is cleanly split with proper song boundaries.

## System Configuration

Based on actual system scan:
- **Ollama Model**: `llama3.2-vision:11b` (7.8 GB)
- **GPU**: NVIDIA GeForce RTX 3080 (10GB VRAM) - GPU acceleration enabled
- **CPU**: Intel i9-12900K (16 cores / 24 logical processors)
- **RAM**: 64 GB
- **Total PDFs**: 11,976 individual song files
- **Estimated Pages**: ~42,000 pages total (avg 3.5 pages/PDF)
- **Cache Storage**: D:\ImageCache (63 GB available) - perfect for rendered PNGs

## Performance Estimates

With GPU acceleration and parallel processing:
- **Ollama inference**: ~1-2 seconds per page (GPU accelerated)
- **Total processing time**: 
  - 8 workers: ~6-8 hours
  - 12 workers: ~4-5 hours
  - 16 workers: ~3-4 hours
- **Disk space needed**: ~6-8 GB for rendered PNGs (H: drive recommended)
- **Memory usage**: ~4-8 GB RAM (well within 64 GB capacity)

## Objectives

1. **Verify ALL individual song PDFs** (11,976 files)
2. **Check ALL pages** of each PDF (not just sampling)
3. **Start with small batches** to validate the pipeline
4. **Use Ollama with GPU acceleration** for local vision verification (no API costs)
5. **Moderate tolerance** for false positives (better to flag too much than miss issues)
6. **Output to CSV** for manual review with yes/no decisions

## Clean Split Definition

A PDF is "cleanly split" if:
- ✅ **First page**: Song title visible, first page of the song with typical first-page accoutrements
- ✅ **Remaining pages**: Only bars of music (no new song starts)
- 🔶 **Optional - End bars**: Double bar lines on last page (nice to have, but some songs may not have them)
- 🔶 **Optional - Page numbers**: Sequential page numbers (lower priority indicator)
- ⚠️ **Edge case**: Some books might have a partial next song on the last page (unlikely but possible)

## Multi-Stage Verification Pipeline

### Stage 1: Quick Heuristic Filtering

Fast checks to identify obvious problems without vision analysis:

**For each individual PDF file**:

**Checks**:
1. **Page count anomalies**: 
   - Single-page songs (might be OK, but flag for review)
   - Very long songs (>15 pages - might be multiple songs concatenated)
2. **File size anomalies**:
   - Unusually small files (<10KB - might be corrupt)
   - Unusually large files (>5MB - might be multiple songs)
3. **Title consistency**:
   - Filename vs PDF metadata title mismatch
   - Missing PDF title metadata
4. **File accessibility**:
   - Can't open PDF (corrupt file)
   - Missing file (broken reference)

**Output**: List of PDFs flagged for Stage 2 vision analysis

### Stage 2: Vision-Based Verification (Ollama)

Use local Ollama vision model to analyze **all pages** of each individual PDF:

**For each PDF file**:
1. **Render ALL pages** to PNG (300 DPI) - cached to H: drive
2. **Analyze each page** with Ollama vision model

**Vision Checks**:

**First Page Analysis**:
```
Prompt: "Look at this sheet music page. Answer these questions:
1. Is there a song title visible at the top? (YES/NO)
2. What is the song title?
3. Does this look like the first page of a song? (YES/NO)
4. Are there any signs this is a continuation page? (YES/NO)"
```

**Middle Pages Analysis** (pages 2 through N-1):
```
Prompt: "Look at this sheet music page. Answer these questions:
1. Is there a song title visible? (YES/NO)
2. Does this look like a continuation page with only music bars? (YES/NO)
3. Are there any signs a new song starts on this page? (YES/NO)
4. Is there excessive text that isn't music notation? (YES/NO)"
```

**Last Page Analysis**:
```
Prompt: "Look at this sheet music page. Answer these questions:
1. Are there end bars (double bar lines) visible? (YES/NO)
2. Does this look like the last page of a song? (YES/NO)
3. Are there any signs a new song starts on this page? (YES/NO)
4. Is there a new song title visible? (YES/NO)"
```

**Flagging Logic**:
- ❌ First page has NO title → FLAG
- ❌ First page looks like continuation → FLAG
- ❌ Any middle page has new song title → FLAG
- ❌ Any middle page has signs of new song starting → FLAG
- ❌ Last page has new song title → FLAG
- ⚠️ Last page has no end bars → WARN (optional check)
- ⚠️ Excessive non-music text on any page → WARN

### Stage 3: Statistical Analysis & Reporting

Aggregate results and generate reports:

**Metrics**:
- Total individual PDFs analyzed
- PDFs flagged for review (by reason)
- PDFs with warnings
- PDFs that passed all checks
- Books with highest error rates (aggregate by source book)
- Common error patterns

**Output Files**:
1. `verification-results-flagged.csv` - All flagged individual PDFs for manual review
2. `verification-results-warnings.csv` - Individual PDFs with warnings
3. `verification-results-by-book.csv` - Statistics aggregated by source book
4. `verification-report.md` - Human-readable summary

## Implementation Plan

### Script Structure

```
verify_pdf_splits.py
├── Stage 1: Heuristic filtering
│   ├── scan_all_individual_pdfs()      # Recursively find all PDFs
│   ├── check_page_count(pdf_path)
│   ├── check_file_size(pdf_path)
│   ├── check_metadata(pdf_path)
│   └── filter_for_vision_check()
├── Stage 2: Vision verification
│   ├── render_all_pdf_pages(pdf_path)  # Render ALL pages to D:/ImageCache/
│   ├── call_ollama_vision(image, prompt, model="llama3.2-vision:11b")
│   ├── analyze_first_page(pdf_path)
│   ├── analyze_middle_pages(pdf_path)  # Check ALL middle pages
│   ├── analyze_last_page(pdf_path)
│   ├── parse_vision_response(response)
│   └── flag_issues(pdf_path, results)
└── Stage 3: Reporting
    ├── aggregate_results()
    ├── aggregate_by_book()             # Group by source book
    ├── generate_csv_reports()
    └── generate_summary_report()
```

### Ollama Integration

**Model**: `llama3.2-vision:11b` (GPU accelerated on RTX 3080)

**Endpoint**: `http://localhost:11434` (default Ollama port)

**API Call Pattern**:
```python
import requests
import base64

def analyze_page_with_ollama(image_path: Path, prompt: str, model: str = "llama3.2-vision:11b") -> dict:
    """Call Ollama vision API with rendered page image."""
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    # Call Ollama API (GPU accelerated)
    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': model,
            'prompt': prompt,
            'images': [image_base64],
            'stream': False
        },
        timeout=30
    )
    
    return response.json()
```

**Error Handling**:
- Retry on connection errors (Ollama might be starting up)
- Timeout after 30 seconds per image
- Log failures and continue with next PDF
- Track Ollama availability issues
- Graceful degradation if Ollama is unavailable

**GPU Optimization**:
- Ollama automatically uses GPU when available
- RTX 3080 provides ~3-5x speedup vs CPU
- Monitor GPU memory usage (10GB VRAM available)
- Can process multiple images concurrently

### Batch Processing Strategy

**Phase 1: Pilot (50 individual PDFs)**
- Randomly select 50 PDFs from diverse artists/books
- Run full pipeline (all pages checked)
- Manually review ALL results
- Tune prompts and thresholds
- Validate GPU performance and disk usage

**Phase 2: Small Batch (500 individual PDFs)**
- Run on 500 PDFs across multiple books
- Spot-check 10% of results
- Validate false positive rate is acceptable
- Confirm system stability over longer run

**Phase 3: Full Run (11,976 individual PDFs)**
- Process all individual song PDFs
- Generate final reports
- Manual review of flagged items

### Performance Considerations

**Parallelization**:
- Process individual PDFs in parallel (12 workers recommended for i9-12900K)
- Each worker processes one PDF at a time
- Ollama can handle concurrent requests with GPU acceleration
- Monitor GPU memory usage (10GB VRAM)

**Caching**:
- Cache rendered PNG files to D:\ImageCache\pdf_verification\
- Organize by artist/book/song for easy cleanup
- Reuse cached renders if re-running
- Clean up cache after successful verification (optional)

**Progress Tracking**:
- Save progress after each PDF to JSON checkpoint file
- Resume from last checkpoint if interrupted
- Real-time progress bar with ETA
- Log GPU utilization and inference times

**Estimated Runtime** (with GPU acceleration):
- ~11,976 individual PDFs
- ~42,000 pages total (avg 3.5 pages/PDF)
- ~1-2 seconds per Ollama call (GPU accelerated)
- ~42,000-84,000 seconds = ~12-23 hours (single-threaded)
- **With 12 workers: ~1-2 hours** (recommended)
- **With 16 workers: ~45-90 minutes** (aggressive)

## Output CSV Format

### verification-results-flagged.csv

```csv
pdf_path,source_book,artist,song_title,issue_type,severity,first_page_has_title,first_page_title,last_page_has_new_song,middle_page_has_title,details
ProcessedSongs/Beatles/Abbey Road/Beatles - Come Together.pdf,Abbey Road,Beatles,Come Together,NO_TITLE_ON_FIRST,ERROR,NO,N/A,NO,NO,"First page missing song title"
ProcessedSongs/Beatles/Abbey Road/Beatles - Something.pdf,Abbey Road,Beatles,Something,NEW_SONG_ON_LAST,ERROR,YES,Something,YES,NO,"Last page starts new song: 'Come Together'"
```

### verification-results-by-book.csv

```csv
source_book,artist,total_songs,flagged_count,warning_count,passed_count,error_rate
Abbey Road,Beatles,17,2,3,12,11.8%
Glass Houses,Billy Joel,10,0,1,9,0.0%
```

## Manual Review Workflow

User will review `verification-results-flagged.csv`:

1. Open CSV in Excel/spreadsheet
2. Add column: `confirmed_issue` (YES/NO)
3. Add column: `notes` (free text)
4. For each flagged individual PDF:
   - Open the PDF manually
   - Verify if the issue is real
   - Mark YES if confirmed, NO if false positive
5. Save reviewed CSV
6. Run fix script (future work) to re-split confirmed issues from source books

## Future Enhancements

1. **Automated fixing**: Re-split books with confirmed issues
2. **Page number detection**: OCR page numbers and verify sequential
3. **Staff line counting**: Verify consistent staff line count per page
4. **Lyrics detection**: Flag pages with excessive text (might be lyrics/instructions)
5. **Confidence scoring**: Assign confidence scores to each check
6. **Web UI**: Interactive review interface instead of CSV

## Questions for User

1. **Workers**: Start with 12 workers (recommended for your CPU), or try 16 for faster processing?
2. **Pilot selection**: Randomly select 50 PDFs, or do you want to specify particular artists/books?
3. **Cache cleanup**: Keep rendered PNGs after verification, or auto-delete to save space?
