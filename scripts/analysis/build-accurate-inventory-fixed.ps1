# Build accurate inventory comparing source books to processed folders
# Handles special cases for _Movie and TV and _Broadway Shows

$sourceRoot = "C:\Work\AWSMusic\SheetMusic"
$processedRoot = "C:\Work\AWSMusic\ProcessedSongs"
$outputCsv = "source-books-status-final.csv"

# Function to normalize strings for comparison
function Normalize-String {
    param([string]$str)
    return $str.ToLower() -replace '\s+', ' ' -replace '^\s+|\s+$', ''
}

# Function to strip artist prefix from book name
function Strip-ArtistPrefix {
    param([string]$bookName, [string]$artistName)
    $normalized = Normalize-String $bookName
    $artistNorm = Normalize-String $artistName
    
    # Try to remove "Artist - " prefix
    if ($normalized -match "^$([regex]::Escape($artistNorm))\s*-\s*(.+)$") {
        return $matches[1].Trim()
    }
    return $bookName
}

# Function to find matching processed folder
function Find-ProcessedFolder {
    param(
        [string]$artistName,
        [string]$bookName,
        [string]$processedRoot
    )
    
    # Normalize the book name (strip artist prefix)
    $strippedBookName = Strip-ArtistPrefix -bookName $bookName -artistName $artistName
    $normalizedBook = Normalize-String $strippedBookName
    
    # Determine the artist folder to search in
    $artistFolder = $null
    if ($artistName -eq "_Movie and TV") {
        $artistFolder = Join-Path $processedRoot "_movie And Tv"
    }
    elseif ($artistName -eq "_Broadway Shows") {
        $artistFolder = Join-Path $processedRoot "_broadway Shows"
    }
    else {
        # Find artist folder (case-insensitive)
        $normalizedArtist = Normalize-String $artistName
        $artistFolder = Get-ChildItem $processedRoot -Directory | Where-Object {
            (Normalize-String $_.Name) -eq $normalizedArtist
        } | Select-Object -First 1 -ExpandProperty FullName
    }
    
    if (-not $artistFolder -or -not (Test-Path $artistFolder)) {
        return $null
    }
    
    # Search for matching book folder
    $bookFolders = Get-ChildItem $artistFolder -Directory -ErrorAction SilentlyContinue
    
    foreach ($folder in $bookFolders) {
        $folderNorm = Normalize-String $folder.Name
        
        # Escape special wildcard characters for -like comparison
        $escapedBook = $normalizedBook -replace '[\[\]\*\?]', '`$&'
        $escapedFolder = $folderNorm -replace '[\[\]\*\?]', '`$&'
        
        # Check if folder name contains the normalized book name
        if ($folderNorm -like "*$escapedBook*" -or $normalizedBook -like "*$escapedFolder*") {
            # Count PDF files in this folder
            $pdfCount = (Get-ChildItem $folder.FullName -Filter "*.pdf" -File -ErrorAction SilentlyContinue).Count
            if ($pdfCount -gt 0) {
                return @{
                    Path = $folder.FullName -replace [regex]::Escape($processedRoot + "\"), "ProcessedSongs\"
                    Count = $pdfCount
                }
            }
        }
    }
    
    return $null
}

# Collect all source books
$sourceBooks = @()

# Get all artist folders
$artistFolders = Get-ChildItem $sourceRoot -Directory

foreach ($artistFolder in $artistFolders) {
    $artistName = $artistFolder.Name
    
    # Handle special cases for _Movie and TV and _Broadway Shows
    if ($artistName -eq "_Movie and TV") {
        # Check subdirectories (Disney, John Williams, Others)
        $subfolders = Get-ChildItem $artistFolder.FullName -Directory
        foreach ($subfolder in $subfolders) {
            $booksPath = Join-Path $subfolder.FullName "Books"
            if (Test-Path $booksPath) {
                $books = Get-ChildItem $booksPath -Filter "*.pdf" -File
                foreach ($book in $books) {
                    $sourceBooks += @{
                        Artist = $artistName
                        BookName = [System.IO.Path]::GetFileNameWithoutExtension($book.Name)
                        SourcePath = $book.FullName
                    }
                }
            }
        }
    }
    elseif ($artistName -eq "_Broadway Shows") {
        # Check direct Books folder
        $booksPath = Join-Path $artistFolder.FullName "Books"
        if (Test-Path $booksPath) {
            $books = Get-ChildItem $booksPath -Filter "*.pdf" -File
            foreach ($book in $books) {
                $sourceBooks += @{
                    Artist = $artistName
                    BookName = [System.IO.Path]::GetFileNameWithoutExtension($book.Name)
                    SourcePath = $book.FullName
                }
            }
        }
        
        # Check subdirectories (e.g., Steven Sondheim)
        $subfolders = Get-ChildItem $artistFolder.FullName -Directory | Where-Object { $_.Name -ne "Books" }
        foreach ($subfolder in $subfolders) {
            $booksPath = Join-Path $subfolder.FullName "Books"
            if (Test-Path $booksPath) {
                $books = Get-ChildItem $booksPath -Filter "*.pdf" -File
                foreach ($book in $books) {
                    $sourceBooks += @{
                        Artist = $artistName
                        BookName = [System.IO.Path]::GetFileNameWithoutExtension($book.Name)
                        SourcePath = $book.FullName
                    }
                }
            }
        }
    }
    else {
        # Standard artist folder structure
        $booksPath = Join-Path $artistFolder.FullName "Books"
        if (Test-Path $booksPath) {
            $books = Get-ChildItem $booksPath -Filter "*.pdf" -File
            foreach ($book in $books) {
                $sourceBooks += @{
                    Artist = $artistName
                    BookName = [System.IO.Path]::GetFileNameWithoutExtension($book.Name)
                    SourcePath = $book.FullName
                }
            }
        }
    }
}

Write-Host "Found $($sourceBooks.Count) source books"

# Build the inventory
$inventory = @()
$expandedCount = 0
$notExpandedCount = 0

foreach ($book in $sourceBooks) {
    $match = Find-ProcessedFolder -artistName $book.Artist -bookName $book.BookName -processedRoot $processedRoot
    
    if ($match) {
        $inventory += [PSCustomObject]@{
            Artist = $book.Artist
            BookName = $book.BookName
            SourcePath = $book.SourcePath
            ProcessedFolder = $match.Path
            PDFCount = $match.Count
            Status = "EXPANDED"
        }
        $expandedCount++
    }
    else {
        $inventory += [PSCustomObject]@{
            Artist = $book.Artist
            BookName = $book.BookName
            SourcePath = $book.SourcePath
            ProcessedFolder = ""
            PDFCount = 0
            Status = "NOT_EXPANDED"
        }
        $notExpandedCount++
    }
}

# Export to CSV
$inventory | Export-Csv -Path $outputCsv -NoTypeInformation -Encoding UTF8

Write-Host "`nInventory Summary:"
Write-Host "Total Source Books: $($sourceBooks.Count)"
Write-Host "Expanded: $expandedCount ($([math]::Round($expandedCount / $sourceBooks.Count * 100, 1))%)"
Write-Host "Not Expanded: $notExpandedCount ($([math]::Round($notExpandedCount / $sourceBooks.Count * 100, 1))%)"
Write-Host "`nInventory saved to: $outputCsv"
