# Book Review and Reprocessing Guide

## Overview

These scripts help you identify books that may have had extraction issues and selectively reprocess them.

## Step 1: Generate Report

Run this after the batch job completes (or while it's running to check progress):

### Basic Report (Fast)
```powershell
.\generate-book-report.ps1
```

### Enhanced Report with TOC Comparison (Slower but more accurate)
```powershell
.\generate-book-report.ps1 -IncludeTOCComparison
```

The enhanced report fetches TOC data from S3 to show:
- **ExpectedCount**: Number of songs found in the Table of Contents
- **ExtractionRate**: Percentage of expected songs that were actually extracted
- **LOW_EXTRACTION_RATE**: Flag for books with <80% extraction rate

**Note**: The TOC comparison is slower because it downloads data from S3 for each book. Use it when you want detailed analysis.

### Report Columns

- **Artist**: Book artist
- **BookName**: Book name
- **SongCount**: Number of songs extracted
- **ExpectedCount**: Songs in TOC (only with -IncludeTOCComparison)
- **ExtractionRate**: Percentage extracted (only with -IncludeTOCComparison)
- **UniqueArtists**: Number of different artists in filenames
- **ArtistList**: List of all artists found
- **Issues**: Detected problems (see below)
- **NeedsReview**: TRUE if any issues detected
- **Path**: Local path to the book folder

### Issue Types

- **FEW_SONGS**: Less than 3 songs extracted (likely incomplete)
- **LOW_EXTRACTION_RATE**: Less than 80% of TOC entries were extracted (requires -IncludeTOCComparison)
- **MULTIPLE_ARTISTS**: Single-artist book has multiple artist names in filenames
- **ARTIST_MISMATCH**: Folder artist doesn't match filename artist
- **SONGWRITER_NAME**: Detected songwriter names instead of performer names

## Step 2: Review the Report

Open `book-processing-report.csv` in Excel:

1. **Sort by NeedsReview** (TRUE first) to see problematic books
2. **Filter by Issues** to focus on specific problems
3. **Sort by SongCount** to find books with very few songs

### What to Look For

**Books with LOW_EXTRACTION_RATE** (requires -IncludeTOCComparison):
- TOC had 25 songs, but only 18 were extracted (72%)
- Indicates page mapping or verification failures
- Most reliable indicator of incomplete extraction

**Books with FEW_SONGS**:
- ACDC Anthology: 3 songs (should have ~20+)
- These likely had TOC parsing or page detection failures

**Books with SONGWRITER_NAME**:
- Artist shows as "Angus Young - Malcolm Young" instead of "ACDC"
- These were processed before the fix

**Books with ARTIST_MISMATCH**:
- Folder says "Billy Joel" but files say "Joel, Billy"
- Usually just formatting differences

## Step 3: Create Reprocess List

From the CSV, create a new file with just the books you want to reprocess:

**Option A - Filter in Excel**:
1. Open `book-processing-report.csv`
2. Filter to books with issues
3. Copy Artist and BookName columns
4. Save as `books-to-reprocess.csv`

**Option B - Use PowerShell**:
```powershell
# Get all books with fewer than 5 songs
Import-Csv book-processing-report.csv | 
    Where-Object { $_.SongCount -lt 5 } | 
    Select-Object Artist, BookName | 
    Export-Csv books-to-reprocess.csv -NoTypeInformation

# Or get all books with any issues
Import-Csv book-processing-report.csv | 
    Where-Object { $_.NeedsReview -eq 'True' } | 
    Select-Object Artist, BookName | 
    Export-Csv books-to-reprocess.csv -NoTypeInformation
```

## Step 4: Reprocess Books

```powershell
# Dry run first to see what would happen
.\reprocess-books.ps1 -BookListFile books-to-reprocess.csv -DryRun

# Actually reprocess
.\reprocess-books.ps1 -BookListFile books-to-reprocess.csv
```

This script will:
1. Delete the DynamoDB record for each book
2. Submit a new Step Functions execution
3. The new execution will use the FIXED code

## Step 5: Download Updated Files

After reprocessing completes:

```powershell
.\download-all-songs.ps1
```

The new files will overwrite the old ones.

## Bulk Rename for Artist Names

If you just need to fix artist names in filenames (not reprocess):

```powershell
# Example: Rename all "Angus Young - Malcolm Young - ..." to "ACDC - ..."
Get-ChildItem -Path ".\ProcessedSongs\Acdc\*\Songs\*.pdf" -Recurse | 
    Where-Object { $_.Name -notlike "Acdc - *" } | 
    ForEach-Object {
        $newName = $_.Name -replace '^[^-]+ - ', 'Acdc - '
        Rename-Item -Path $_.FullName -NewName $newName
        Write-Host "Renamed: $($_.Name) -> $newName"
    }
```

## Quick Stats

To get a quick count of songs per book without generating full report:

```powershell
Get-ChildItem -Path ".\ProcessedSongs" -Directory | ForEach-Object {
    $artist = $_.Name
    Get-ChildItem -Path $_.FullName -Directory | ForEach-Object {
        $book = $_.Name
        $songCount = (Get-ChildItem -Path "$($_.FullName)\Songs" -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
        [PSCustomObject]@{
            Artist = $artist
            Book = $book
            Songs = $songCount
        }
    }
} | Sort-Object Songs | Format-Table -AutoSize
```

## Example Workflow

```powershell
# 1. Generate enhanced report with TOC comparison
.\generate-book-report.ps1 -IncludeTOCComparison

# 2. Review in console or Excel
# Look for LOW_EXTRACTION_RATE, FEW_SONGS, or SONGWRITER_NAME issues

# 3. Create filtered list for books with low extraction
Import-Csv book-processing-report.csv | 
    Where-Object { 
        $_.ExtractionRate -ne "N/A" -and 
        [int]($_.ExtractionRate -replace '%', '') -lt 80 
    } | 
    Select-Object Artist, BookName, SongCount, ExpectedCount, ExtractionRate | 
    Export-Csv books-to-reprocess.csv -NoTypeInformation

# 4. Reprocess (dry run first)
.\reprocess-books.ps1 -BookListFile books-to-reprocess.csv -DryRun
.\reprocess-books.ps1 -BookListFile books-to-reprocess.csv

# 5. Wait for completion, then download
.\download-all-songs.ps1

# 6. Generate new report to verify
.\generate-book-report.ps1 -IncludeTOCComparison
```

## Notes

- The basic report is fast and only reads local files
- The TOC comparison report is slower but more accurate (downloads from S3)
- Use `-IncludeTOCComparison` when you want to identify incomplete extractions
- Reprocessing costs money (AWS charges), so review the list carefully first
- Use `-DryRun` to test before actually reprocessing
- Books processed after the fix (deployed Jan 26, 2026 11:14 AM) should be correct
- Books processed before the fix may have artist name issues

## Performance Tips

**For quick checks** (150+ books):
```powershell
.\generate-book-report.ps1  # Fast, local only
```

**For detailed analysis** (when you have time):
```powershell
.\generate-book-report.ps1 -IncludeTOCComparison  # Slower, downloads TOC data
```

**For specific books** (check just a few):
```powershell
# Manually check TOC for specific book
aws s3 cp s3://jsmith-output/artifacts/acdc-anthology/toc_parse.json - --region us-east-1 | ConvertFrom-Json | Select-Object -ExpandProperty entries | Measure-Object
```
