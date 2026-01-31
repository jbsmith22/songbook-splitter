# Restore Billy Joel folder structure by downloading from S3 into proper subfolders

$books = @(
    @{Name="Anthology"; S3Folder="Billy Joel - Anthology"; LocalFolder="Anthology"},
    @{Name="Fantasies & Delusions"; S3Folder="Billy Joel - Fantasies & Delusions"; LocalFolder="Fantasies & Delusions"},
    @{Name="Glass Houses"; S3Folder="Billy Joel - Glass Houses"; LocalFolder="Glass Houses"},
    @{Name="Greatest Hits"; S3Folder="Billy Joel - Greatest Hits"; LocalFolder="Greatest Hits"},
    @{Name="Keyboard Book"; S3Folder="Billy Joel - Keyboard Book"; LocalFolder="Keyboard Book"}
)

$baseLocal = "ProcessedSongs\Billy Joel"

Write-Host "Restoring Billy Joel folder structure from S3..." -ForegroundColor Cyan
Write-Host ""

foreach ($book in $books) {
    Write-Host "Downloading: $($book.Name)" -ForegroundColor Yellow
    
    $s3Path = "s3://jsmith-output/Billy Joel/$($book.S3Folder)/Songs/"
    $localPath = "$baseLocal\$($book.LocalFolder)"
    
    # Create local folder if it doesn't exist
    if (-not (Test-Path $localPath)) {
        New-Item -ItemType Directory -Path $localPath -Force | Out-Null
    }
    
    # Download files
    $result = aws s3 cp $s3Path $localPath --recursive --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $count = (Get-ChildItem $localPath -Filter "*.pdf" | Measure-Object).Count
        Write-Host "  Downloaded $count songs to $($book.LocalFolder)" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: $result" -ForegroundColor Red
    }
    
    Write-Host ""
}

Write-Host "================================================================================"
Write-Host "Restore complete"
Write-Host "================================================================================"
