# Build accurate inventory with aggressive fuzzy matching
$sourceRoot = "C:\Work\AWSMusic\SheetMusic"
$processedRoot = "C:\Work\AWSMusic\ProcessedSongs"
$outputCsv = "source-books-status-final.csv"

# Function to normalize strings aggressively
function Normalize-String {
    param([string]$str)
    # Convert to lowercase, remove all special chars, collapse whitespace
    $normalized = $str.ToLower()
    $normalized = $normalized -replace '[^\w\s]', ' '  # Replace special chars with space
    $normalized = $normalized -replace '\s+', ' '      # Collapse whitespace
    $normalized = $normalized.Trim()
    return $normalized
}

# Function to strip artist prefix from book name
function Strip-ArtistPrefix {
    param([string]$bookName, [string]$artistName)
    $normalized = Normalize-String $bookName
    $artistNorm = Normalize-String $artistName
    
    # Try to remove "Artist - " prefix
    if ($normalized -match "^$([regex]::Escape($artistNorm))\s+(.+)$") {
        return $matches[1].Trim()
    }
    return $normalized
}

# Build index of all processed folders with PDFs (using .NET for bracket handling)
Write-Host "Building index of processed folders..."
$processedIndex = @{}

function Get-FoldersWithPDFs {
    param([string]$rootPath)
    
    $artistFolders = [System.IO.Directory]::GetDirectories($rootPath)
    
    foreach ($artistFolder in $artistFolders) {
        $artistName = [System.IO.Path]::GetFileName($artistFolder)
        $bookFolders = [System.IO.Directory]::GetDirectories($artistFolder)
        
        foreach ($bookFolder in $bookFolders) {
            $bookName = [System.IO.Path]::GetFileName($bookFolder)
            
            # Count PDFs recursively
            $pdfCount = ([System.IO.Directory]::GetFiles($bookFolder, "*.pdf", [System.IO.SearchOption]::AllDirectories)).Count
            
            if ($pdfCount -gt 0) {
                $relativePath = $bookFolder -replace [regex]::Escape($rootPath + "\"), "ProcessedSongs\"
                $normalizedName = Normalize-String $bookName
                
                $processedIndex[$bookFolder] = @{
                    Path = $relativePath
                    Name = $bookName
                    NormalizedName = $normalizedName
                    Artist = $artistName
                    PDFCount = $pdfCount
                    Matched = $false
                }
            }
        }
    }
}

Get-FoldersWithPDFs -rootPath $processedRoot

Write-Host "Found $($processedIndex.Count) processed folders with PDFs"

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

# Match source books to processed folders
$inventory = @()
$expandedCount = 0
$notExpandedCount = 0

foreach ($book in $sourceBooks) {
    $matched = $false
    $matchedFolder = $null
    
    # Normalize book name (strip artist prefix)
    $strippedBookName = Strip-ArtistPrefix -bookName $book.BookName -artistName $book.Artist
    $normalizedBook = Normalize-String $strippedBookName
    
    # Try to find matching processed folder
    foreach ($key in $processedIndex.Keys) {
        $folder = $processedIndex[$key]
        
        $folderNorm = $folder.NormalizedName
        
        # First check: Artist must match (case-insensitive, normalized)
        $artistMatch = $false
        $normalizedArtist = Normalize-String $book.Artist
        $normalizedFolderArtist = Normalize-String $folder.Artist
        
        if ($normalizedArtist -eq $normalizedFolderArtist) {
            $artistMatch = $true
        }
        
        # Skip if artist doesn't match
        if (-not $artistMatch) {
            continue
        }
        
        # Check for match using various strategies
        $isMatch = $false
        
        # Strategy 1: Exact normalized match
        if ($folderNorm -eq $normalizedBook) {
            $isMatch = $true
        }
        
        # Strategy 2: Folder contains book name (must be substantial match)
        if (-not $isMatch -and $normalizedBook.Length -gt 5 -and $folderNorm.Contains($normalizedBook)) {
            $isMatch = $true
        }
        
        # Strategy 3: Book name contains folder name (must be substantial match)
        if (-not $isMatch -and $folderNorm.Length -gt 5 -and $normalizedBook.Contains($folderNorm)) {
            $isMatch = $true
        }
        
        # Strategy 4: Significant word overlap (at least 70% of words match)
        if (-not $isMatch) {
            $bookWords = $normalizedBook -split '\s+' | Where-Object { $_.Length -gt 2 }
            $folderWords = $folderNorm -split '\s+' | Where-Object { $_.Length -gt 2 }
            
            if ($bookWords.Count -gt 0 -and $folderWords.Count -gt 0) {
                $matchingWords = 0
                foreach ($word in $bookWords) {
                    if ($folderWords -contains $word) {
                        $matchingWords++
                    }
                }
                $matchRatio = $matchingWords / $bookWords.Count
                if ($matchRatio -ge 0.7) {
                    $isMatch = $true
                }
            }
        }
        
        if ($isMatch) {
            $matched = $true
            $matchedFolder = $folder
            break
        }
    }
    
    if ($matched) {
        $inventory += [PSCustomObject]@{
            Artist = $book.Artist
            BookName = $book.BookName
            SourcePath = $book.SourcePath
            ProcessedFolder = $matchedFolder.Path
            PDFCount = $matchedFolder.PDFCount
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

# Show NOT_EXPANDED books
if ($notExpandedCount -gt 0) {
    Write-Host "`n=== NOT_EXPANDED Books ==="
    $inventory | Where-Object { $_.Status -eq "NOT_EXPANDED" } | ForEach-Object {
        Write-Host "$($_.Artist) - $($_.BookName)"
    }
}
