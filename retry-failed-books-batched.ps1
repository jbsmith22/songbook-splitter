# Retry failed books in batches of 10 to avoid rate limiting

$ErrorActionPreference = "Stop"

if (-not (Test-Path "failed-books-no-output.csv")) {
    Write-Host "ERROR: failed-books-no-output.csv not found" -ForegroundColor Red
    Write-Host "Run identify-failed-books.ps1 first" -ForegroundColor Yellow
    exit 1
}

$failedBooks = Import-Csv "failed-books-no-output.csv"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Retry Failed Books (Batched)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total failed books: $($failedBooks.Count)" -ForegroundColor Yellow
Write-Host "Processing in batches of 10 with 30 second delays between batches" -ForegroundColor Yellow
Write-Host ""

$inputBucket = "jsmith-input"
$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

$batchSize = 10
$batchDelay = 30  # seconds between batches
$executionDelay = 2  # seconds between executions within a batch

$allExecutions = @()
$processedCount = 0
$failCount = 0
$batchNumber = 0

for ($i = 0; $i -lt $failedBooks.Count; $i += $batchSize) {
    $batchNumber++
    $batch = $failedBooks[$i..[Math]::Min($i + $batchSize - 1, $failedBooks.Count - 1)]
    
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Batch $batchNumber - Processing $($batch.Count) books" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($book in $batch) {
        $artist = $book.Artist
        $bookName = $book.BookName
        $s3Key = $book.S3Key
        
        Write-Host "Processing: $artist - $bookName" -ForegroundColor Yellow
        
        # Generate book_id (SHA256 hash of S3 URI, first 16 chars)
        $s3Uri = "s3://$inputBucket/$s3Key"
        $sha256 = [System.Security.Cryptography.SHA256]::Create()
        $hashBytes = $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($s3Uri))
        $hashString = [System.BitConverter]::ToString($hashBytes).Replace("-", "").ToLower()
        $bookId = $hashString.Substring(0, 16)
        
        # Start execution with CORRECT input format
        $executionInput = @{
            book_id = $bookId
            source_pdf_uri = $s3Uri
            bucket = $inputBucket
            key = $s3Key
            artist = $artist
            book_name = $bookName
        }
        
        # Save to temp file
        $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
        $tempFile = "temp-execution-input-$timestamp.json"
        $executionInput | ConvertTo-Json | Out-File -FilePath $tempFile -Encoding ASCII -NoNewline
        
        $sanitizedName = ($bookName -replace '[^a-zA-Z0-9-]', '-').ToLower()
        $executionName = "retry-$sanitizedName-$timestamp"
        
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
                $allExecutions += [PSCustomObject]@{
                    Artist = $artist
                    BookName = $bookName
                    ExecutionArn = $executionArn
                    ExecutionName = $executionName
                    S3Key = $s3Key
                    BookId = $bookId
                    Batch = $batchNumber
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
        
        # Small delay between executions within batch
        Start-Sleep -Seconds $executionDelay
    }
    
    Write-Host ""
    
    # Delay between batches (except after last batch)
    if ($i + $batchSize -lt $failedBooks.Count) {
        Write-Host "Waiting $batchDelay seconds before next batch..." -ForegroundColor Yellow
        Write-Host ""
        Start-Sleep -Seconds $batchDelay
    }
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Batches processed: $batchNumber" -ForegroundColor Cyan
Write-Host "Executions started: $processedCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($allExecutions.Count -gt 0) {
    $allExecutions | Export-Csv "retry-failed-books-executions.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Execution details saved to: retry-failed-books-executions.csv" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Monitor progress with:" -ForegroundColor Yellow
    Write-Host "  .\monitor-all-new-executions.ps1" -ForegroundColor White
}

Write-Host "================================================================================" -ForegroundColor Cyan
