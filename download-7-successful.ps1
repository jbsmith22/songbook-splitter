# Download the 7 successful retry books

$ErrorActionPreference = "Stop"
$Profile = "default"

Write-Host ("=" * 80)
Write-Host "DOWNLOADING 7 SUCCESSFUL BOOKS"
Write-Host ("=" * 80)
Write-Host ""

# The 7 books that succeeded with actual files
$books = @(
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - 25th Annual Putnam County Spelling Bee/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - 25th Annual Putnam County Spelling Bee"}
    @{S3="s3://jsmith-output/_broadway Shows/Various Artists - Little Shop Of Horrors Script/Songs"; Local="ProcessedSongs\_Broadway Shows\Various Artists - Little Shop Of Horrors Script"}
    @{S3="s3://jsmith-output/John Denver/John Denver - Back Home Again/Songs"; Local="ProcessedSongs\John Denver\John Denver - Back Home Again"}
    @{S3="s3://jsmith-output/_movie and TV/Various Artists - Complete TV And Film/Songs"; Local="ProcessedSongs\_Movie and TV\Various Artists - Complete TV And Film"}
    @{S3="s3://jsmith-output/Night Ranger/Night Ranger - Seven Wishes _Jap Score_/Songs"; Local="ProcessedSongs\Night Ranger\Night Ranger - Seven Wishes _Jap Score_"}
    @{S3="s3://jsmith-output/_movie and TV/The Wizard Of Oz Script/Songs"; Local="ProcessedSongs\_Movie and TV\The Wizard Of Oz Script"}
    @{S3="s3://jsmith-output/Mamas and the Papas/Mamas And The Papas - Songbook _PVG_/Songs"; Local="ProcessedSongs\Mamas and the Papas\Mamas And The Papas - Songbook _PVG_"}
)

$counter = 0
$successCount = 0
$totalFiles = 0

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
            $totalFiles += $fileCount
        } else {
            Write-Host "  WARNING - No files found"
        }
    } catch {
        Write-Host "  ERROR - $_"
    }
}

Write-Host ""
Write-Host ("=" * 80)
Write-Host "SUMMARY"
Write-Host ("=" * 80)
Write-Host "Books downloaded: $successCount / $($books.Count)"
Write-Host "Total songs: $totalFiles"
Write-Host ("=" * 80)
