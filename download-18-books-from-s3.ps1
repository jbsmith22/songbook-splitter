# Download the 18 books that are already in S3

$ErrorActionPreference = "Stop"
$Profile = "default"

Write-Host "Downloading 18 books from S3..."
Write-Host ""

# Map of local names to S3 paths (found by checking S3)
$books = @(
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - Shrek The Musical/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - Shrek The Musical"}
    @{S3="s3://jsmith-output/_broadway Shows/Wicked Workshop/Songs"; Local="ProcessedSongs\_Broadway Shows\Wicked Workshop"}
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - You're A Good Man Charlie Brown [revival] [score]/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - Youre A Good Man Charlie Brown _Score_"}
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - High School Musical [score]/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - High School Musical _score_"}
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - Little Shop Of Horrors (original)/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - Little Shop Of Horrors _Broadway_"}
    @{S3="s3://jsmith-output/_movie and TV/Various Artists - Wizard Of Oz - Piano Conductor/Songs"; Local="ProcessedSongs\_Movie and TV\The Wizard Of Oz Script"}
    @{S3="s3://jsmith-output/_movie and TV/Various Artists - Complete TV And Film/Songs"; Local="ProcessedSongs\_Movie and TV\Various Artists - Complete TV And Film"}
    @{S3="s3://jsmith-output/Crosby Stills and Nash/Crosby Stills Nash And Young - The Guitar Collection/Songs"; Local="ProcessedSongs\Crosby Stills and Nash\Crosby Stills Nash And Young - The Guitar Collection"}
    @{S3="s3://jsmith-output/Dire Straits/Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_/Songs"; Local="ProcessedSongs\Dire Straits\Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"}
    @{S3="s3://jsmith-output/Elvis Presley/Elvis Presley - The Compleat _PVG Book_/Songs"; Local="ProcessedSongs\Elvis Presley\Elvis Presley - The Compleat _PVG Book_"}
    @{S3="s3://jsmith-output/Eric Clapton/Eric Clapton - The Cream Of Clapton/Songs"; Local="ProcessedSongs\Eric Clapton\Eric Clapton - The Cream Of Clapton"}
    @{S3="s3://jsmith-output/John Denver/John Denver - Back Home Again/Songs"; Local="ProcessedSongs\John Denver\John Denver - Back Home Again"}
    @{S3="s3://jsmith-output/Mamas and the Papas/Mamas And The Papas - Songbook _PVG_/Songs"; Local="ProcessedSongs\Mamas and the Papas\Mamas And The Papas - Songbook _PVG_"}
    @{S3="s3://jsmith-output/Night Ranger/Night Ranger - Seven Wishes _Jap Score_/Songs"; Local="ProcessedSongs\Night Ranger\Night Ranger - Seven Wishes _Jap Score_"}
    @{S3="s3://jsmith-output/Robbie Robertson/Robbie Robertson - Songbook _Guitar Tab_/Songs"; Local="ProcessedSongs\Robbie Robertson\Robbie Robertson - Songbook _Guitar Tab_"}
    @{S3="s3://jsmith-output/Tom Waits/Tom Waits - Tom Waits Anthology/Songs"; Local="ProcessedSongs\Tom Waits\Tom Waits - Tom Waits Anthology"}
    @{S3="s3://jsmith-output/Various Artists/Various Artists - Ultimate 80s Songs/Songs"; Local="ProcessedSongs\Various Artists\Various Artists - Ultimate 80s Songs"}
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - 25th Annual Putnam County Spelling Bee/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - 25th Annual Putnam County Spelling Bee"}
)

$counter = 0
$successCount = 0

foreach ($book in $books) {
    $counter++
    $bookName = Split-Path $book.Local -Leaf
    Write-Host "[$counter/$($books.Count)] $bookName"
    
    # Create directory
    if (-not (Test-Path $book.Local)) {
        New-Item -ItemType Directory -Path $book.Local -Force | Out-Null
    }
    
    # Download
    try {
        aws s3 cp $book.S3 $book.Local --recursive --profile $Profile 2>&1 | Out-Null
        $fileCount = (Get-ChildItem $book.Local -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
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
Write-Host ("=" * 80)
Write-Host "Downloaded: $successCount / $($books.Count)"
Write-Host ("=" * 80)
