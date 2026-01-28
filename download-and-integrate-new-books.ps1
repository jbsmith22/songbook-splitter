# Download and integrate results from new executions

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

if ($allExecutions.Count -eq 0) {
    Write-Host "No executions found" -ForegroundColor Red
    exit 1
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Download and Integrate New Books" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$s3Bucket = "jsmith-output"
$localBase = "C:\Work\AWSMusic\ProcessedSongs"

$downloadedCount = 0
$failedCount = 0
$skippedCount = 0

foreach ($exec in $allExecutions) {
    # Check execution status
    $status = aws stepfunctions describe-execution `
        --execution-arn $exec.ExecutionArn `
        --profile default `
        --query 'status' `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$($exec.Artist) - $($exec.BookName): ERROR querying status" -ForegroundColor Red
        $failedCount++
        continue
    }
    
    if ($status -ne "SUCCEEDED") {
        Write-Host "$($exec.Artist) - $($exec.BookName): $status (skipping)" -ForegroundColor Yellow
        $skippedCount++
        continue
    }
    
    Write-Host "$($exec.Artist) - $($exec.BookName): SUCCEEDED - Downloading..." -ForegroundColor Green
    
    # Construct S3 path - the output goes to <Artist>/<BookName>/Songs/
    $s3Path = "$($exec.Artist)/$($exec.BookName)/Songs/"
    
    # Check if path exists
    $checkResult = aws s3 ls "s3://$s3Bucket/$s3Path" --profile default 2>&1
    if ($LASTEXITCODE -ne 0 -or -not $checkResult) {
        Write-Host "  ERROR: Could not find S3 output path: $s3Path" -ForegroundColor Red
        $failedCount++
        continue
    }
    
    # Create local directory
    $localDir = Join-Path $localBase $exec.Artist
    $localBookDir = Join-Path $localDir $exec.BookName
    
    if (-not (Test-Path $localDir)) {
        [System.IO.Directory]::CreateDirectory($localDir) | Out-Null
    }
    
    if (-not (Test-Path $localBookDir)) {
        [System.IO.Directory]::CreateDirectory($localBookDir) | Out-Null
    }
    
    # Download from S3
    Write-Host "  Downloading from: s3://$s3Bucket/$s3Path" -ForegroundColor Gray
    Write-Host "  To: $localBookDir" -ForegroundColor Gray
    
    $downloadResult = aws s3 sync "s3://$s3Bucket/$s3Path" $localBookDir --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Downloaded successfully" -ForegroundColor Green
        $downloadedCount++
    } else {
        Write-Host "  ERROR downloading: $downloadResult" -ForegroundColor Red
        $failedCount++
    }
    
    Write-Host ""
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Downloaded: $downloadedCount" -ForegroundColor Green
Write-Host "Skipped (not finished): $skippedCount" -ForegroundColor Yellow
Write-Host "Failed: $failedCount" -ForegroundColor Red
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
