# Check for books that are in S3 but missing locally

Write-Host "Checking for missing books..." -ForegroundColor Cyan
Write-Host ""

# Get all book folders from S3
$s3Books = aws s3 ls "s3://jsmith-output/" --profile default | Where-Object { $_ -match "PRE " } | ForEach-Object { $_ -replace ".*PRE ", "" -replace "/", "" } | Sort-Object

Write-Host "Found $($s3Books.Count) artist folders in S3" -ForegroundColor Yellow
Write-Host ""

# Get all local artist folders
$localArtists = Get-ChildItem "ProcessedSongs" -Directory | Select-Object -ExpandProperty Name | Sort-Object

Write-Host "Found $($localArtists.Count) artist folders locally" -ForegroundColor Yellow
Write-Host ""

# Compare
$missingArtists = $s3Books | Where-Object { $_ -notin $localArtists }

if ($missingArtists) {
    Write-Host "Missing artist folders:" -ForegroundColor Red
    $missingArtists | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
} else {
    Write-Host "All artist folders present locally" -ForegroundColor Green
}

Write-Host ""
Write-Host "Checking for missing books within each artist..." -ForegroundColor Cyan
Write-Host ""

$totalMissing = 0

foreach ($artist in $localArtists) {
    # Get S3 books for this artist
    $s3ArtistBooks = aws s3 ls "s3://jsmith-output/$artist/" --profile default --recursive | Where-Object { $_ -match "Songs/" } | ForEach-Object { 
        if ($_ -match "$artist/([^/]+)/Songs/") {
            $matches[1]
        }
    } | Select-Object -Unique | Sort-Object
    
    if (-not $s3ArtistBooks) { continue }
    
    # Get local books for this artist
    $localBooks = Get-ChildItem "ProcessedSongs\$artist" -Directory | Select-Object -ExpandProperty Name | Sort-Object
    
    # Find missing
    $missing = $s3ArtistBooks | Where-Object { $_ -notin $localBooks }
    
    if ($missing) {
        Write-Host "$artist - Missing $($missing.Count) books:" -ForegroundColor Yellow
        $missing | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
        $totalMissing += $missing.Count
        Write-Host ""
    }
}

Write-Host "================================================================================"
Write-Host "Total missing books: $totalMissing"
Write-Host "================================================================================"
