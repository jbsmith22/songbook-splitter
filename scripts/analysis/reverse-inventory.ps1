# Reverse inventory - show all processed folders and whether they have a matching source book

Write-Host "Building reverse inventory (ProcessedSongs -> SheetMusic)..." -ForegroundColor Cyan
Write-Host ""

$results = @()

# Get all source books for lookup
$sourceBooks = @{}
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
            $bookName = $book.BaseName
            
            # Remove artist prefix if present
            $bookNameWithoutArtist = $bookName
            if ($bookName -like "$artistName -*") {
                $bookNameWithoutArtist = $bookName.Substring($artistName.Length + 3).Trim()
            }
            
            # Normalize for lookup
            $normalizedName = $bookNameWithoutArtist -replace '[^a-zA-Z0-9]', ''
            $key = "$artistName|$normalizedName"
            $sourceBooks[$key] = $bookName
        }
    }
}

Write-Host "Loaded $($sourceBooks.Count) source books for lookup" -ForegroundColor Green
Write-Host ""

# Now scan all processed folders
$processedArtistFolders = Get-ChildItem "ProcessedSongs" -Directory
$matchedCount = 0
$unmatchedCount = 0

foreach ($artistDir in $processedArtistFolders) {
    $artistName = $artistDir.Name
    $bookFolders = Get-ChildItem $artistDir.FullName -Directory
    
    foreach ($bookFolder in $bookFolders) {
        $bookFolderName = $bookFolder.Name
        
        # Count songs in this folder (use .NET to avoid wildcard issues with brackets)
        try {
            $songCount = ([System.IO.Directory]::GetFiles($bookFolder.FullName, "*.pdf", [System.IO.SearchOption]::AllDirectories) | Measure-Object).Count
        } catch {
            $songCount = 0
        }
        
        # Normalize folder name for lookup
        $normalizedFolderName = $bookFolderName -replace '[^a-zA-Z0-9]', ''
        $key = "$artistName|$normalizedFolderName"
        
        $hasSource = $sourceBooks.ContainsKey($key)
        $sourceBookName = if ($hasSource) { $sourceBooks[$key] } else { "" }
        
        if ($hasSource) {
            $matchedCount++
        } else {
            $unmatchedCount++
        }
        
        $results += [PSCustomObject]@{
            Artist = $artistName
            ProcessedFolder = $bookFolderName
            SongCount = $songCount
            HasSourceBook = $hasSource
            SourceBookName = $sourceBookName
            ProcessedPath = $bookFolder.FullName
        }
    }
}

Write-Host "Found $matchedCount folders with matching source books" -ForegroundColor Green
Write-Host "Found $unmatchedCount folders WITHOUT matching source books" -ForegroundColor Yellow
Write-Host ""

# Export all results
$outputFile = "reverse-inventory-all.csv"
$results | Sort-Object Artist, ProcessedFolder | Export-Csv $outputFile -NoTypeInformation -Encoding UTF8
Write-Host "All folders saved to: $outputFile" -ForegroundColor Cyan

# Export only unmatched
$unmatchedFile = "reverse-inventory-unmatched.csv"
$results | Where-Object { $_.HasSourceBook -eq $false } | Sort-Object Artist, ProcessedFolder | Export-Csv $unmatchedFile -NoTypeInformation -Encoding UTF8
Write-Host "Unmatched folders saved to: $unmatchedFile" -ForegroundColor Cyan

# Calculate totals
$totalSongsMatched = ($results | Where-Object { $_.HasSourceBook -eq $true } | Measure-Object -Property SongCount -Sum).Sum
$totalSongsUnmatched = ($results | Where-Object { $_.HasSourceBook -eq $false } | Measure-Object -Property SongCount -Sum).Sum

Write-Host ""
Write-Host "================================================================================"
Write-Host "Summary:"
Write-Host "  Total processed folders: $($results.Count)"
Write-Host "  Folders with source books: $matchedCount"
Write-Host "  Folders WITHOUT source books: $unmatchedCount"
Write-Host "  Songs in matched folders: $totalSongsMatched"
Write-Host "  Songs in unmatched folders: $totalSongsUnmatched"
Write-Host "  Total songs: $($totalSongsMatched + $totalSongsUnmatched)"
Write-Host "================================================================================"
