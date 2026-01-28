# Reorganize Local Files to Proper Structure
# This script reorganizes existing local files to match the desired structure:
# - Artist\Book Title\<Artist> - <Song Title>.pdf
# - Uses folder artist name instead of composer from pages
# - Except for Various Artists, Broadway, Movie/TV where song-level artist is kept

param(
    [string]$SourceDir = ".\ProcessedSongs",
    [string]$OutputDir = ".\ProcessedSongs_Reorganized",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$logFile = "reorganize-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Get-SongTitle {
    param($Filename)
    # Extract song title from filename
    # Format is usually: "<Artist/Composer> - <Song Title>.pdf"
    if ($Filename -match ' - (.+)\.pdf$') {
        return $matches[1]
    }
    # If no dash, just remove .pdf
    return $Filename -replace '\.pdf$', ''
}

function Should-Keep-Original-Artist {
    param($Artist)
    # Keep original artist names for these categories
    $keepOriginal = @(
        'Various Artists',
        '_broadway Shows',
        '_movie And Tv',
        '_Fake Books'
    )
    return $keepOriginal -contains $Artist
}

Write-Log "=== Reorganize Local Files ===" -Color Cyan
Write-Log "Source: $SourceDir"
Write-Log "Output: $OutputDir"
if ($DryRun) {
    Write-Log "DRY RUN MODE - No changes will be made" -Color Yellow
}
Write-Log ""

# Get all song files
Write-Log "Scanning for song files..." -Color Cyan
$allSongs = Get-ChildItem -Path $SourceDir -Recurse -Filter "*.pdf" | Where-Object { $_.Directory.Name -eq "Songs" }
Write-Log "Found $($allSongs.Count) song files" -Color Green
Write-Log ""

$processed = 0
$renamed = 0
$moved = 0
$errors = 0
$changes = @()

foreach ($song in $allSongs) {
    $processed++
    
    if ($processed % 100 -eq 0) {
        Write-Log "Progress: $processed / $($allSongs.Count)" -Color Cyan
    }
    
    try {
        # Get the path components
        $fullPath = $song.FullName
        $sourceRoot = (Resolve-Path $SourceDir).Path
        $relativePath = $fullPath.Substring($sourceRoot.Length).TrimStart('\', '/')
        $pathParts = $relativePath -split '[/\\]'
        
        if ($pathParts.Count -lt 3) {
            Write-Log "Skipping invalid path: $relativePath" -Color Yellow
            continue
        }
        
        $artist = $pathParts[0]
        $book = $pathParts[1]
        $originalFilename = $song.Name
        
        # Determine new filename
        $newFilename = $originalFilename
        $willRename = $false
        if (-not (Should-Keep-Original-Artist $artist)) {
            # Replace artist name in filename with folder artist
            $songTitle = Get-SongTitle $originalFilename
            $newFilename = "$artist - $songTitle.pdf"
            
            if ($newFilename -ne $originalFilename) {
                $renamed++
                $willRename = $true
            }
        }
        
        # Construct new path: Artist\Book Title\Artist - Song.pdf
        $newPath = Join-Path $OutputDir "$artist\$book\$newFilename"
        
        # Track changes for CSV
        if ($DryRun) {
            $changes += [PSCustomObject]@{
                Artist = $artist
                Book = $book
                OriginalFilename = $originalFilename
                NewFilename = $newFilename
                WillRename = $willRename
                OriginalPath = $relativePath
                NewPath = "$artist\$book\$newFilename"
            }
        }
        
        # Create directory and copy file
        if (-not $DryRun) {
            $newDir = [System.IO.Path]::GetDirectoryName($newPath)
            if (-not (Test-Path -LiteralPath $newDir)) {
                [System.IO.Directory]::CreateDirectory($newDir) | Out-Null
            }
            
            # Use .NET method to avoid PowerShell wildcard issues
            [System.IO.File]::Copy($fullPath, $newPath, $true)
            $moved++
        } else {
            if ($newFilename -ne $originalFilename) {
                Write-Log "[DRY RUN] Would rename: $originalFilename -> $newFilename" -Color Yellow
            }
        }
        
    } catch {
        Write-Log "Error processing $($song.FullName): $_" -Color Red
        $errors++
    }
}

Write-Log ""
Write-Log "=== Reorganization Complete ===" -Color Cyan
Write-Log "Total files processed: $processed"
Write-Log "Files renamed: $renamed"
Write-Log "Files moved: $moved"
Write-Log "Errors: $errors"
Write-Log ""

# Export CSV in dry run mode
if ($DryRun -and $changes.Count -gt 0) {
    $csvFile = "reorganize-preview-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv"
    $changes | Export-Csv -Path $csvFile -NoTypeInformation -Encoding UTF8
    Write-Log "CSV preview saved to: $csvFile" -Color Green
    
    # Summary stats
    $willRenameCount = ($changes | Where-Object { $_.WillRename -eq $true }).Count
    $noChangeCount = ($changes | Where-Object { $_.WillRename -eq $false }).Count
    
    Write-Log ""
    Write-Log "=== DRY RUN SUMMARY ===" -Color Cyan
    Write-Log "Files that will be renamed: $willRenameCount" -Color Yellow
    Write-Log "Files that will keep original name: $noChangeCount" -Color Green
    Write-Log ""
    Write-Log "Review the CSV file for details: $csvFile" -Color Cyan
}

if (-not $DryRun) {
    Write-Log "New structure created in: $OutputDir" -Color Green
    Write-Log ""
    Write-Log "NEXT STEPS:" -Color Yellow
    Write-Log "1. Review the new structure in: $OutputDir" -Color Yellow
    Write-Log "2. If satisfied, delete old ProcessedSongs and rename:" -Color Yellow
    Write-Log "   Remove-Item .\ProcessedSongs -Recurse -Force" -Color Yellow
    Write-Log "   Rename-Item .\ProcessedSongs_Reorganized ProcessedSongs" -Color Yellow
}

Write-Log ""
Write-Log "Log file: $logFile" -Color Green
