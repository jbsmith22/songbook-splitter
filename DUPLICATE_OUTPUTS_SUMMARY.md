# Duplicate Output Folders Summary

## Overview
Found **331 input PDFs** that have multiple possible output folders.

## Breakdown

### 1. Identical PDF Counts (79 cases)
These output folders have the **same number of PDFs**, suggesting they're true duplicates of the same book with different naming conventions (bracket styles, etc.).

**Examples:**
- `America - Greatest Hits _Book_.pdf` → 
  - `America - Greatest Hits [Book]` (4 PDFs)
  - `America - Greatest Hits _Book_` (4 PDFs)

- `Beatles - Complete Scores.pdf` →
  - `Beatles - Complete Scores` (210 PDFs)
  - `Beatles - Complete Scores _2_` (210 PDFs)

- `Beatles - Revolver.pdf` →
  - `Beatles - Revolver` (14 PDFs)
  - `Beatles - Revolver _2_` (14 PDFs)

**Action:** For these 79 cases, we should:
1. Compare the actual PDF files in both folders to confirm they're identical
2. Keep the folder that exactly matches the input PDF name
3. Delete the other folder

**File:** `duplicates_identical_counts.csv`

### 2. Different PDF Counts (252 cases)
These output folders have **different numbers of PDFs**, meaning they're likely different versions or splits of the same book.

**Examples:**
- `Allman Brothers - Band Best _Score_.pdf` →
  - `Allman Brothers - Band Best _Score_` (8 PDFs)
  - `Allman Brothers - Best Of _PVG_` (28 PDFs)

- `America - Greatest Hits.pdf` →
  - `America - Greatest Hits` (12 PDFs)
  - `America - Greatest Hits [Book]` (4 PDFs)

- `Beatles - Anthology 1.pdf` →
  - `Beatles - Anthology 1` (18 PDFs)
  - `Beatles - Anthology` (199 PDFs)

**Action:** For these 252 cases, you need to manually review to determine:
1. Which output folder is the correct split of the input PDF
2. Whether both are valid (different versions from S3)
3. Which one should be kept

**File:** `duplicates_different_counts.csv`

## Recommended Workflow

### Phase 1: Handle Identical Counts (Automated)
1. For each of the 79 identical-count cases:
   - Compare the PDF files in both folders
   - If identical, keep the folder that matches the input PDF name exactly
   - Delete the duplicate folder

### Phase 2: Handle Different Counts (Manual Review)
1. Review the `duplicates_different_counts.csv` file
2. For each case, decide which output folder is correct
3. Delete the incorrect folder

## Expected Results

After cleanup:
- **Current:** 569 output folders
- **After removing ~79 identical duplicates:** ~490 output folders
- **After manual review of 252 different-count cases:** Will depend on your decisions

**Final target:** 559 output folders (one per input PDF) + any legitimate multiple versions from S3

## Files Created
- `duplicate_output_folders.csv` - All 331 duplicate cases
- `duplicates_identical_counts.csv` - 79 cases with same PDF count
- `duplicates_different_counts.csv` - 252 cases with different PDF counts
