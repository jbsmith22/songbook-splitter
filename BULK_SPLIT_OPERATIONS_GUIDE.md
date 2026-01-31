# Bulk Split Operations Guide

## Overview

The PDF verification review interface now supports bulk operations for efficiently handling multiple PDFs that need splitting. This guide explains how to use these features and execute the splits.

## New Features

### 1. PDF Selection Checkboxes

Each PDF card now has a checkbox in the header that allows you to select it for bulk operations.

### 2. Bulk Action Buttons

Located at the top of the page, these buttons help you work with multiple PDFs at once:

- **✓ Select All "Missed Split" Cases** - Automatically selects only PDFs that you've marked with the "Missed split" error type
- **✓ Select All PDFs** - Selects every PDF on the page
- **✗ Deselect All** - Clears all selections
- **📋 Extract Song Info for Selected** - Runs the extraction process on all selected PDFs at once

### 3. Selection Counter

Shows how many PDFs are currently selected: "Selected: X PDFs"

## Workflow

### Step 1: Review and Mark PDFs

1. Review each flagged PDF
2. Click "✓ Detection is CORRECT" for real issues
3. Select the error type (e.g., "🔀 Missed split")
4. The split tool section will appear automatically

### Step 2: Select PDFs for Bulk Extraction

**Option A: Select Missed Splits Only**
- Click "✓ Select All 'Missed Split' Cases"
- This automatically finds and selects all PDFs you marked as missed splits

**Option B: Manual Selection**
- Check the boxes next to specific PDFs you want to process
- Or use "✓ Select All PDFs" to select everything

### Step 3: Extract Song Information

1. Click "📋 Extract Song Info for Selected"
2. The system will:
   - Extract song titles from Claude's detection responses
   - Calculate page ranges automatically
   - Populate the split form fields for each selected PDF
3. Review the results in the alert dialog

### Step 4: Review and Adjust

For each PDF with extracted songs:
1. Scroll to the PDF card
2. Review the extracted song titles and page ranges
3. Make any necessary corrections
4. Click "💾 Save Split Instructions"

### Step 5: Export Your Work

1. Click "💾 Export Reviews" at the top
2. This saves a JSON file with:
   - All your review decisions
   - Error type classifications
   - Split instructions for all PDFs
   - Timestamp and summary statistics

## Executing the Splits

Once you've saved split instructions and exported your reviews, you can execute the actual PDF splits.

### Dry Run (Preview)

First, run in dry-run mode to see what will happen:

```powershell
py execute_splits.py review_feedback_2026-01-28.json
```

This will show you:
- Which PDFs will be split
- What songs will be created
- What page ranges will be used
- Where files will be saved

**No files are modified in dry-run mode.**

### Execute the Splits

When you're ready to actually split the PDFs:

```powershell
py execute_splits.py review_feedback_2026-01-28.json --execute
```

This will:
1. Create new PDF files for each song
2. Name them: `{Artist} - {Song Title}.pdf`
3. Place them in the same folder as the original
4. Backup the original file as `{original}.pdf.original`

### Example Output

```
================================================================================
📄 Beatles - Please Please Me.pdf
   Artist: Beatles
   Book: Please Please Me
   Splitting into 2 songs:
   1. Please Please Me (pages 1-3) → Beatles - Please Please Me.pdf
      ✓ Created: C:\...\Beatles - Please Please Me.pdf
   2. One After 909 (pages 4-7) → Beatles - One After 909.pdf
      ✓ Created: C:\...\Beatles - One After 909.pdf
   ✓ Original backed up to: Beatles - Please Please Me.pdf.original
================================================================================
```

## Tips

1. **Work in Batches**: Review 10-20 PDFs, mark them, then use bulk extraction
2. **Save Often**: The interface auto-saves to localStorage, but export regularly
3. **Check Extractions**: Always review the extracted song titles before saving
4. **Test First**: Always run execute_splits.py in dry-run mode first
5. **Backup**: The execute script backs up originals, but you can also backup manually

## Troubleshooting

### "No songs detected" Error

If extraction fails for a PDF:
- The PDF might not have clear song boundaries in Claude's responses
- Try manual extraction using the "Extract from Detection" button on that specific PDF
- Or manually enter the song titles and page ranges

### Wrong Song Titles Extracted

- Claude's responses are parsed for text in quotes
- If the wrong text is extracted, manually correct it in the form fields
- Click "💾 Save Split Instructions" after correcting

### Selection Not Persisting

- Selections are saved to localStorage
- If you refresh the page, selections should restore
- If not, re-select and try again

## Data Storage

All data is stored in your browser's localStorage:
- `pdf-reviews` - Your review decisions (correct/incorrect/skip)
- `pdf-feedback` - False positive reasons and notes
- `pdf-correct-types` - Error type classifications
- `pdf-split-instructions` - Song titles and page ranges for splits
- `pdf-selected` - Currently selected PDFs

This data persists across browser sessions until you clear it or use "Clear All Reviews".
