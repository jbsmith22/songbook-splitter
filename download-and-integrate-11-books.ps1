# Download and integrate 11 books that have output files in S3
$books = @(
    @{Name="John Denver - Back Home Again"; S3Path="John Denver/Best Of [easy Piano]/Songs/"; LocalArtist="John Denver"; LocalBook="John Denver - Back Home Again"},
    @{Name="REO Speedwagon - Life As We Know It"; S3Path="Reo Speedwagon/Reo Speedwagon - Life As We Know It/Songs/"; LocalArtist="REO Speedwagon"; LocalBook="REO Speedwagon - Life As We Know It"},
    @{Name="Tom Waits - Tom Waits Anthology"; S3Path="Tom Waits/Tom Waits - Tom Waits Anthology/Songs/"; LocalArtist="Tom Waits"; LocalBook="Tom Waits - Tom Waits Anthology"},
    @{Name="Who - Quadrophenia (PVG)"; S3Path="Who/Who - Quadrophenia (pvg)/Songs/"; LocalArtist="Who"; LocalBook="Who - Quadrophenia (PVG)"},
    @{Name="Wings - London Town (PVG Book)"; S3Path="Wings/Wings - London Town (pvg Book)/Songs/"; LocalArtist="Wings"; LocalBook="Wings - London Town (PVG Book)"},
    @{Name="Wicked Workshop"; S3Path="_broadway Shows/Wicked Workshop/Songs/"; LocalArtist="_Broadway Shows"; LocalBook="Wicked Workshop"},
    @{Name="The Wizard of Oz Script"; S3Path="_broadway Shows/Various Artists - Wizard Of Oz (rsc Piano-conductor)/Songs/"; LocalArtist="_Movie and TV"; LocalBook="The Wizard of Oz Script"},
    @{Name="America - Greatest Hits [Book]"; S3Path="America/America - Greatest Hits [book]/Songs/"; LocalArtist="America"; LocalBook="America - Greatest Hits [Book]"},
    @{Name="Ben Folds - Rockin' The Suburbs [Book]"; S3Path="Ben Folds/Ben Folds - Rockin' The Suburbs [book]/Songs/"; LocalArtist="Ben Folds"; LocalBook="Ben Folds - Rockin' The Suburbs [Book]"},
    @{Name="Elton John - The Elton John Collection [Piano Solos]"; S3Path="Elo/Elton John - The Elton John Collection [piano Solos]/Songs/"; LocalArtist="ELO"; LocalBook="Elton John - The Elton John Collection [Piano Solos]"},
    @{Name="Kinks - Guitar Legends [Tab]"; S3Path="Kinks/Guitar Legends [guitar]/Songs/"; LocalArtist="Kinks"; LocalBook="Kinks - Guitar Legends [Tab]"}
)

$totalFiles = 0
$totalBooks = 0

Write-Host "========================================"
Write-Host "Downloading 11 Books from S3"
Write-Host "========================================"
Write-Host ""

foreach ($book in $books) {
    Write-Host "Processing: $($book.Name)"
    Write-Host "  S3 Path: $($book.S3Path)"
    
    $localPath = "ProcessedSongs\$($book.LocalArtist)\$($book.LocalBook)"
    
    if (-not (Test-Path $localPath)) {
        [System.IO.Directory]::CreateDirectory($localPath) | Out-Null
        Write-Host "  Created directory: $localPath"
    }
    
    Write-Host "  Downloading files..."
    $s3Uri = "s3://jsmith-output/$($book.S3Path)"
    
    aws s3 sync $s3Uri $localPath --profile default --exclude "*" --include "*.pdf"
    
    if ($LASTEXITCODE -eq 0) {
        $fileCount = (Get-ChildItem -Path $localPath -Filter "*.pdf" -File).Count
        Write-Host "  Downloaded $fileCount files"
        $totalFiles += $fileCount
        $totalBooks++
    } else {
        Write-Host "  Download failed"
    }
    
    Write-Host ""
}

Write-Host "========================================"
Write-Host "DOWNLOAD COMPLETE"
Write-Host "========================================"
Write-Host "Books downloaded: $totalBooks"
Write-Host "Total files: $totalFiles"
Write-Host ""
Write-Host "Files are in: ProcessedSongs"
