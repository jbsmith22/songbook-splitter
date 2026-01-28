# Process the remaining 34 books through AWS pipeline

$ErrorActionPreference = "Stop"

# Load the list of books with no folders
$booksToProcess = Import-Csv "books-with-no-folders.csv"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Processing Remaining Books Through AWS Pipeline" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Books to process: $($booksToProcess.Count)" -ForegroundColor Yellow
Write-Host ""

# AWS Configuration
$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$inputBucket = "jsmith-input"
$outputBucket = "jsmith-output"

# Process each book
$executionArns = @()
$successCount = 0
$failCount = 0

foreach ($book in $booksToProcess) {
    $artist = $book.Artist
    $bookName = $book.SourceBook
    $sourcePath = $book.SourcePath
    
    # Extract just the filename
    $fileName = Split-Path $sourcePath -Leaf
    
    # Construct S3 key (books/Artist/filename)
    $s3Key = "books/$artist/$fileName"
    
    Write-Host "Processing: $artist - $bookName" -ForegroundColor Yellow
    Write-Host "  Source: $sourcePath"
    Write-Host "  S3 Key: $s3Key"
    
    # Create execution input
    $executionInput = @{
        input_bucket = $inputBucket
        output_bucket = $outputBucket
        s3_key = $s3Key
        artist = $artist
    } | ConvertTo-Json -Compress
    
    # Generate execution name (must be unique)
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $sanitizedName = ($bookName -replace '[^a-zA-Z0-9-]', '-').ToLower()
    $executionName = "process-$sanitizedName-$timestamp"
    
    # Start execution
    try {
        $result = aws stepfunctions start-execution `
            --state-machine-arn $stateMachineArn `
            --name $executionName `
            --input $executionInput `
            --profile default `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $executionArn = ($result | ConvertFrom-Json).executionArn
            $executionArns += [PSCustomObject]@{
                Artist = $artist
                BookName = $bookName
                ExecutionArn = $executionArn
                ExecutionName = $executionName
            }
            Write-Host "  Started: $executionName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  FAILED to start: $result" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
    
    # Small delay to avoid throttling
    Start-Sleep -Milliseconds 500
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Execution Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Successfully started: $successCount" -ForegroundColor Green
Write-Host "Failed to start: $failCount" -ForegroundColor Red
Write-Host ""

if ($executionArns.Count -gt 0) {
    # Save execution details
    $executionArns | Export-Csv "remaining-books-executions.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Execution details saved to: remaining-books-executions.csv" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor progress with:" -ForegroundColor Yellow
    Write-Host "  .\monitor-remaining-books.ps1" -ForegroundColor White
}

Write-Host "================================================================================" -ForegroundColor Cyan
