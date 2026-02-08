# Processing Remaining 20 Books - Fixed Scripts

## Summary

Created corrected scripts to process the remaining 20 unprocessed books through the AWS Step Functions pipeline.

## Issues Fixed

### 1. Wrong AWS Account ID
- **Old**: `730335490735`
- **New**: `227027150061` ✓

### 2. Wrong State Machine Name
- **Old**: `SheetMusicSplitterStateMachine`
- **New**: `jsmith-sheetmusic-splitter-pipeline` ✓

### 3. Outdated File Paths
- **Problem**: CSV had old filenames with brackets/parentheses before normalization
- **Solution**: Created `update_ready_for_aws.py` to find actual normalized filenames
- **Result**: All 20 books found with correct paths ✓

## Files Created

### 1. `update_ready_for_aws.py`
Python script that:
- Reads the old CSV with outdated paths
- Searches for actual files in the filesystem
- Handles both `Books` and `Others\Books` subdirectories
- Generates updated CSV with correct normalized paths

### 2. `ready_for_aws_processing_updated.csv`
Updated CSV with:
- All 20 books found
- Correct normalized filenames (brackets → underscores, etc.)
- Correct file paths including `Others\Books` for Movie/TV books

### 3. `process-remaining-20-books-fixed.ps1`
Corrected batch processing script:
- Uses correct state machine ARN
- Uses updated CSV with correct paths
- Uploads each PDF to S3
- Starts Step Functions execution for each book
- Saves execution details to `remaining-20-executions.csv`

### 4. `test-one-book.ps1`
Single book test script:
- Tests with Steely Dan - The Best
- Verifies AWS credentials
- Uploads to S3
- Starts execution
- Provides monitoring command

## The 20 Books to Process

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
18. Steely Dan - The Best (Steely Dan)
19. Tom Waits - Tom Waits Anthology (Tom Waits)
20. Various Artists - Ultimate 80s Songs (Various Artists)

## Usage

### Test with One Book First
```powershell
.\test-one-book.ps1
```

This will:
1. Process Steely Dan - The Best
2. Show you the execution ARN
3. Give you a monitoring command

### Monitor the Test Execution
```powershell
.\monitor-execution.ps1 -ExecutionArn '<arn-from-test>'
```

### Process All 20 Books
Once the test succeeds:
```powershell
.\process-remaining-20-books-fixed.ps1
```

This will:
1. Process all 20 books sequentially
2. Upload each to S3
3. Start Step Functions execution for each
4. Save execution details to `remaining-20-executions.csv`

### Monitor All Executions
```powershell
.\monitor-remaining-20.ps1
```

## Expected Results

After successful processing:
- 20 new folders in `ProcessedSongs` (one per book)
- Each folder contains individual song PDFs
- Total completion: 561/561 books (100%)

## Notes

- The script waits 500ms between executions to avoid throttling
- Each execution is named with timestamp for uniqueness
- All executions are logged to CSV for tracking
- The state machine typically takes 2-5 minutes per book
