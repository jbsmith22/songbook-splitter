# Generate Book Processing Report
# This script analyzes all processed books and generates a report showing:
# - Book name
# - Number of songs extracted
# - Expected song count from TOC
# - Artist names used
# - Potential issues

param(
    [string]$OutputDir = ".\ProcessedSongs",
    [string]$ReportFile = "book-processing-report.csv",
    [string]$S3Bucket = "jsmith-output",
    [string]$Region = "us-east-1",
    [switch]$IncludeTOCComparison
)

$ErrorActionPreference = "Continue"

function Get-BookId {
    param($Artist, $BookName)
    $combined = "$Artist-$BookName"
    $sanitized = $combined -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-' -replace '^-|-$', ''
    return $sanitized.ToLower()
}

function Get-TOCEntryCount {
    param($BookId)
    
    try {
        # Download TOC parse JSON from S3
        $s3Key = "artifacts/$BookId/toc_parse.json"
        $tempFile = [System.IO.Path]::GetTempFileName()
        
        aws s3 cp "s3://$S3Bucket/$s3Key" $tempFile --region $Region --only-show-errors 2>$null
        
        if ($LASTEXITCODE -eq 0 -and (Test-Path $tempFile)) {
            $tocData = Get-Content $tempFile -Raw | ConvertFrom-Json
            $entryCount = $tocData.entries.Count
            Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
            return $entryCount
        }
        
        Remove-Item $tempFile -Force -ErrorAction SilentlyContinue
        return $null
    } catch {
        return $null
    }
}

Write-Host "Analyzing processed books..." -ForegroundColor Cyan
if ($IncludeTOCComparison) {
    Write-Host "Fetching TOC data from S3 for comparison..." -ForegroundColor Cyan
    Write-Host "(This may take a while for many books)" -ForegroundColor Gray
}
Write-Host ""

# Collect book statistics
$bookStats = @()

# Get all artist directories
$artistDirs = Get-ChildItem -Path $OutputDir -Directory -ErrorAction SilentlyContinue

foreach ($artistDir in $artistDirs) {
    # Get all book directories for this artist
    $bookDirs = Get-ChildItem -Path $artistDir.FullName -Directory -ErrorAction SilentlyContinue
    
    foreach ($bookDir in $bookDirs) {
        # Get Songs directory
        $songsDir = Join-Path $bookDir.FullName "Songs"
        
        if (Test-Path $songsDir) {
            # Count PDF files
            $songFiles = Get-ChildItem -Path $songsDir -Filter "*.pdf" -File
            $songCount = $songFiles.Count
            
            # Extract unique artists from filenames
            $artists = @()
            foreach ($file in $songFiles) {
                # Extract artist from "Artist - Song.pdf" format
                if ($file.Name -match '^(.+?)\s*-\s*(.+)\.pdf$') {
                    $songArtist = $matches[1].Trim()
                    if ($artists -notcontains $songArtist) {
                        $artists += $songArtist
                    }
                }
            }
            
            # Determine potential issues
            $issues = @()
            
            # Issue 1: Very few songs (likely incomplete extraction)
            if ($songCount -lt 3) {
                $issues += "FEW_SONGS"
            }
            
            # Issue 2: Multiple artists in a single-artist book
            if ($artistDir.Name -ne "Various Artists" -and $artists.Count -gt 1) {
                $issues += "MULTIPLE_ARTISTS"
            }
            
            # Issue 3: Artist name mismatch (folder vs filename)
            $folderArtist = $artistDir.Name
            if ($artists.Count -eq 1 -and $artists[0] -ne $folderArtist -and $folderArtist -ne "Various Artists") {
                $issues += "ARTIST_MISMATCH"
            }
            
            # Issue 4: Songwriter names detected (common patterns)
            $songwriterPatterns = @("Young", "Johnson", "Lennon", "McCartney", "Words And Music")
            foreach ($artist in $artists) {
                foreach ($pattern in $songwriterPatterns) {
                    if ($artist -like "*$pattern*" -and $artist -like "*-*") {
                        $issues += "SONGWRITER_NAME"
                        break
                    }
                }
            }
            
            # Get expected count from TOC if requested
            $expectedCount = $null
            $extractionRate = $null
            
            if ($IncludeTOCComparison) {
                $bookId = Get-BookId -Artist $artistDir.Name -BookName $bookDir.Name
                $expectedCount = Get-TOCEntryCount -BookId $bookId
                
                if ($expectedCount -ne $null -and $expectedCount -gt 0) {
                    $extractionRate = [math]::Round(($songCount / $expectedCount) * 100, 1)
                    
                    # Issue 5: Low extraction rate
                    if ($extractionRate -lt 80) {
                        $issues += "LOW_EXTRACTION_RATE"
                    }
                }
            }
            
            $bookStats += [PSCustomObject]@{
                Artist = $artistDir.Name
                BookName = $bookDir.Name
                SongCount = $songCount
                ExpectedCount = if ($expectedCount -ne $null) { $expectedCount } else { "N/A" }
                ExtractionRate = if ($extractionRate -ne $null) { "$extractionRate%" } else { "N/A" }
                UniqueArtists = $artists.Count
                ArtistList = ($artists -join "; ")
                Issues = ($issues -join ", ")
                NeedsReview = ($issues.Count -gt 0)
                Path = $bookDir.FullName
            }
        }
    }
}

# Sort by issues first, then by song count
$bookStats = $bookStats | Sort-Object @{Expression={$_.NeedsReview}; Descending=$true}, SongCount

# Export to CSV
$bookStats | Export-Csv -Path $ReportFile -NoTypeInformation

Write-Host "Report generated: $ReportFile" -ForegroundColor Green
Write-Host ""

# Display summary statistics
$totalBooks = $bookStats.Count
$booksWithIssues = ($bookStats | Where-Object { $_.NeedsReview }).Count
$totalSongs = ($bookStats | Measure-Object -Property SongCount -Sum).Sum

Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total books processed: $totalBooks"
Write-Host "Total songs extracted: $totalSongs"
Write-Host "Books with potential issues: $booksWithIssues" -ForegroundColor $(if ($booksWithIssues -gt 0) { "Yellow" } else { "Green" })
Write-Host ""

# Display books needing review
if ($booksWithIssues -gt 0) {
    Write-Host "=== BOOKS NEEDING REVIEW ===" -ForegroundColor Yellow
    Write-Host ""
    
    $needsReview = $bookStats | Where-Object { $_.NeedsReview }
    
    foreach ($book in $needsReview) {
        Write-Host "$($book.Artist) - $($book.BookName)" -ForegroundColor White
        Write-Host "  Songs: $($book.SongCount)" -ForegroundColor Gray
        Write-Host "  Artists: $($book.ArtistList)" -ForegroundColor Gray
        Write-Host "  Issues: $($book.Issues)" -ForegroundColor Red
        Write-Host ""
    }
}

# Display books with very few songs (likely extraction failures)
$fewSongs = $bookStats | Where-Object { $_.SongCount -lt 5 } | Sort-Object SongCount
if ($fewSongs.Count -gt 0) {
    Write-Host "=== BOOKS WITH FEW SONGS (Possible Extraction Failures) ===" -ForegroundColor Red
    Write-Host ""
    
    foreach ($book in $fewSongs) {
        if ($book.ExpectedCount -ne "N/A") {
            Write-Host "$($book.Artist) - $($book.BookName): $($book.SongCount) songs (expected $($book.ExpectedCount), $($book.ExtractionRate))" -ForegroundColor Yellow
        } else {
            Write-Host "$($book.Artist) - $($book.BookName): $($book.SongCount) songs" -ForegroundColor Yellow
        }
    }
    Write-Host ""
}

# Display books with low extraction rate
if ($IncludeTOCComparison) {
    $lowExtraction = $bookStats | Where-Object { $_.ExtractionRate -ne "N/A" -and [int]($_.ExtractionRate -replace '%', '') -lt 80 } | Sort-Object { [int]($_.ExtractionRate -replace '%', '') }
    if ($lowExtraction.Count -gt 0) {
        Write-Host "=== BOOKS WITH LOW EXTRACTION RATE (<80%) ===" -ForegroundColor Red
        Write-Host ""
        
        foreach ($book in $lowExtraction) {
            Write-Host "$($book.Artist) - $($book.BookName): $($book.SongCount)/$($book.ExpectedCount) songs ($($book.ExtractionRate))" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

# Display statistics by artist
Write-Host "=== TOP 10 ARTISTS BY SONG COUNT ===" -ForegroundColor Cyan
$artistSummary = $bookStats | Group-Object Artist | ForEach-Object {
    [PSCustomObject]@{
        Artist = $_.Name
        Books = $_.Count
        TotalSongs = ($_.Group | Measure-Object -Property SongCount -Sum).Sum
    }
} | Sort-Object TotalSongs -Descending | Select-Object -First 10

$artistSummary | Format-Table -AutoSize

Write-Host ""
Write-Host "Full report saved to: $ReportFile" -ForegroundColor Green
Write-Host "Open in Excel to sort and filter by issues" -ForegroundColor Gray
