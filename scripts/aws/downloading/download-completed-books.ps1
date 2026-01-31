# Download all completed books that have S3 output

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
Write-Host "Download Completed Books" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$s3Bucket = "jsmith-output"
$localBase = "C:\Work\AWSMusic\ProcessedSongs"

$downloadedCount = 0
$failedCount = 0
$skippedCount = 0
$alreadyDownloaded = 0

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
        $skippedCount++
        continue
    }
    
    # Check if S3 output exists
    $s3Path = "$($exec.Artist)/$($exec.BookName)/Songs/"
    $checkResult = aws s3 ls "s3://$s3Bucket/$s3Path" --profile default 2>&1
    
    if ($LASTEXITCODE -ne 0 -or -not $checkResult) {
        # No output - failed during processing
        $failedCount++
        continue
    }
    
    # Create local directory
    $localDir = Join-Path $localBase $exec.Artist
    $localBookDir = Join-Path $localDir $exec.BookName
    
    # Check if already downloaded
    if (Test-Path $localBookDir) {
        $existingFiles = Get-ChildItem $localBookDir -File -ErrorAction SilentlyContinue
        if ($existingFiles -and $existingFiles.Count -gt 0) {
            $alreadyDownloaded++
            continue
        }
    }
    
    Write-Host "Downloading: $($exec.Artist) - $($exec.BookName)" -ForegroundColor Green
    
    if (-not (Test-Path $localDir)) {
        [System.IO.Directory]::CreateDirectory($localDir) | Out-Null
    }
    
    if (-not (Test-Path $localBookDir)) {
        [System.IO.Directory]::CreateDirectory($localBookDir) | Out-Null
    }
    
    # Download from S3
    $downloadResult = aws s3 sync "s3://$s3Bucket/$s3Path" $localBookDir --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Downloaded successfully" -ForegroundColor Green
        $downloadedCount++
    } else {
        Write-Host "  ERROR downloading: $downloadResult" -ForegroundColor Red
        $failedCount++
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Downloaded: $downloadedCount" -ForegroundColor Green
Write-Host "Already downloaded: $alreadyDownloaded" -ForegroundColor Cyan
Write-Host "Skipped (not finished): $skippedCount" -ForegroundColor Yellow
Write-Host "Failed (no output): $failedCount" -ForegroundColor Red
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
