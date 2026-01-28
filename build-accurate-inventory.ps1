# Build accurate inventory by crawling physical directories

Write-Host "Building accurate inventory from physical directories..." -ForegroundColor Cyan
Write-Host ""

$results = @()

# Get all source books from SheetMusic folder
Write-Host "Scanning SheetMusic folder for source books..." -ForegroundColor Yellow

$sourceBooks = @()

# Get all artist folders in SheetMusic
$artistFolders = Get-ChildItem "SheetMusic" -Directory

foreach ($artistFolder in $artistFolders) {
    $artistName = $artistFolder.Name
    
    # Skip Fake Books
    if ($artistName -like "*Fake Book*") {
        Write-Host "  Skipping: $artistName" -ForegroundColor Gray
        continue
    }
    
    # Check for books in "books" or "Books" subfolder
    $booksFolder = $null
    $booksFolderLower = Join-Path $artistFolder.FullName "books"
    $booksFolderUpper = Join-Path $artistFolder.FullName "Books"
    
    if (Test-Path $booksFolderLower) {
        $booksFolder = $booksFolderLower
    } elseif (Test-Path $booksFolderUpper) {
        $booksFolder = $booksFolderUpper
    }
    
    if ($booksFolder) {
        $books = Get-ChildItem $booksFolder -Filter "*.pdf" -File
        
        foreach ($book in $books) {
            $sourceBooks += @{
                Artist = $artistName
                BookName = $book.BaseName
                SourcePath = $book.FullName
            }
        }
    }
}

Write-Host "Found $($sourceBooks.Count) source books" -ForegroundColor Green
Write-Host ""

# Now check ProcessedSongs for each source book
Write-Host "Checking ProcessedSongs for processed versions..." -ForegroundColor Yellow
Write-Host ""

$processedCount = 0

foreach ($sourceBook in $sourceBooks) {
    $artist = $sourceBook.Artist
    $bookName = $sourceBook.BookName
    
    # Look for matching folder in ProcessedSongs
    $processedArtistFolder = Join-Path "ProcessedSongs" $artist
    
    $hasProcessed = $false
    $songCount = 0
    $processedFolder = ""
    
    if (Test-Path $processedArtistFolder) {
        # Get all book folders for this artist
        $bookFolders = Get-ChildItem $processedArtistFolder -Directory
        
        # Try to find a matching book folder
        # The book name might not match exactly, so we'll look for close matches
        $matchingFolder = $bookFolders | Where-Object { 
            $_.Name -eq $bookName -or 
            $_.Name -like "*$bookName*" -or
            $bookName -like "*$($_.Name)*"
        } | Select-Object -First 1
        
        if ($matchingFolder) {
            $hasProcessed = $true
            $processedFolder = $matchingFolder.Name
            $songCount = (Get-ChildItem $matchingFolder.FullName -Filter "*.pdf" -Recurse | Measure-Object).Count
            $processedCount++
        }
    }
    
    $results += [PSCustomObject]@{
        Artist = $artist
        BookName = $bookName
        SourcePath = $sourceBook.SourcePath
        HasProcessed = $hasProcessed
        ProcessedFolder = $processedFolder
        SongCount = $songCount
    }
}

Write-Host "Found $processedCount books with processed songs" -ForegroundColor Green
Write-Host ""

# Export to CSV
$outputFile = "accurate-book-inventory.csv"
$results | Export-Csv $outputFile -NoTypeInformation -Encoding UTF8

Write-Host "================================================================================"
Write-Host "Inventory saved to: $outputFile"
Write-Host "================================================================================"
Write-Host ""
Write-Host "Summary:"
Write-Host "  Total source books: $($sourceBooks.Count)"
Write-Host "  Books with processed songs: $processedCount"
Write-Host "  Books without processed songs: $($sourceBooks.Count - $processedCount)"
Write-Host "  Total songs: $(($results | Measure-Object -Property SongCount -Sum).Sum)"
Write-Host "================================================================================"
