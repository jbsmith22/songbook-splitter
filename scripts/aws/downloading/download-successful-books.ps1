# Download and integrate the 6 books that succeeded from the original batch

Write-Host "================================================================================"
Write-Host "DOWNLOADING SUCCESSFUL BOOKS FROM ORIGINAL BATCH"
Write-Host "================================================================================"
Write-Host ""

# Books that succeeded: Shrek, Wicked Workshop, Charlie Brown, High School Musical, Little Shop Broadway, Tom Waits
$patterns = @(
    "Shrek"
    "Wicked"
    "Charlie Brown"
    "High School"
    "Little Shop"
    "Tom Waits"
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = "download-successful-$timestamp.log"

Write-Host "Finding files in S3..." | Tee-Object -FilePath $logFile
Write-Host ""

$filesToDownload = @()

foreach ($pattern in $patterns) {
    Write-Host "Searching for: $pattern" | Tee-Object -FilePath $logFile -Append
    
    $files = aws s3 ls s3://jsmith-output/ --recursive | 
        Select-String "2026-01-2[78]" | 
        Select-String "\.pdf$" | 
        Select-String $pattern
    
    if ($files) {
        $count = ($files | Measure-Object).Count
        Write-Host "  Found $count files" -ForegroundColor Green | Tee-Object -FilePath $logFile -Append
        $filesToDownload += $files
    } else {
        Write-Host "  No files found" -ForegroundColor Yellow | Tee-Object -FilePath $logFile -Append
    }
}

Write-Host ""
Write-Host "Total files to download: $($filesToDownload.Count)" | Tee-Object -FilePath $logFile -Append
Write-Host ""

if ($filesToDownload.Count -eq 0) {
    Write-Host "No files to download. Exiting." -ForegroundColor Yellow
    exit 0
}

Write-Host "Downloading files..." | Tee-Object -FilePath $logFile -Append
Write-Host ""

$downloadedCount = 0
$errorCount = 0

foreach ($file in $filesToDownload) {
    # Parse the S3 path from the ls output
    # Format: "2026-01-29 21:44:45     399384 Night Ranger/Night Ranger - Seven Wishes..."
    $parts = $file -split '\s+', 4
    if ($parts.Count -lt 4) {
        continue
    }
    
    $s3Path = $parts[3].Trim()
    $s3Uri = "s3://jsmith-output/$s3Path"
    
    # Determine local path
    # S3 path format: Artist/BookName/Songs/Artist - SongTitle.pdf
    # Local path format: ProcessedSongs\Artist\BookName\Artist - SongTitle.pdf
    
    $pathParts = $s3Path -split '/', 4
    if ($pathParts.Count -lt 4) {
        Write-Host "  Skipping invalid path: $s3Path" -ForegroundColor Yellow | Tee-Object -FilePath $logFile -Append
        continue
    }
    
    $artist = $pathParts[0]
    $bookName = $pathParts[1]
    $fileName = $pathParts[3]
    
    $localDir = "ProcessedSongs\$artist\$bookName"
    $localPath = "$localDir\$fileName"
    
    # Create directory if it doesn't exist
    if (-not (Test-Path $localDir)) {
        [System.IO.Directory]::CreateDirectory($localDir) | Out-Null
    }
    
    # Download file
    try {
        aws s3 cp $s3Uri $localPath --quiet
        
        if ($LASTEXITCODE -eq 0) {
            $downloadedCount++
            if ($downloadedCount % 10 -eq 0) {
                Write-Host "  Downloaded $downloadedCount files..." -ForegroundColor Green
            }
        } else {
            Write-Host "  ERROR downloading: $s3Path" -ForegroundColor Red | Tee-Object -FilePath $logFile -Append
            $errorCount++
        }
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red | Tee-Object -FilePath $logFile -Append
        $errorCount++
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "DOWNLOAD COMPLETE"
Write-Host "================================================================================"
Write-Host "Downloaded: $downloadedCount files" -ForegroundColor Green
Write-Host "Errors: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { "Red" } else { "Green" })
Write-Host "Log file: $logFile"
Write-Host ""
