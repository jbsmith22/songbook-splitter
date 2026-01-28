# Download Billy Joel results from S3

$books = @(
    "Anthology",
    "Fantasies--Delusions",
    "Glass-Houses",
    "Greatest-Hits",
    "Keyboard-Book"
)

$outputBase = "ProcessedSongs\Billy Joel"

# Create output directory if it doesn't exist
if (-not (Test-Path $outputBase)) {
    New-Item -ItemType Directory -Path $outputBase -Force | Out-Null
}

Write-Host "Downloading Billy Joel results from S3..." -ForegroundColor Cyan
Write-Host ""

$totalSongs = 0

foreach ($book in $books) {
    Write-Host "Downloading: $book" -ForegroundColor Yellow
    
    $s3Path = "s3://jsmith-output/SheetMusicOut/Billy_Joel/books/$book/"
    
    # Check if path exists
    $files = aws s3 ls $s3Path --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        # Count files
        $fileCount = ($files | Measure-Object).Count
        $totalSongs += $fileCount
        
        Write-Host "  Found $fileCount files" -ForegroundColor Green
        
        # Download files
        aws s3 cp $s3Path $outputBase --recursive --profile default --quiet
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Downloaded successfully" -ForegroundColor Green
        } else {
            Write-Host "  ERROR downloading files" -ForegroundColor Red
        }
    } else {
        Write-Host "  No files found at $s3Path" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "================================================================================"
Write-Host "Download complete: $totalSongs total songs downloaded"
Write-Host "================================================================================"
