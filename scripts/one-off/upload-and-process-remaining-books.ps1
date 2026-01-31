# Upload remaining books to S3 and process them

$ErrorActionPreference = "Stop"

$booksToProcess = Import-Csv "books-with-no-folders.csv"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Upload and Process Remaining Books" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Books to process: $($booksToProcess.Count)" -ForegroundColor Yellow
Write-Host ""

$inputBucket = "jsmith-input"
$outputBucket = "jsmith-output"
$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

$executionArns = @()
$uploadedCount = 0
$processedCount = 0
$failCount = 0

foreach ($book in $booksToProcess) {
    $artist = $book.Artist
    $bookName = $book.SourceBook
    $sourcePath = $book.SourcePath
    
    Write-Host "Processing: $artist - $bookName" -ForegroundColor Yellow
    
    # Check if source file exists
    if (-not (Test-Path $sourcePath)) {
        Write-Host "  ERROR: Source file not found: $sourcePath" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    $fileName = Split-Path $sourcePath -Leaf
    $s3Key = "books/$artist/$fileName"
    
    Write-Host "  Uploading to S3: $s3Key"
    
    # Upload to S3
    try {
        $uploadResult = aws s3 cp $sourcePath "s3://$inputBucket/$s3Key" --profile default 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  FAILED to upload: $uploadResult" -ForegroundColor Red
            $failCount++
            Write-Host ""
            continue
        }
        
        Write-Host "  Uploaded successfully" -ForegroundColor Green
        $uploadedCount++
    } catch {
        Write-Host "  ERROR uploading: $_" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    # Start execution
    $executionInput = @{
        input_bucket = $inputBucket
        output_bucket = $outputBucket
        s3_key = $s3Key
        artist = $artist
    }
    
    # Save to temp file
    $tempFile = "temp-execution-input-$timestamp.json"
    $executionInput | ConvertTo-Json | Out-File -FilePath $tempFile -Encoding ASCII -NoNewline
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $sanitizedName = ($bookName -replace '[^a-zA-Z0-9-]', '-').ToLower()
    $executionName = "remaining-$sanitizedName-$timestamp"
    
    try {
        $result = aws stepfunctions start-execution `
            --state-machine-arn $stateMachineArn `
            --name $executionName `
            --input file://$tempFile `
            --profile default `
            2>&1
        
        # Clean up temp file
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            $executionArn = ($result | ConvertFrom-Json).executionArn
            $executionArns += [PSCustomObject]@{
                Artist = $artist
                BookName = $bookName
                ExecutionArn = $executionArn
                ExecutionName = $executionName
                S3Key = $s3Key
            }
            Write-Host "  Started execution: $executionName" -ForegroundColor Green
            $processedCount++
        } else {
            Write-Host "  FAILED to start execution: $result" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ERROR starting execution: $_" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Uploaded: $uploadedCount" -ForegroundColor Green
Write-Host "Executions started: $processedCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($executionArns.Count -gt 0) {
    $executionArns | Export-Csv "remaining-books-executions.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Execution details saved to: remaining-books-executions.csv" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor progress with:" -ForegroundColor Yellow
    Write-Host "  .\monitor-remaining-books.ps1" -ForegroundColor White
}

Write-Host "================================================================================" -ForegroundColor Cyan
