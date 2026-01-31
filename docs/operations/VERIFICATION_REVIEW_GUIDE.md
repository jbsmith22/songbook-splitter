# PDF Verification Review Guide

## Quick Start

### 1. Run Verification on Your PDFs

Create a text file with PDF paths (relative to ProcessedSongs), one per line:

```
Various Artists/Best Of 80s Rock [pvg]/The Police - Every Breath You Take.pdf
Billy Joel/52nd Street/Billy Joel - Big Shot.pdf
...
```

Then run:

```powershell
py run_verification_with_output.py your_pdf_list.txt
```

This will:
- Render all pages to JPG (cached in S:\SlowImageCache)
- Call AWS Bedrock (Claude 3.5 Sonnet) to analyze each page
- Save results to `verification_results/bedrock_results.json`
- Show cost and summary

### 2. Generate Review Page

```powershell
py generate_review_page.py
```

This creates an HTML page at: `verification_results/review_page.html`

### 3. Review in Browser

Open the HTML file in your browser:

```
file:///C:/Work/AWSMusic/verification_results/review_page.html
```

For each flagged PDF, you'll see:
- All pages with embedded images
- Claude's analysis for each page
- Which pages were flagged and why
- Three buttons:
  - **✓ Detection is CORRECT** - Real issue, should be flagged
  - **✗ Detection is WRONG** - False positive, PDF is actually fine
  - **⊘ Skip / Unsure** - Not sure, skip for now

**When you mark a false positive**, a feedback section appears with:
- **Quick-select reasons**: Common false positive patterns
  - Song starts mid-page (acceptable)
  - Guitar tabs above music (normal)
  - Text-only guitar tabs (no staff)
  - Extra content at end (photos/text)
  - Section marker (not new song)
  - Tempo/key change (same song)
  - Title mid-page (previous song ends)
  - Just continuation of song
  - Other (explain below)
- **Notes field**: Add any additional context

**When you mark a correct detection**, a different feedback section appears with:
- **Error type classification** (select one):
  - ⚠️ **Starts mid-song (SAME song)** - Like Bob Dylan: PDF has the correct song but starts partway through it
  - ❌ **Wrong song entirely (DIFFERENT song)** - Like Billy Joel: PDF is labeled one song but contains a different song
  - 🔀 **Missed split (multiple songs)** - Like Every Breath You Take: Multiple songs in one PDF that should be split
  - 📄 **Extra pages** - Song continues into the next song's pages
- **Notes field**: Add details about what's wrong

This distinction is critical for understanding what types of errors the splitter is making.

Your reviews and feedback are saved automatically in browser localStorage.

### 4. Export Your Feedback

Click the "💾 Export Reviews" button to download a JSON file with your feedback.

The exported file includes:
- Summary statistics (total, correct, false positives, rate)
- Your review decisions for each PDF
- Detailed feedback reasons and notes
- Timestamp

### 5. Analyze Feedback Patterns

Run the analysis script on your exported feedback:

```powershell
py analyze_feedback.py review_feedback_2026-01-28.json
```

This will:
- Calculate false positive rate
- Identify common false positive patterns
- Suggest specific prompt improvements
- Recommend whether to proceed with full run or tune first

## Test Run (5 Known Errors)

I've already run a test with the 5 known errors:

```powershell
py run_verification_with_output.py test_5_known_errors.txt
py generate_review_page.py
```

Open `verification_results/review_page.html` to see the interface.

All 5 should be marked as "✓ Detection is CORRECT" since these are real issues.

## Next Steps

### Option 1: Test with 50 Manually Reviewed PDFs

Create a list of the 50 PDFs you manually reviewed and run the same process.

This will give us a good estimate of the false positive rate.

### Option 2: Run Full Verification (11,976 PDFs)

If the false positive rate is acceptable (say, under 20%), we can run the full verification:

1. Create a list of all 11,976 PDFs
2. Run verification (will take ~2-3 hours, cost ~$400)
3. Generate review page
4. Review only the flagged PDFs (hopefully a manageable number)

## Cost Estimates

- **5 PDFs**: $0.18 (2 minutes)
- **50 PDFs**: ~$1.80 (20 minutes)
- **11,976 PDFs**: ~$418 (2-3 hours)

## Files

- `run_verification_with_output.py` - Main verification script
- `generate_review_page.py` - Generate HTML review page
- `analyze_feedback.py` - Analyze exported feedback and suggest improvements
- `test_5_known_errors.txt` - List of 5 known error PDFs
- `verification_results/bedrock_results.json` - Raw results
- `verification_results/review_page.html` - Interactive review page

## Feedback Categories Explained

### False Positive Reasons

When marking false positives, you can select from these categories:

- **Song starts mid-page**: The song title appears mid-page because the previous song ended there (this is acceptable per your split rules)
- **Guitar tabs above music**: Guitar tablature notation above standard sheet music (normal in guitar books)
- **Text-only guitar tabs**: Text-based guitar tabs without staff lines (valid format)
- **Extra content at end**: Photos, discography, or text blocks at the end (acceptable)
- **Section marker**: Verse/Chorus/Bridge markers within the same song (not a new song)
- **Tempo/key change**: Musical changes within the same song (not a new song)
- **Title mid-page**: Song title appears mid-page where previous song ends (acceptable)
- **Just continuation**: Simply a continuation of the current song (no issue)
- **Other**: Any other reason (please explain in notes)

### Error Type Classification

When marking correct detections, classify the error type:

- **⚠️ Starts mid-song (SAME song, wrong start)**: 
  - Example: Bob Dylan "It's Alright, Ma" - PDF has the correct song but starts partway through
  - The filename is correct, but the content is missing the beginning
  - This indicates the splitter found the wrong page as the start point

- **❌ Wrong song entirely (DIFFERENT song)**:
  - Example: Billy Joel "Opus 8" - PDF is labeled one song but contains a completely different song
  - The filename doesn't match the content at all
  - This indicates the splitter associated the wrong song with the wrong pages

- **🔀 Missed split (multiple songs)**:
  - Example: "Every Breath You Take" - Multiple distinct songs in one PDF
  - Should have been split into separate PDFs
  - This indicates the splitter failed to detect a song boundary

- **📄 Extra pages (continues into next song)**:
  - The song is correct but includes pages from the next song
  - This indicates the splitter found the wrong end point

This classification helps identify which part of the splitting algorithm needs improvement.
