# Book Inventory Reconciliation Summary

## Final Accurate Count

- **Total Source Books**: 561 PDF files in Books folders
- **Successfully Expanded**: 396 books (70.6%)
- **Not Expanded**: 165 books (29.4%)
  - Includes both unprocessed books AND books that were processed but failed to extract songs

## Key Findings

### 1. Actual Source Book Count
The actual count is **561 source books**, not 562 as previously thought. This was verified by counting all PDF files in "Books" folders across the SheetMusic directory.

### 2. Duplicate Source Books
Some source books are duplicates or different versions that map to the same processed folder:
- 396 source books map to 386 unique processed folders
- 33 processed folders have multiple source books mapping to them
- Examples:
  - Beatles - Anthology: 9 different source versions
  - Beatles - Complete Scores: 2 versions
  - Beatles - Fake Songbook: 2 versions

### 3. Empty Processed Folders
Many books were processed but failed to extract any songs, resulting in empty folders:
- These folders exist in ProcessedSongs but contain 0 PDF files
- Examples:
  - Adele - 19 [PVG Book]
  - Allman Brothers - Allman Brothers Band [PVG]
  - Allman Brothers - Band Best [Score]
  - Allman Brothers - Best Of [PVG]

### 4. Special Folder Structures
The script now correctly handles special folder structures:
- **_Movie and TV**: Has subdirectories (Disney, John Williams, Others) with Books folders
  - Source: `SheetMusic\_Movie and TV\<Subcategory>\Books\*.pdf`
  - Processed: `ProcessedSongs\_movie And Tv\<BookName>\*.pdf`
- **_Broadway Shows**: Has both direct Books folder and composer subdirectories
  - Source: `SheetMusic\_Broadway Shows\Books\*.pdf`
  - Source: `SheetMusic\_Broadway Shows\<Composer>\Books\*.pdf`
  - Processed: `ProcessedSongs\_broadway Shows\<BookName>\*.pdf`

## Processing Status

### Successfully Processed
**396 books (70.6%)** have been successfully expanded with PDF files extracted.

### Processed But Failed Extraction
**162 books (28.9%)** were processed but failed to extract any songs:
- Empty folders exist in ProcessedSongs
- These need to be re-processed or investigated for extraction issues
- May indicate problems with:
  - Table of contents parsing
  - Page mapping
  - PDF structure incompatibility

### Never Processed
**3 books (0.5%)** were never processed at all:
1. Elvis Presley - The Compleat [PVG Book]
2. Mamas and The Papas - Songbook [PVG]
3. Robbie Robertson - Songbook [Guitar Tab]

These books have no artist folder in ProcessedSongs and need to be uploaded and processed.

## Files Generated

- `source-books-status-final.csv`: Complete inventory with status of all 561 source books
- `build-accurate-inventory-fixed.ps1`: Script that generates the inventory

## Next Steps

1. **Process the 3 never-processed books**:
   - Elvis Presley - The Compleat [PVG Book]
   - Mamas and The Papas - Songbook [PVG]
   - Robbie Robertson - Songbook [Guitar Tab]

2. **Investigate the 162 failed extractions**:
   - Review a sample of failed books to identify common issues
   - Check if they have table of contents problems
   - Check if they have unusual PDF structures
   - Determine if code fixes are needed or if they're just incompatible formats

3. **Re-process failed books** (if fixes are identified):
   - Process in small batches
   - Monitor for success rate improvements

4. **Update final statistics** after processing/re-processing
