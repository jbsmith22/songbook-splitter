# Strict 1:1 matching - find folders that don't have a direct source book match

Write-Host "Building strict 1:1 inventory..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Get ALL source books with their exact paths
Write-Host "Step 1: Scanning source books..." -ForegroundColor Yellow
$sourceBooks = @()
$artistFolders = Get-ChildItem "SheetMusic" -Directory

foreach ($artistFolder in $artistFolders) {
    $artistName = $artistFolder.Name
    
    # Skip Fake Books
    if ($artistName -like "*Fake Book*") { continue }
    
    # Handle special collection folders with nested structure
    if ($artistName -eq "_Movie and TV" -or $artistName -eq "_Broadway Shows") {
        # First check for Books folder at root level
        $rootBooksFolder = Join-Path $artistFolder.FullName "Books"
        if (Test-Path $rootBooksFolder) {
            $books = Get-ChildItem $rootBooksFolder -Filter "*.pdf" -File
            foreach ($book in $books) {
                $sourceBooks += [PSCustomObject]@{
                    Artist = $artistName
                    BookName = $book.BaseName
                    SourcePath = $book.FullName
                }
            }
        }
        
        # Then check subfolders with Books subfolders
        $subfolders = Get-ChildItem $artistFolder.FullName -Directory | Where-Object { $_.Name -ne "Books" }
        foreach ($subfolder in $subfolders) {
            $booksFolder = Join-Path $subfolder.FullName "Books"
            if (Test-Path $booksFolder) {
                $books = Get-ChildItem $booksFolder -Filter "*.pdf" -File
                foreach ($book in $books) {
                    $sourceBooks += [PSCustomObject]@{
                        Artist = $artistName
                        BookName = $book.BaseName
                        SourcePath = $book.FullName
                    }
                }
            }
        }
    } else {
        # Regular artists - check for books or Books subfolder
        $booksFolderLower = Join-Path $artistFolder.FullName "books"
        $booksFolderUpper = Join-Path $artistFolder.FullName "Books"
        
        $booksFolder = $null
        if (Test-Path $booksFolderLower) {
            $booksFolder = $booksFolderLower
        } elseif (Test-Path $booksFolderUpper) {
            $booksFolder = $booksFolderUpper
        }
        
        if ($booksFolder) {
            $books = Get-ChildItem $booksFolder -Filter "*.pdf" -File
            foreach ($book in $books) {
                $sourceBooks += [PSCustomObject]@{
                    Artist = $artistName
                    BookName = $book.BaseName
                    SourcePath = $book.FullName
                }
            }
        }
    }
}

Write-Host "Found $($sourceBooks.Count) source books" -ForegroundColor Green
Write-Host ""

# Step 2: Get ALL processed folders
Write-Host "Step 2: Scanning processed folders..." -ForegroundColor Yellow
$processedFolders = @()
$artistDirs = Get-ChildItem "ProcessedSongs" -Directory

foreach ($artistDir in $artistDirs) {
    $bookFolders = Get-ChildItem $artistDir.FullName -Directory
    
    foreach ($bookFolder in $bookFolders) {
        # Count songs
        try {
            $songCount = ([System.IO.Directory]::GetFiles($bookFolder.FullName, "*.pdf", [System.IO.SearchOption]::AllDirectories) | Measure-Object).Count
        } catch {
            $songCount = 0
        }
        
        $processedFolders += [PSCustomObject]@{
            Artist = $artistDir.Name
            FolderName = $bookFolder.Name
            ProcessedPath = $bookFolder.FullName
            SongCount = $songCount
        }
    }
}

Write-Host "Found $($processedFolders.Count) processed folders" -ForegroundColor Green
Write-Host ""

# Step 3: Try to match each processed folder to exactly ONE source book
Write-Host "Step 3: Matching processed folders to source books..." -ForegroundColor Yellow

$matched = @()
$unmatched = @()

foreach ($procFolder in $processedFolders) {
    $artist = $procFolder.Artist
    $folderName = $procFolder.FolderName
    
    # Normalize folder name
    $normalizedFolder = $folderName -replace '[^a-zA-Z0-9]', ''
    $normalizedFolder = $normalizedFolder.ToLower()
    
    # Also try with artist prefix removed
    $normalizedWithoutArtist = $folderName
    if ($folderName -like "$artist -*") {
        $normalizedWithoutArtist = $folderName.Substring($artist.Length + 3).Trim()
    }
    $normalizedWithoutArtist = $normalizedWithoutArtist -replace '[^a-zA-Z0-9]', ''
    $normalizedWithoutArtist = $normalizedWithoutArtist.ToLower()
    
    # Find matching source books
    $matchingBooks = @()
    foreach ($sourceBook in $sourceBooks) {
        $sourceArtist = $sourceBook.Artist
        $sourceBookName = $sourceBook.BookName
        
        # Only consider books from the same artist
        if ($sourceArtist -ne $artist) {
            continue
        }
        
        # Remove artist prefix from source book if present
        $sourceWithoutArtist = $sourceBookName
        if ($sourceBookName -like "$sourceArtist -*") {
            $sourceWithoutArtist = $sourceBookName.Substring($sourceArtist.Length + 3).Trim()
        }
        
        # Normalize source book name
        $normalizedSource = $sourceWithoutArtist -replace '[^a-zA-Z0-9]', ''
        $normalizedSource = $normalizedSource.ToLower()
        
        # Check if it matches
        if (($normalizedSource -eq $normalizedFolder) -or ($normalizedSource -eq $normalizedWithoutArtist)) {
            $matchingBooks += $sourceBook
        }
    }
    
    if ($matchingBooks.Count -eq 1) {
        # Perfect 1:1 match
        $matched += [PSCustomObject]@{
            Artist = $artist
            ProcessedFolder = $folderName
            ProcessedPath = $procFolder.ProcessedPath
            SongCount = $procFolder.SongCount
            SourceBook = $matchingBooks[0].BookName
            SourcePath = $matchingBooks[0].SourcePath
            MatchType = "1:1"
        }
    } elseif ($matchingBooks.Count -gt 1) {
        # Multiple matches - ambiguous
        $matched += [PSCustomObject]@{
            Artist = $artist
            ProcessedFolder = $folderName
            ProcessedPath = $procFolder.ProcessedPath
            SongCount = $procFolder.SongCount
            SourceBook = "MULTIPLE MATCHES: $($matchingBooks.Count)"
            SourcePath = ""
            MatchType = "1:Many"
        }
    } else {
        # No match found
        $unmatched += [PSCustomObject]@{
            Artist = $artist
            ProcessedFolder = $folderName
            ProcessedPath = $procFolder.ProcessedPath
            SongCount = $procFolder.SongCount
        }
    }
}

Write-Host "Matched: $($matched.Count) folders" -ForegroundColor Green
Write-Host "Unmatched: $($unmatched.Count) folders" -ForegroundColor Yellow
Write-Host ""

# Export results
$matched | Export-Csv "strict-inventory-matched.csv" -NoTypeInformation -Encoding UTF8
$unmatched | Export-Csv "strict-inventory-unmatched.csv" -NoTypeInformation -Encoding UTF8

Write-Host "================================================================================"
Write-Host "Summary:"
Write-Host "  Source books: $($sourceBooks.Count)"
Write-Host "  Processed folders: $($processedFolders.Count)"
Write-Host "  Matched (1:1): $($matched.Count)"
Write-Host "  Unmatched: $($unmatched.Count)"
Write-Host ""
Write-Host "  Difference: $($processedFolders.Count - $sourceBooks.Count) more processed folders than source books"
Write-Host ""
Write-Host "Files saved:"
Write-Host "  - strict-inventory-matched.csv"
Write-Host "  - strict-inventory-unmatched.csv"
Write-Host "================================================================================"

if ($unmatched.Count -gt 0) {
    Write-Host ""
    Write-Host "Unmatched folders (no corresponding source book):" -ForegroundColor Yellow
    $unmatched | Select-Object Artist, ProcessedFolder, SongCount | Format-Table -AutoSize
}
