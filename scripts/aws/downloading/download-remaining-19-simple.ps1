# Simple download script - downloads all 18 succeeded books

$ErrorActionPreference = "Stop"

$Profile = "default"

Write-Host "Downloading 18 succeeded books..."
Write-Host ""

# Download each book directly
$downloads = @(
    @{Artist="_broadway Shows"; Book="Various Artists - Shrek The Musical"; Local="_Broadway Shows\Various Artists - Shrek The Musical"}
    @{Artist="_broadway Shows"; Book="Wicked Workshop"; Local="_Broadway Shows\Wicked Workshop"}
    @{Artist="_broadway Shows"; Book="Various Artists - You're A Good Man Charlie Brown [revival] [score]"; Local="_Broadway Shows\Various Artists - Youre A Good Man Charlie Brown _Score_"}
    @{Artist="_movie and TV"; Book="Various Artists - Wizard Of Oz - Piano Conductor"; Local="_Movie and TV\The Wizard Of Oz Script"}
    @{Artist="_movie and TV"; Book="Various Artists - Complete TV And Film"; Local="_Movie and TV\Various Artists - Complete TV And Film"}
    @{Artist="Crosby Stills and Nash"; Book="Crosby Stills Nash And Young - The Guitar Collection"; Local="Crosby Stills and Nash\Crosby Stills Nash And Young - The Guitar Collection"}
    @{Artist="Dire Straits"; Book="Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"; Local="Dire Straits\Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"}
    @{Artist="Elvis Presley"; Book="Elvis Presley - The Compleat _PVG Book_"; Local="Elvis Presley\Elvis Presley - The Compleat _PVG Book_"}
    @{Artist="Eric Clapton"; Book="Eric Clapton - The Cream Of Clapton"; Local="Eric Clapton\Eric Clapton - The Cream Of Clapton"}
    @{Artist="John Denver"; Book="John Denver - Back Home Again"; Local="John Denver\John Denver - Back Home Again"}
    @{Artist="Mamas and the Papas"; Book="Mamas And The Papas - Songbook _PVG_"; Local="Mamas and the Papas\Mamas And The Papas - Songbook _PVG_"}
    @{Artist="Night Ranger"; Book="Night Ranger - Seven Wishes _Jap Score_"; Local="Night Ranger\Night Ranger - Seven Wishes _Jap Score_"}
    @{Artist="Robbie Robertson"; Book="Robbie Robertson - Songbook _Guitar Tab_"; Local="Robbie Robertson\Robbie Robertson - Songbook _Guitar Tab_"}
    @{Artist="Tom Waits"; Book="Tom Waits - Tom Waits Anthology"; Local="Tom Waits\Tom Waits - Tom Waits Anthology"}
    @{Artist="Various Artists"; Book="Various Artists - Ultimate 80s Songs"; Local="Various Artists\Various Artists - Ultimate 80s Songs"}
)

$counter = 0
$successCount = 0

foreach ($dl in $downloads) {
    $counter++
    Write-Host "[$counter/15] $($dl.Book)"
    
    $s3Path = "s3://jsmith-output/$($dl.Artist)/$($dl.Book)/Songs/"
    $localPath = "ProcessedSongs\$($dl.Local)"
    
    # Create directory
    if (-not (Test-Path $localPath)) {
        New-Item -ItemType Directory -Path $localPath -Force | Out-Null
    }
    
    # Download
    try {
        aws s3 cp $s3Path $localPath --recursive --profile $Profile 2>&1 | Out-Null
        $fileCount = (Get-ChildItem $localPath -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
        if ($fileCount -gt 0) {
            Write-Host "  SUCCESS - Downloaded $fileCount files"
            $successCount++
        } else {
            Write-Host "  WARNING - No files found"
        }
    } catch {
        Write-Host "  ERROR - $_"
    }
}

Write-Host ""
Write-Host "Downloaded: $successCount / $($downloads.Count)"
