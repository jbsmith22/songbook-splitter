# Download processed files for the remaining books

$ErrorActionPreference = "Continue"

if (-not (Test-Path "remaining-books-executions.csv")) {
    Write-Host "No executions file found. Run process-remaining-books.ps1 first." -ForegroundColor Red
    exit 1
}

$executions = Import-Csv "remaining-books-executions.csv"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Downloading Processed Files for Remaining Books" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$outputBucket = "jsmith-output"
$downloadedCount = 0
$failedCount = 0

foreach ($exec in $executions) {
    $artist = $exec.Artist
    $bookName = $exec.BookName
    
    Write-Host "Downloading: $artist - $bookName" -ForegroundColor Yellow
    
    # Construct S3 prefix for this book's output
    $s3Prefix = "songs/$artist/"
    
    # Local destination
    $localPath = "ProcessedSongs\$artist"
    
    # Ensure local directory exists
    if (-not (Test-Path $localPath)) {
        New-Item -ItemType Directory -Path $localPath -Force | Out-Null
    }
    
    # Download from S3
    try {
        $result = aws s3 sync "s3://$outputBucket/$s3Prefix" $localPath --profile default 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Downloaded to: $localPath" -ForegroundColor Green
            $downloadedCount++
        } else {
            Write-Host "  FAILED: $result" -ForegroundColor Red
            $failedCount++
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        $failedCount++
    }
    
    Write-Host ""
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Download Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Successfully downloaded: $downloadedCount" -ForegroundColor Green
Write-Host "Failed: $failedCount" -ForegroundColor Red
Write-Host ""
Write-Host "Files downloaded to: ProcessedSongs\" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
