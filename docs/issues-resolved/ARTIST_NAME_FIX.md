# Artist Name Fix - January 26, 2026

## Problem

Two critical issues were identified:

1. **Wrong Artist Names**: Songs from single-artist books (like ACDC Anthology) were being labeled with songwriter/composer names (e.g., "Angus Young - Malcolm Young - Brian Johnson") instead of the performer name (e.g., "ACDC")

2. **Few Songs Detected**: Some books were only extracting a few songs instead of all songs in the book

## Root Cause

The page mapper service was not receiving the book-level artist name from the state machine. When vision scanned sheet music pages, it extracted the composer/songwriter names that appear on the page rather than using the performer name from the book's folder structure.

## Solution

### 1. Pass Book-Level Artist to Page Mapper

**Modified Files:**
- `ecs/task_entrypoints.py`: Updated `page_mapper_task()` to accept `ARTIST` and `BOOK_NAME` environment variables
- `app/services/page_mapper.py`: Updated `build_page_mapping()` to accept `book_artist` and `book_name` parameters

### 2. Implement Smart Artist Assignment Logic

Added logic to determine artist names based on book type:

**For Single-Artist Books** (e.g., "ACDC", "Billy Joel"):
- ALWAYS use the book-level artist from the folder name
- Ignore vision-extracted artist names (which are usually songwriters)
- Example: `SheetMusic/ACDC/books/ACDC - Anthology.pdf` → All songs labeled as "ACDC"

**For Various Artists Books** (e.g., "Various Artists", "Fake Books", "Broadway"):
- Use TOC artist if available
- Fall back to vision-extracted artist
- Fall back to "Unknown Artist"
- Example: `SheetMusic/Various Artists/books/Great Bands Of The 70s.pdf` → Each song gets its own artist

### 3. Detection Logic

Added `_is_various_artists_book()` method that checks for indicators:
- "Various Artists"
- "Compilation"
- "Fake Book" / "Fakebook"
- "Broadway"
- "Movie" / "TV" / "Television"
- "Soundtrack"
- "Collection"

### 4. State Machine Update

**Modified File:** `temp_state_machine_def_ascii.json`

Added environment variables to PageMapping task:
```json
{
  "Name": "ARTIST",
  "Value.$": "$.artist"
},
{
  "Name": "BOOK_NAME",
  "Value.$": "$.book_name"
}
```

## Deployment

1. **Docker Image**: Built and pushed with digest `sha256:0d5bc416b050d935ceb2ad8480d6b33e724e8bf6d805acdf588346a49c44b586`
2. **Task Definition**: Registered as `jsmith-page-mapper:6`
3. **State Machine**: Updated to use new task definition and pass artist/book_name

## Expected Behavior After Fix

### Single-Artist Books
```
Input: SheetMusic/ACDC/books/ACDC - Anthology.pdf
Output: 
  ACDC/Anthology/Songs/ACDC - You Shook Me All Night Long.pdf
  ACDC/Anthology/Songs/ACDC - Back In Black.pdf
  ACDC/Anthology/Songs/ACDC - Highway To Hell.pdf
```

### Various Artists Books
```
Input: SheetMusic/Various Artists/books/Great Bands Of The 70s.pdf
Output:
  Various Artists/Great Bands Of The 70s/Songs/Abba - Knowing Me, Knowing You.pdf
  Various Artists/Great Bands Of The 70s/Songs/Blondie - Heart Of Glass.pdf
  Various Artists/Great Bands Of The 70s/Songs/Free - All Right Now.pdf
```

## Testing

To test the fix:

1. **Stop the current batch processing** (Ctrl+C)
2. **Clear DynamoDB** for books you want to reprocess:
   ```powershell
   # This will force reprocessing
   aws dynamodb delete-item --table-name jsmith-sheetmusic-splitter-books --key '{"book_id":{"S":"acdc-anthology"}}' --region us-east-1
   ```
3. **Rerun the batch script**:
   ```powershell
   .\process-and-download-all.ps1
   ```

## Notes

- The fix only affects NEW processing runs
- Already-processed books will NOT be automatically fixed
- To fix existing books, you must:
  1. Delete their DynamoDB records
  2. Reprocess them through the pipeline
  3. The new files will overwrite the old ones in S3

## Files Modified

1. `ecs/task_entrypoints.py` - Added ARTIST and BOOK_NAME parameters
2. `app/services/page_mapper.py` - Added book_artist logic and _is_various_artists_book() method
3. `temp_state_machine_def_ascii.json` - Added ARTIST and BOOK_NAME to PageMapping task
4. `temp_page_mapper_task_def_v6.json` - New task definition with updated image

## Deployment Artifacts

- Docker Image Digest: `sha256:0d5bc416b050d935ceb2ad8480d6b33e724e8bf6d805acdf588346a49c44b586`
- Page Mapper Task Definition: `arn:aws:ecs:us-east-1:227027150061:task-definition/jsmith-page-mapper:6`
- State Machine Revision: `025ff528-8442-4d56-9bad-dbcf7a90c20e`
- Update Date: 2026-01-26 11:14:44 EST
