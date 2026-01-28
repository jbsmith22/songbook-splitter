# Process found books using the CSV with actual paths

$ErrorActionPreference = "Stop"

$booksToProcess = Import-Csv "found-missing-books.csv"

# Add America manually
$americaBook = [PSCustomObject]@{
    Artist = "America"
    BookName = "America - Greatest Hits [Book]"
    ActualPath = "C:\Work\AWSMusic\SheetMusic\America\Books\America - Greatest Hits [Book] .pdf"
    ActualName = "America - Greatest Hits [Book] .pdf"
}

$allBooks = @($americaBook) + $booksToProcess

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Process Found Missing Books from CSV" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Books to process: $($allBooks.Count)" -ForegroundColor Yellow
Write-Host ""

$inputBucket = "jsmith-input"
$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

$executionArns = @()
$uploadedCount = 0
$processedCount = 0
$failCount = 0

foreach ($book in $allBooks) {
    $artist = $book.Artist
    $bookName = $book.BookName
    $sourcePath = $book.ActualPath
    
    Write-Host "Processing: $artist - $bookName" -ForegroundColor Yellow
    
    # Check if source file exists
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        Write-Host "  ERROR: Source file not found: $sourcePath" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    $fileName = [System.IO.Path]::GetFileName($sourcePath)
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
    $executionName = "found-$sanitizedName-$timestamp"
    
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
                BookId = $bookId
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
    $executionArns | Export-Csv "found-books-executions.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Execution details saved to: found-books-executions.csv" -ForegroundColor Cyan
}

Write-Host "================================================================================" -ForegroundColor Cyan
