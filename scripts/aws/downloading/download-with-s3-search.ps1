# Download books by searching S3 directly for matches

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
Write-Host "Download Books with S3 Search" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$s3Bucket = "jsmith-output"
$localBase = "C:\Work\AWSMusic\ProcessedSongs"

$downloadedCount = 0
$alreadyDownloaded = 0
$notFound = 0
$skipped = 0

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
        $skipped++
        continue
    }
    
    Write-Host "Checking: $($exec.Artist) - $($exec.BookName)" -ForegroundColor Yellow
    
    # List all folders under the artist in S3
    $artistFolders = aws s3 ls "s3://$s3Bucket/$($exec.Artist)/" --profile default 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Artist folder not found in S3" -ForegroundColor Red
        $notFound++
        continue
    }
    
    # Find matching book folder (case-insensitive)
    $bookNameLower = $exec.BookName.ToLower()
    $matchedFolder = $null
    
    foreach ($line in $artistFolders) {
        if ($line -match 'PRE (.+)/') {
            $folderName = $matches[1]
            if ($folderName.ToLower() -eq $bookNameLower) {
                $matchedFolder = $folderName
                break
            }
        }
    }
    
    if (-not $matchedFolder) {
        Write-Host "  Book folder not found in S3" -ForegroundColor Red
        $notFound++
        continue
    }
    
    # Check if Songs subfolder exists
    $s3Path = "$($exec.Artist)/$matchedFolder/Songs/"
    $songsCheck = aws s3 ls "s3://$s3Bucket/$s3Path" --profile default 2>&1
    
    if ($LASTEXITCODE -ne 0 -or -not $songsCheck) {
        Write-Host "  No Songs folder found" -ForegroundColor Red
        $notFound++
        continue
    }
    
    # Check if already downloaded
    $localDir = Join-Path $localBase $exec.Artist
    $localBookDir = Join-Path $localDir $exec.BookName
    
    if (Test-Path $localBookDir) {
        $existingFiles = Get-ChildItem $localBookDir -File -ErrorAction SilentlyContinue
        if ($existingFiles -and $existingFiles.Count -gt 0) {
            Write-Host "  Already downloaded" -ForegroundColor Cyan
            $alreadyDownloaded++
            continue
        }
    }
    
    # Download
    Write-Host "  Downloading from: s3://$s3Bucket/$s3Path" -ForegroundColor Green
    
    if (-not (Test-Path $localDir)) {
        [System.IO.Directory]::CreateDirectory($localDir) | Out-Null
    }
    
    if (-not (Test-Path $localBookDir)) {
        [System.IO.Directory]::CreateDirectory($localBookDir) | Out-Null
    }
    
    $downloadResult = aws s3 sync "s3://$s3Bucket/$s3Path" $localBookDir --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Downloaded successfully" -ForegroundColor Green
        $downloadedCount++
    } else {
        Write-Host "  ERROR downloading" -ForegroundColor Red
        $notFound++
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Downloaded: $downloadedCount" -ForegroundColor Green
Write-Host "Already downloaded: $alreadyDownloaded" -ForegroundColor Cyan
Write-Host "Not found in S3: $notFound" -ForegroundColor Red
Write-Host "Skipped (not finished): $skipped" -ForegroundColor Yellow
Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
