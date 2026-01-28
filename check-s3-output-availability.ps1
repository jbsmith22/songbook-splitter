# Check which succeeded executions actually have S3 output available

$ErrorActionPreference = "Stop"

$allExecutions = @()

if (Test-Path "remaining-books-executions-corrected.csv") {
    $corrected = Import-Csv "remaining-books-executions-corrected.csv"
    $allExecutions += $corrected
}

if (Test-Path "found-books-executions.csv") {
    $found = Import-Csv "found-books-executions.csv"
    $allExecutions += $found
}

if (Test-Path "retry-failed-books-executions.csv") {
    $retry = Import-Csv "retry-failed-books-executions.csv"
    $allExecutions += $retry
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Check S3 Output Availability" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$s3Bucket = "jsmith-output"
$localBase = "C:\Work\AWSMusic\ProcessedSongs"

$availableInS3 = @()
$alreadyDownloaded = @()
$noOutput = @()
$stillRunning = @()

foreach ($exec in $allExecutions) {
    # Check execution status
    $status = aws stepfunctions describe-execution `
        --execution-arn $exec.ExecutionArn `
        --profile default `
        --query 'status' `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        continue
    }
    
    if ($status -ne "SUCCEEDED") {
        $stillRunning += $exec
        continue
    }
    
    # Try to find S3 output with case-insensitive artist name matching
    $artistVariations = @(
        $exec.Artist,
        (Get-Culture).TextInfo.ToTitleCase($exec.Artist.ToLower())
    )
    
    $foundInS3 = $false
    $actualS3Path = $null
    
    foreach ($artistVar in $artistVariations) {
        $s3Path = "$artistVar/$($exec.BookName)/Songs/"
        $checkResult = aws s3 ls "s3://$s3Bucket/$s3Path" --profile default 2>&1
        
        if ($LASTEXITCODE -eq 0 -and $checkResult) {
            $foundInS3 = $true
            $actualS3Path = $s3Path
            break
        }
    }
    
    if (-not $foundInS3) {
        $noOutput += $exec
        continue
    }
    
    # Check if already downloaded locally
    $localDir = Join-Path $localBase $exec.Artist
    $localBookDir = Join-Path $localDir $exec.BookName
    
    if (Test-Path $localBookDir) {
        $existingFiles = Get-ChildItem $localBookDir -File -ErrorAction SilentlyContinue
        if ($existingFiles -and $existingFiles.Count -gt 0) {
            $alreadyDownloaded += [PSCustomObject]@{
                Artist = $exec.Artist
                BookName = $exec.BookName
                S3Path = $actualS3Path
            }
            continue
        }
    }
    
    $availableInS3 += [PSCustomObject]@{
        Artist = $exec.Artist
        BookName = $exec.BookName
        S3Path = $actualS3Path
        ExecutionArn = $exec.ExecutionArn
    }
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Already downloaded: $($alreadyDownloaded.Count)" -ForegroundColor Green
Write-Host "Available in S3 (ready to download): $($availableInS3.Count)" -ForegroundColor Cyan
Write-Host "No output (failed during processing): $($noOutput.Count)" -ForegroundColor Red
Write-Host "Still running: $($stillRunning.Count)" -ForegroundColor Yellow
Write-Host ""

if ($alreadyDownloaded.Count -gt 0) {
    Write-Host "Already Downloaded:" -ForegroundColor Green
    foreach ($book in $alreadyDownloaded) {
        Write-Host "  - $($book.Artist) - $($book.BookName)" -ForegroundColor Green
    }
    Write-Host ""
}

if ($availableInS3.Count -gt 0) {
    Write-Host "Available to Download:" -ForegroundColor Cyan
    foreach ($book in $availableInS3) {
        Write-Host "  - $($book.Artist) - $($book.BookName)" -ForegroundColor Cyan
    }
    Write-Host ""
    
    $availableInS3 | Export-Csv "books-available-to-download.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Details saved to: books-available-to-download.csv" -ForegroundColor Cyan
    Write-Host ""
}

if ($noOutput.Count -gt 0) {
    Write-Host "No Output (Failed):" -ForegroundColor Red
    foreach ($book in $noOutput) {
        Write-Host "  - $($book.Artist) - $($book.BookName)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "================================================================================" -ForegroundColor Cyan
