# Songbook Reprocessing and Manual Editing Guide

## Overview

You now have tools to:
1. **Queue books for reprocessing** - Mark incomplete books to be reprocessed through the pipeline
2. **Manually adjust split points** - Visually edit where songs start and end when auto-detection fails
3. **Batch reprocess** - Process multiple books from a queue

---

## Tool 1: Complete Provenance Viewer (Enhanced)

**Location**: `web/viewers/complete_provenance_viewer.html`

### New Features

#### Reprocessing Queue
- **Queue Button**: Click "Queue" on any book to add it to the reprocessing queue
- **Reprocess Queue Button**: View all queued books (shows count badge)
- **Export Queue**: Export book IDs to `books_to_reprocess.txt`
- **Clear Queue**: Remove all books from queue

#### Manual Editor
- **Edit Button**: Opens the manual split point editor for the selected book
- Automatically loads book info into the editor

### Usage Workflow

1. **Find incomplete books**:
   - Filter by Status: "Incomplete"
   - Check issues column for specific problems

2. **Add to reprocess queue**:
   - Click "Queue" button for books that need reprocessing
   - Queue is saved in browser localStorage

3. **Export queue**:
   - Click "Reprocess Queue" button
   - Click "Export to file"
   - Saves `books_to_reprocess.txt` with book IDs

4. **For manual editing**:
   - Click "Edit" button
   - Opens manual split point editor in new tab

---

## Tool 2: Manual Split Point Editor

**Location**: `web/editors/manual_split_editor.html`

### Features

- **PDF Viewer**: Display source PDF with navigation
- **Song List**: Left panel shows all songs with split points
- **Visual Marking**: Click pages and mark them as song start points
- **Manual Entry**: Type in exact page ranges
- **Save/Export**: Save split points to JSON file

### Usage Workflow

#### Starting Fresh

1. **Load PDF**:
   - Click "Load PDF" button
   - Select source PDF from `SheetMusic/` folder

2. **Load TOC (if available)**:
   - Enter book ID in the text field
   - Click "Load from Database"
   - This loads TOC entries as starting points

3. **Adjust Split Points**:
   - Navigate through PDF pages
   - For each song:
     - Click "Mark as Start Page" when you see the song begin
     - Adjust end page manually
     - Click "Add Song" or "Update Selected Song"

4. **Review**:
   - Check statistics panel
   - Ensure all pages are covered
   - Verify song count matches expectations

5. **Save**:
   - Click "Save Split Points" (saves to browser)
   - Click "Export JSON" to download file
   - Save file as `data/manual_splits/{book_id}.json`

#### Editing Existing Splits

1. Load PDF
2. Load from database or import existing JSON
3. Click a song in the list to select it
4. Adjust start/end pages
5. Click "Update Selected Song"
6. Save when done

### Manual Split Point Format

```json
{
  "book_id": "abc123",
  "book_name": "Artist - Album",
  "created_at": "2026-02-03T12:00:00Z",
  "total_pages": 100,
  "songs": [
    {
      "title": "Song Title",
      "start_page": 10,
      "end_page": 15,
      "page_count": 6,
      "source": "manual"
    }
  ]
}
```

---

## Tool 3: Reprocessing Script

**Location**: `scripts/reprocessing/reprocess_book.py`

### Usage

#### Single Book
```bash
cd d:\Work\songbook-splitter
py scripts\reprocessing\reprocess_book.py abc123def456
```

#### Batch Processing
```bash
py scripts\reprocessing\reprocess_book.py --from-file books_to_reprocess.txt
```

### What It Does

1. Loads book info from provenance database
2. Verifies source PDF exists
3. Checks for manual split points in `data/manual_splits/{book_id}.json`
4. **TODO**: Triggers your processing pipeline
   - You need to implement the actual pipeline trigger
   - Options:
     - AWS Lambda invocation
     - Step Functions execution
     - Local processing script
     - Docker container run

### Implementing Pipeline Trigger

Edit `reprocess_book.py` and add your pipeline trigger:

```python
# Option 1: AWS Lambda
lambda_client = boto3.client('lambda')
response = lambda_client.invoke(
    FunctionName='your-processing-function',
    InvocationType='Event',
    Payload=json.dumps({
        'book_id': book_id,
        'source_pdf': str(source_pdf_path),
        'manual_splits': manual_split_file if manual_split_file.exists() else None
    })
)

# Option 2: Local script
import subprocess
subprocess.run([
    'py', 'process_songbook.py',
    '--source', str(source_pdf_path),
    '--book-id', book_id,
    '--manual-splits', str(manual_split_file) if manual_split_file.exists() else ''
])

# Option 3: Step Functions
sfn = boto3.client('stepfunctions')
response = sfn.start_execution(
    stateMachineArn='your-state-machine-arn',
    input=json.dumps({
        'book_id': book_id,
        'source_pdf': str(source_pdf_path),
        'use_manual_splits': manual_split_file.exists()
    })
)
```

---

## Complete Workflow: Fixing an Incomplete Book

### Example: ACDC Anthology (16 TOC songs, only 3 present)

1. **In Provenance Viewer**:
   - Search for "ACDC Anthology"
   - See: TOC Songs: 16, Actual Songs: 3
   - Status: INCOMPLETE, Issues: MISSING_SONGS:13

2. **Option A: Auto-Reprocess**:
   - Click "Queue" button
   - After reviewing several books, click "Reprocess Queue"
   - Export to `books_to_reprocess.txt`
   - Run: `py reprocess_book.py --from-file books_to_reprocess.txt`
   - Your pipeline re-extracts songs (hopefully with better results)

3. **Option B: Manual Split Points**:
   - Click "Edit" button
   - Manual editor opens
   - Load the source PDF: `SheetMusic/ACDC/ACDC - Anthology.pdf`
   - Enter book ID: `48a0aa4baf216184`
   - Click "Load from Database" (loads 16 TOC entries)
   - Page through PDF, adjust each song's end page
   - Songs should now span all pages
   - Export JSON to `data/manual_splits/48a0aa4baf216184.json`
   - Run reprocessing script (will detect manual splits)

4. **Verify**:
   - After reprocessing completes
   - Rebuild provenance database:
     ```bash
     py scripts/analysis/finalize_provenance_with_song_matching.py
     ```
   - Refresh provenance viewer
   - Check ACDC Anthology now shows 16/16 songs

---

## Best Practices

### When to Use Auto-Reprocessing
- TOC was detected but page ranges are slightly off
- A few songs are missing but most are correct
- Source PDF quality is good
- You've improved the TOC detection algorithm

### When to Use Manual Split Points
- TOC detection completely failed
- Songs are split incorrectly (merged or cut off)
- Non-standard book layout
- Book has no TOC (you need to define all songs manually)
- Quick fix needed for specific problem book

### Batch Processing Tips
1. Review books in viewer first
2. Add similar problems to queue together
3. Export queue after collecting 10-20 books
4. Process in batches during off-hours
5. Review results and rebuild database

---

## Storage Locations

- **Reprocess Queue**: Browser localStorage (`reprocess_queue`)
- **Manual Splits**: `data/manual_splits/{book_id}.json`
- **Exported Queue**: `books_to_reprocess.txt` (downloads folder)
- **Provenance Database**: `data/analysis/complete_provenance_database.json`

---

## Troubleshooting

### "Manual editor won't load PDF"
- Make sure PDF.js CDN is accessible
- Try a different browser
- Check browser console for errors

### "Queue not saving"
- Check if localStorage is enabled in browser
- Try a different browser
- Clear browser cache and retry

### "Reprocessing script says 'TODO'"
- You need to implement the pipeline trigger
- See "Implementing Pipeline Trigger" section above
- Connect to your actual processing system

### "Split points not being used"
- Make sure JSON is in `data/manual_splits/{book_id}.json`
- Verify format matches expected structure
- Check reprocessing script detects the file

---

## Next Steps

1. **Test the manual editor**:
   - Open `web/editors/manual_split_editor.html`
   - Load a problematic PDF
   - Try marking split points

2. **Implement pipeline trigger**:
   - Edit `scripts/reprocessing/reprocess_book.py`
   - Add your actual processing invocation
   - Test with one book first

3. **Process incomplete books**:
   - Use viewer to identify issues
   - Queue books for reprocessing
   - Use manual editor for problem cases
   - Run batch reprocessing

4. **Verify results**:
   - Rebuild provenance database
   - Check improvements in viewer
   - Iterate on problem books
