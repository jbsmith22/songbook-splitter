# Batch Verification Workflow

## Overview

This workflow processes 11,983 PDFs in 8 batches, verifies them for split issues, allows manual review and correction, and generates comprehensive reports.

## Step 1: Run Batches

Run each batch sequentially (or all at once overnight):

```powershell
cd c:\Work\AWSMusic\verification_batches

# Run individual batches
.\batch1.ps1  # 2,000 PDFs - Various Artists (~2 hours, ~$70)
.\batch2.ps1  # 100 PDFs - Various Artists (~10 min, ~$3.50)
.\batch3.ps1  # 1,848 PDFs - Movie & TV (~1.5 hours, ~$65)
# ... etc

# Or run all at once
.\run_all_batches.ps1  # ~12-16 hours total, ~$420
```

Each batch creates:
- `verification_results/batch{N}_results.json` - Raw verification data
- `verification_results/batch{N}_review.html` - Review interface

## Step 2: Review Each Batch

Open each batch's review page in your browser:

```
file:///C:/Work/AWSMusic/verification_results/batch1_review.html
```

### Review Workflow

1. **Mark each flagged PDF:**
   - ✓ Detection is CORRECT (Real Issue) - Select error type
   - ✗ Detection is WRONG (False Positive) - Select reason
   - ⊘ Skip / Unsure

2. **For "Missed Split" errors:**
   - Click "Extract from Detection" to auto-extract song titles
   - Review and adjust song titles/page ranges
   - Click "Save Split Instructions"

3. **For "Multi-song page" errors:**
   - **Currently requires manual entry** (auto-extract doesn't work yet)
   - Manually enter song titles and page ranges
   - Click "Save Split Instructions"

4. **Export your work:**
   - Click "💾 Export Reviews" at the top
   - Save as `review_feedback_batch{N}.json`

## Step 3: Generate Comprehensive Reports

After reviewing all batches (or as many as you want), run the analysis script:

```powershell
cd c:\Work\AWSMusic
py analyze_all_batches.py
```

This generates reports in `verification_reports/`:

### Generated Reports

**JSON Files (detailed):**
1. `01_passed_verification.json` - All PDFs that passed (no issues)
2. `02_missed_splits.json` - Missed splits with correction status
3. `03_multi_song_pages.json` - Multiple songs on same page
4. `04_{error_type}.json` - Other error types (starts-mid-song, wrong-song, etc.)
5. `05_false_positives.json` - Incorrectly flagged PDFs
6. `06_unreviewed.json` - Flagged but not yet reviewed

**CSV Files (summaries):**
- `missed_splits_summary.csv` - Missed splits with original/new paths
- `multi_song_pages_summary.csv` - Multi-song pages with song lists

## Step 4: Execute Splits

For PDFs with split instructions, execute the actual splits:

```powershell
# Dry run first (shows what will happen)
py execute_splits.py review_feedback_batch1.json

# Execute for real
py execute_splits.py review_feedback_batch1.json --execute
```

Repeat for each batch that has split instructions.

## Known Issues

### 1. Multi-song Page Auto-Extract Doesn't Work

**Issue:** When you mark a PDF as "Multiple songs on same page", the auto-extract doesn't find the second song.

**Workaround:** Manually enter song titles and page ranges.

**Why:** The extraction logic looks for `has_issue: true` pages, but multi-song pages don't always trigger that flag.

### 2. "Select All Missed Splits" Only Finds First 5

**Issue:** The button only selects 5 PDFs even if more are marked.

**Possible Cause:** localStorage data not fully loaded, or browser cache issue.

**Workaround:** 
- Refresh the page (Ctrl+F5)
- Or manually check the boxes for missed splits

### 3. Feedback Not Used for Model Refinement

**Status:** Correct - we're not currently using feedback to retrain the model.

**Purpose:** The feedback is preserved for:
- Generating reports (what types of errors occur)
- Tracking false positive rate
- Future model improvements
- Audit trail of corrections made

## Tips

1. **Review in batches** - Don't try to review all 2,000 PDFs in batch 1 at once. Do 100-200, export, take a break.

2. **Export frequently** - Click "Export Reviews" every 30-60 minutes to save your work.

3. **Use bulk operations:**
   - "Select All 'Missed Split' Cases" - Quick select
   - "Extract Song Info for Selected" - Batch extract
   - Review and save each one

4. **False positives are OK** - If Claude flagged something incorrectly, mark it as false positive and move on. This helps us understand the accuracy rate.

5. **Skip if unsure** - If you're not sure about a PDF, click "Skip" and come back to it later.

## Estimated Time

- **Batch processing:** 12-16 hours (can run overnight)
- **Review per batch:** 30-60 minutes for 100-200 flagged PDFs
- **Total review time:** 4-8 hours across all batches
- **Report generation:** < 1 minute
- **Split execution:** 5-10 minutes per batch

## Cost

- **Total verification:** ~$420 for all 11,983 PDFs
- **Per batch:** ~$35-70 depending on size
