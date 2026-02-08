# Batch Processing Scripts

These PowerShell scripts allow you to process all your sheet music books overnight without using Kiro tokens.

## Scripts Overview

### 1. `process-all-books.ps1`
Scans local SheetMusic directory, uploads PDFs to S3, and submits Step Functions executions.

### 2. `download-all-songs.ps1`
Downloads all processed songs from S3 to local directories.

### 3. `process-and-download-all.ps1` (RECOMMENDED)
Master script that runs both processing and downloading in sequence.

## Quick Start - Overnight Processing

Run this command in PowerShell and let it run overnight:

```powershell
.\process-and-download-all.ps1
```

This will:
1. Upload all PDFs from `.\SheetMusic\` to S3
2. Submit processing jobs (max 3 concurrent)
3. Wait for all jobs to complete
4. Download all processed songs to `.\ProcessedSongs\`

## Advanced Usage

### Process Only (No Download)
```powershell
.\process-and-download-all.ps1 -ProcessOnly
```

### Download Only (Skip Processing)
```powershell
.\process-and-download-all.ps1 -DownloadOnly
```

### Custom Directories
```powershell
.\process-and-download-all.ps1 -SheetMusicDir "D:\MyMusic" -OutputDir "D:\Processed"
```

### Dry Run (Test Without Changes)
```powershell
.\process-and-download-all.ps1 -DryRun
```

### Adjust Concurrency
```powershell
.\process-and-download-all.ps1 -MaxConcurrent 5
```

## Individual Script Usage

### Process Books Only
```powershell
# Basic usage
.\process-all-books.ps1

# With options
.\process-all-books.ps1 -MaxConcurrent 5 -DryRun
```

### Download Songs Only
```powershell
# Basic usage
.\download-all-songs.ps1

# Skip files that already exist locally
.\download-all-songs.ps1 -SkipExisting

# Custom output directory
.\download-all-songs.ps1 -LocalOutputDir "D:\MySongs"
```

## Expected Directory Structure

### Input (Local)
```
SheetMusic/
├── Billy Joel/
│   └── Books/
│       ├── Billy Joel - Glass Houses.pdf
│       └── Billy Joel - Piano Man.pdf
├── Various Artists/
│   └── Books/
│       └── Various Artists - Great Bands Of The 70s.pdf
└── ...
```

### Output (Local)
```
ProcessedSongs/
├── Billy Joel/
│   ├── Glass Houses/
│   │   └── Songs/
│   │       ├── Billy Joel - Glass Houses.pdf
│   │       └── Billy Joel - You May Be Right.pdf
│   └── Piano Man/
│       └── Songs/
│           └── Billy Joel - Piano Man.pdf
├── Various Artists/
│   └── Great Bands Of The 70s/
│       └── Songs/
│           ├── Abba - Knowing Me, Knowing You.pdf
│           ├── Blondie - Heart Of Glass.pdf
│           └── ...
└── ...
```

## Monitoring Progress

### Check Running Executions
```powershell
aws stepfunctions list-executions `
    --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
    --status-filter RUNNING `
    --region us-east-1
```

### Check Failed Executions
```powershell
aws stepfunctions list-executions `
    --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
    --status-filter FAILED `
    --region us-east-1
```

### View CloudWatch Logs
```powershell
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --follow --region us-east-1
```

## Log Files

Each script creates a timestamped log file:
- `process-all-books-YYYYMMDD-HHMMSS.log`
- `download-all-songs-YYYYMMDD-HHMMSS.log`
- `master-process-YYYYMMDD-HHMMSS.log`

## Deduplication

The system automatically prevents reprocessing of books that have already been successfully processed. If you need to reprocess a book:

1. Delete the DynamoDB record, OR
2. Use a different book_id in the input

## Cost Considerations

- **S3 Storage**: ~$0.023 per GB/month
- **Step Functions**: $0.025 per 1,000 state transitions
- **ECS Fargate**: ~$0.04 per vCPU-hour + $0.004 per GB-hour
- **Bedrock Vision**: ~$0.003 per image

Estimated cost per book: $0.10 - $0.50 depending on size and complexity

## Troubleshooting

### Script Won't Run
```powershell
# Enable script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### AWS Credentials Not Found
```powershell
# Configure AWS CLI
aws configure
```

### Too Many Concurrent Executions
Reduce the `-MaxConcurrent` parameter:
```powershell
.\process-and-download-all.ps1 -MaxConcurrent 2
```

### Execution Failed
Check CloudWatch logs for the specific execution:
```powershell
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 1h --region us-east-1
```

## Tips for Overnight Processing

1. **Test First**: Run with `-DryRun` to verify everything is configured correctly
2. **Start Small**: Process a few books first to ensure it works
3. **Monitor Initially**: Watch the first few executions to catch any issues
4. **Check Logs**: Review log files in the morning to see what happened
5. **Verify Results**: Spot-check downloaded files to ensure quality

## Example: Full Overnight Run

```powershell
# 1. Test with dry run
.\process-and-download-all.ps1 -DryRun

# 2. Start the actual processing
.\process-and-download-all.ps1 -MaxConcurrent 3

# 3. Go to bed! The script will:
#    - Upload all PDFs
#    - Process them (respecting concurrency limits)
#    - Wait for completion
#    - Download all results
#    - Create a log file with summary

# 4. In the morning, check:
#    - Log file for summary
#    - ProcessedSongs directory for results
#    - Failed executions (if any)
```
