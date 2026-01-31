# Processing Remaining 20 Books

This guide explains how to process the 20 remaining unprocessed books through the AWS Step Functions pipeline.

## Prerequisites

1. AWS credentials configured: `aws sso login --profile default`
2. The 20 PDFs are in the `SheetMusic` folder
3. The `ready_for_aws_processing.csv` file exists

## Step 1: Process the Books

Run the processing script to upload PDFs to S3 and start Step Functions executions:

```powershell
.\process-remaining-20-books.ps1
```

This script will:
- Upload each PDF to S3 (`s3://jsmith-input/SheetMusic/...`)
- Start a Step Functions execution for each book
- Save execution details to `remaining-20-executions.csv`

**Expected time**: ~2-3 minutes to start all executions

## Step 2: Monitor Progress

Monitor the execution status:

```powershell
.\monitor-remaining-20.ps1
```

This shows:
- Current status of each execution (RUNNING, SUCCEEDED, FAILED)
- Progress summary
- Failed executions (if any)

**Tip**: Auto-refresh every 30 seconds:
```powershell
while ($true) { cls; .\monitor-remaining-20.ps1; Start-Sleep -Seconds 30 }
```

**Expected processing time**: 
- Simple books (10-20 songs): 5-10 minutes
- Complex books (50+ songs): 15-30 minutes
- Total for all 20: 2-4 hours

## Step 3: Download Results

Once executions are complete, download the processed songs:

```powershell
.\download-remaining-20-results.ps1
```

This script will:
- Check each execution status
- Download successful results from S3
- Save to `ProcessedSongs/{Artist}/{BookName}/`

## The 20 Books Being Processed

1. Various Artists - 25th Annual Putnam County Spelling Bee
2. Various Artists - High School Musical [score]
3. Various Artists - Little Shop Of Horrors (Broadway)
4. Various Artists - Little Shop of Horrors Script
5. Various Artists - Shrek The Musical
6. Various Artists - You're A Good Man Charlie Brown (Score)
7. Wicked Workshop
8. The Wizard Of Oz Script
9. Various Artists - Complete TV and Film
10. Crosby, Stills, Nash & Young - The Guitar Collection
11. Dire Straits - Mark Knopfler Guitar Styles Vol 1
12. Elvis Presley - The Compleat
13. Eric Clapton - The Cream of Clapton
14. John Denver - Back Home Again
15. Mamas and The Papas - Songbook
16. Night Ranger - Seven Wishes
17. Robbie Robertson - Songbook
18. Steely Dan - The Best
19. Tom Waits - Tom Waits Anthology
20. Various Artists - Ultimate 80s Songs

## Files Generated

- `remaining-20-executions.csv` - Execution ARNs and details
- `remaining-20-status.csv` - Current status of each execution

## Troubleshooting

### AWS Credentials Expired
```powershell
aws sso login --profile default
```

### Check Individual Execution
```powershell
aws stepfunctions describe-execution --execution-arn <ARN> --profile default
```

### View Execution History
```powershell
aws stepfunctions get-execution-history --execution-arn <ARN> --profile default
```

### Check S3 Output
```powershell
aws s3 ls s3://jsmith-output/s3://jsmith-output/SheetMusicOut/ --recursive --profile default
```

## After Processing

Once all 20 books are processed:

1. Verify folder structure matches PDF names
2. Check song counts in each folder
3. Update project completion status to 100%!

## Expected Final State

- **Total PDFs**: 561
- **Processed**: 561 (100%)
- **Unprocessed**: 0
- **Completion**: 100%! 🎉
