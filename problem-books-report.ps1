# Generate report of problem books: no folders or multiple folders

Write-Host "Generating problem books report..." -ForegroundColor Cyan
Write-Host ""

# Load the matched inventory
$matched = Import-Csv "strict-inventory-matched.csv"

# Get all source books
Write-Host "Step 1: Loading all source books..." -ForegroundColor Yellow
$sourceBooks = @()
$artistFolders = Get-ChildItem "SheetMusic" -Directory

foreach ($artistFolder in $artistFolders) {
    $artistName = $artistFolder.Name
    
    if ($artistName -like "*Fake Book*") { continue }
    
    if ($artistName -eq "_Movie and TV" -or $artistName -eq "_Broadway Shows") {
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

# Step 2: Group matched folders by source book
Write-Host "Step 2: Analyzing matches..." -ForegroundColor Yellow
$grouped = $matched | Group-Object SourcePath

$noFolders = @()
$multipleFolders = @()

foreach ($sourceBook in $sourceBooks) {
    $sourcePath = $sourceBook.SourcePath
    $group = $grouped | Where-Object { $_.Name -eq $sourcePath }
    
    if (-not $group) {
        # No folders for this source book
        $noFolders += [PSCustomObject]@{
            Artist = $sourceBook.Artist
            SourceBook = $sourceBook.BookName
            SourcePath = $sourcePath
            FolderCount = 0
            Folders = ""
        }
    } elseif ($group.Count -gt 1 -or $group.Group.Count -gt 1) {
        # Multiple folders for this source book
        $folderNames = ($group.Group | ForEach-Object { $_.ProcessedFolder }) -join "; "
        $multipleFolders += [PSCustomObject]@{
            Artist = $sourceBook.Artist
            SourceBook = $sourceBook.BookName
            SourcePath = $sourcePath
            FolderCount = $group.Group.Count
            Folders = $folderNames
        }
    }
}

Write-Host "Books with NO folders: $($noFolders.Count)" -ForegroundColor Red
Write-Host "Books with MULTIPLE folders: $($multipleFolders.Count)" -ForegroundColor Yellow
Write-Host ""

# Export results
$noFolders | Export-Csv "books-with-no-folders.csv" -NoTypeInformation -Encoding UTF8
$multipleFolders | Export-Csv "books-with-multiple-folders.csv" -NoTypeInformation -Encoding UTF8

Write-Host "================================================================================"
Write-Host "Reports saved:"
Write-Host "  - books-with-no-folders.csv ($($noFolders.Count) books)"
Write-Host "  - books-with-multiple-folders.csv ($($multipleFolders.Count) books)"
Write-Host "================================================================================"
Write-Host ""

if ($noFolders.Count -gt 0) {
    Write-Host "Books with NO folders (first 20):" -ForegroundColor Red
    $noFolders | Select-Object -First 20 Artist, SourceBook | Format-Table -AutoSize
    Write-Host ""
}

if ($multipleFolders.Count -gt 0) {
    Write-Host "Books with MULTIPLE folders (first 20):" -ForegroundColor Yellow
    $multipleFolders | Select-Object -First 20 Artist, SourceBook, FolderCount | Format-Table -AutoSize
}
