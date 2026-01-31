# Build simple inventory - just list what we have

Write-Host "Building simple inventory..." -ForegroundColor Cyan
Write-Host ""

$results = @()

# Get all source books
$sourceBooks = @()
$artistFolders = Get-ChildItem "SheetMusic" -Directory

foreach ($artistFolder in $artistFolders) {
    $artistName = $artistFolder.Name
    
    # Skip Fake Books
    if ($artistName -like "*Fake Book*") { continue }
    
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

# Check ProcessedSongs
$processedCount = 0

foreach ($sourceBook in $sourceBooks) {
    $artist = $sourceBook.Artist
    $bookName = $sourceBook.BookName
    
    # Remove artist prefix from book name if present (e.g., "Billy Joel - Anthology" -> "Anthology")
    $bookNameWithoutArtist = $bookName
    if ($bookName -like "$artist -*") {
        $bookNameWithoutArtist = $bookName.Substring($artist.Length + 3).Trim()
    }
    
    # Normalize names for comparison (remove special chars and spaces)
    $normalizedBookName = $bookNameWithoutArtist -replace '[^a-zA-Z0-9]', ''
    
    $processedArtistFolder = Join-Path "ProcessedSongs" $artist
    
    $hasProcessed = $false
    $songCount = 0
    $processedFolder = ""
    
    if (Test-Path $processedArtistFolder) {
        $bookFolders = Get-ChildItem $processedArtistFolder -Directory
        
        # Find matching folder by normalizing names
        foreach ($folder in $bookFolders) {
            $normalizedFolderName = $folder.Name -replace '[^a-zA-Z0-9]', ''
            
            if ($normalizedFolderName -eq $normalizedBookName) {
                $hasProcessed = $true
                $processedFolder = $folder.Name
                try {
                    $songCount = (Get-ChildItem $folder.FullName -Filter "*.pdf" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
                } catch {
                    $songCount = 0
                }
                $processedCount++
                break
            }
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

# Export
$outputFile = "simple-book-inventory.csv"
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
