# Download newly processed Billy Joel songs

$books = @(
    @{Name="Anthology"; Folder="Billy Joel - Anthology"},
    @{Name="Fantasies & Delusions"; Folder="Billy Joel - Fantasies & Delusions"},
    @{Name="Glass Houses"; Folder="Billy Joel - Glass Houses"},
    @{Name="Greatest Hits"; Folder="Billy Joel - Greatest Hits"},
    @{Name="Keyboard Book"; Folder="Billy Joel - Keyboard Book"}
)

$outputBase = "ProcessedSongs\Billy Joel"

Write-Host "Downloading newly processed Billy Joel songs..." -ForegroundColor Cyan
Write-Host ""

$totalSongs = 0

foreach ($book in $books) {
    Write-Host "Downloading: $($book.Name)" -ForegroundColor Yellow
    
    $s3Path = "s3://jsmith-output/Billy Joel/$($book.Folder)/Songs/"
    $localPath = "$outputBase"
    
    # Download files
    aws s3 cp $s3Path $localPath --recursive --profile default --quiet
    
    if ($LASTEXITCODE -eq 0) {
        $count = (Get-ChildItem $localPath -Filter "*.pdf" -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-30) }).Count
        $totalSongs += $count
        Write-Host "  Downloaded $count songs" -ForegroundColor Green
    } else {
        Write-Host "  ERROR downloading files" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "================================================================================"
Write-Host "Download complete: $totalSongs total songs downloaded"
Write-Host "================================================================================"
