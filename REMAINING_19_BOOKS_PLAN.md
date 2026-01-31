# Processing Remaining 19 Books - Complete Plan

## Status

- **Steely Dan**: ✓ Processed and downloaded (23 songs)
- **Remaining**: 19 books to process

## What Was Done

### 1. Fixed JSON Encoding Issue
- **Problem**: PowerShell's `ConvertTo-Json` with UTF-8 encoding added BOM (Byte Order Mark)
- **Solution**: Changed to ASCII encoding for temp JSON files
- **Result**: Step Functions now accepts the JSON input correctly

### 2. Tested with Steely Dan
- Successfully uploaded PDF to S3
- Started Step Functions execution
- Execution completed in 2.2 seconds (already processed)
- Downloaded 23 songs to `ProcessedSongs\Steely Dan\Steely Dan - The Best\`

### 3. Updated CSV
- Created `ready_for_aws_processing_remaining_19.csv`
- Removed Steely Dan from the list
- 19 books remaining

## The 19 Remaining Books

1. Various Artists - 25th Annual Putnam County Spelling Bee (_Broadway Shows)
2. Various Artists - High School Musical _score_ (_Broadway Shows)
3. Various Artists - Little Shop Of Horrors _Broadway_ (_Broadway Shows)
4. Various Artists - Little Shop Of Horrors Script (_Broadway Shows)
5. Various Artists - Shrek The Musical (_Broadway Shows)
6. Various Artists - Youre A Good Man Charlie Brown _Score_ (_Broadway Shows)
7. Wicked Workshop (_Broadway Shows)
8. The Wizard Of Oz Script (_Movie and TV)
9. Various Artists - Complete TV And Film (_Movie and TV)
10. Crosby Stills Nash And Young - The Guitar Collection (Crosby Stills and Nash)
11. Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_ (Dire Straits)
12. Elvis Presley - The Compleat _PVG Book_ (Elvis Presley)
13. Eric Clapton - The Cream Of Clapton (Eric Clapton)
14. John Denver - Back Home Again (John Denver)
15. Mamas And The Papas - Songbook _PVG_ (Mamas and the Papas)
16. Night Ranger - Seven Wishes _Jap Score_ (Night Ranger)
17. Robbie Robertson - Songbook _Guitar Tab_ (Robbie Robertson)
18. Tom Waits - Tom Waits Anthology (Tom Waits)
19. Various Artists - Ultimate 80s Songs (Various Artists)

## Scripts Ready to Use

### 1. Process All 19 Books
```powershell
.\process-remaining-19-books.ps1
```

This will:
- Upload each PDF to S3
- Start Step Functions execution for each book
- Save execution details to `remaining-19-executions.csv`
- Wait 500ms between executions to avoid throttling

### 2. Download Results
```powershell
.\download-remaining-19-results.ps1
```

This will:
- Check status of all executions
- Download completed books from S3
- Save to `ProcessedSongs\{Artist}\{BookName}\`
- Show summary of succeeded/failed/running

## Expected Timeline

- **Upload time**: ~1 minute (19 books × 3 seconds each)
- **Processing time**: 2-5 minutes per book
- **Total time**: ~40-100 minutes for all 19 books
- **Download time**: ~5-10 minutes (depends on number of songs)

## S3 Path Structure

Files are stored at:
```
s3://jsmith-output/{Artist}/{BookName}/Songs/{Artist} - {SongTitle}.pdf
```

Example:
```
s3://jsmith-output/Steely Dan/Steely Dan - The Best/Songs/Steely Dan - Aja.pdf
```

## After Completion

Once all 19 books are processed and downloaded:
- Total books: 561/561 (100%)
- All books split into individual songs
- Ready for final verification and project completion

## Notes

- The script uses ASCII encoding for JSON files to avoid BOM issues
- Each execution is named with timestamp for uniqueness
- Temp JSON files are cleaned up after each execution
- The state machine ARN is correct: `arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline`
