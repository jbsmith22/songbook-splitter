# Reverse inventory v2 - handles nested structures for collections

Write-Host "Building reverse inventory (ProcessedSongs -> SheetMusic)..." -ForegroundColor Cyan
Write-Host ""

$results = @()

# Build a comprehensive lookup of all source books
$sourceBooks = @{}

function Add-SourceBooks {
    param($folderPath, $artistName)
    
    if (Test-Path $folderPath) {
        $books = Get-ChildItem $folderPath -Filter "*.pdf" -File
        
        foreach ($book in $books) {
            $bookName = $book.BaseName
            
            # Remove artist prefix if present
            $bookNameWithoutArtist = $bookName
            if ($bookName -like "$artistName -*") {
                $bookNameWithoutArtist = $bookName.Substring($artistName.Length + 3).Trim()
            }
            
            # Normalize for lookup (remove all non-alphanumeric, case insensitive)
            $normalizedName = $bookNameWithoutArtist -replace '[^a-zA-Z0-9]', '' -replace '\s+', ''
            $normalizedName = $normalizedName.ToLower()
            
            # Store with multiple keys for better matching
            $key1 = "$artistName|$normalizedName"
            $key2 = $normalizedName  # Just the book name for cross-artist matching
            
            $sourceBooks[$key1] = @{
                FullName = $bookName
                Path = $book.FullName
                Artist = $artistName
            }
            
            # Also store without artist for collections
            if (-not $sourceBooks.ContainsKey($key2)) {
                $sourceBooks[$key2] = @{
                    FullName = $bookName
                    Path = $book.FullName
                    Artist = $artistName
                }
            }
        }
    }
}

# Scan regular artist folders
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
            Add-SourceBooks -folderPath $rootBooksFolder -artistName $artistName
        }
        
        # Then check subfolders (Disney, John Williams, Steven Sondheim, etc.) with Books subfolders
        $subfolders = Get-ChildItem $artistFolder.FullName -Directory | Where-Object { $_.Name -ne "Books" }
        foreach ($subfolder in $subfolders) {
            $booksFolder = Join-Path $subfolder.FullName "Books"
            if (Test-Path $booksFolder) {
                Add-SourceBooks -folderPath $booksFolder -artistName $artistName
            }
        }
    } else {
        # Regular artists - check for books or Books subfolder
        $booksFolderLower = Join-Path $artistFolder.FullName "books"
        $booksFolderUpper = Join-Path $artistFolder.FullName "Books"
        
        if (Test-Path $booksFolderLower) {
            Add-SourceBooks -folderPath $booksFolderLower -artistName $artistName
        } elseif (Test-Path $booksFolderUpper) {
            Add-SourceBooks -folderPath $booksFolderUpper -artistName $artistName
        }
    }
}

Write-Host "Loaded $($sourceBooks.Count) source book entries for lookup" -ForegroundColor Green
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
        
        # Count songs in this folder (use .NET to avoid wildcard issues)
        try {
            $songCount = ([System.IO.Directory]::GetFiles($bookFolder.FullName, "*.pdf", [System.IO.SearchOption]::AllDirectories) | Measure-Object).Count
        } catch {
            $songCount = 0
        }
        
        # Normalize folder name for lookup
        $normalizedFolderName = $bookFolderName -replace '[^a-zA-Z0-9]', '' -replace '\s+', ''
        $normalizedFolderName = $normalizedFolderName.ToLower()
        
        # Also try with artist prefix removed (in case folder has full name)
        $normalizedWithoutArtist = $bookFolderName
        if ($bookFolderName -like "$artistName -*") {
            $normalizedWithoutArtist = $bookFolderName.Substring($artistName.Length + 3).Trim()
        }
        $normalizedWithoutArtist = $normalizedWithoutArtist -replace '[^a-zA-Z0-9]', '' -replace '\s+', ''
        $normalizedWithoutArtist = $normalizedWithoutArtist.ToLower()
        
        # Try multiple lookup strategies
        $key1 = "$artistName|$normalizedFolderName"
        $key2 = $normalizedFolderName  # Just book name
        $key3 = "$artistName|$normalizedWithoutArtist"  # With artist prefix removed
        $key4 = $normalizedWithoutArtist  # Just book name without artist
        
        $hasSource = $false
        $sourceBookName = ""
        $sourcePath = ""
        
        if ($sourceBooks.ContainsKey($key1)) {
            $hasSource = $true
            $sourceBookName = $sourceBooks[$key1].FullName
            $sourcePath = $sourceBooks[$key1].Path
        } elseif ($sourceBooks.ContainsKey($key2)) {
            $hasSource = $true
            $sourceBookName = $sourceBooks[$key2].FullName
            $sourcePath = $sourceBooks[$key2].Path
        } elseif ($sourceBooks.ContainsKey($key3)) {
            $hasSource = $true
            $sourceBookName = $sourceBooks[$key3].FullName
            $sourcePath = $sourceBooks[$key3].Path
        } elseif ($sourceBooks.ContainsKey($key4)) {
            $hasSource = $true
            $sourceBookName = $sourceBooks[$key4].FullName
            $sourcePath = $sourceBooks[$key4].Path
        }
        
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
            SourcePath = $sourcePath
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
