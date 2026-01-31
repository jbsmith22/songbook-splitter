# Find duplicate folders by comparing MD5 hashes of all files in each folder

Write-Host "Scanning for duplicate folders in ProcessedSongs..." -ForegroundColor Cyan
Write-Host "This may take a while..." -ForegroundColor Yellow
Write-Host ""

$results = @()
$folderHashes = @{}

# Get all book folders
$artistFolders = Get-ChildItem "ProcessedSongs" -Directory

$totalFolders = 0
foreach ($artistDir in $artistFolders) {
    $bookFolders = Get-ChildItem $artistDir.FullName -Directory
    $totalFolders += $bookFolders.Count
}

Write-Host "Found $totalFolders folders to analyze" -ForegroundColor Green
Write-Host ""

$processed = 0
foreach ($artistDir in $artistFolders) {
    $bookFolders = Get-ChildItem $artistDir.FullName -Directory
    
    foreach ($bookFolder in $bookFolders) {
        $processed++
        if ($processed % 50 -eq 0) {
            Write-Host "Progress: $processed / $totalFolders folders..." -ForegroundColor Gray
        }
        
        # Get all PDFs in this folder
        try {
            $pdfs = [System.IO.Directory]::GetFiles($bookFolder.FullName, "*.pdf", [System.IO.SearchOption]::AllDirectories)
        } catch {
            $pdfs = @()
        }
        
        if ($pdfs.Count -eq 0) {
            continue
        }
        
        # Create a signature for this folder: sorted list of (filename, hash) pairs
        $fileSignatures = @()
        foreach ($pdf in $pdfs | Sort-Object) {
            $fileName = [System.IO.Path]::GetFileName($pdf)
            $hash = (Get-FileHash -Path $pdf -Algorithm MD5).Hash
            $fileSignatures += "$fileName|$hash"
        }
        
        # Create folder signature
        $folderSignature = ($fileSignatures | Sort-Object) -join "::"
        
        # Store folder info
        $folderInfo = @{
            Artist = $artistDir.Name
            Folder = $bookFolder.Name
            Path = $bookFolder.FullName
            FileCount = $pdfs.Count
            Signature = $folderSignature
        }
        
        # Check if we've seen this signature before
        if ($folderHashes.ContainsKey($folderSignature)) {
            # Duplicate found!
            $original = $folderHashes[$folderSignature]
            $results += [PSCustomObject]@{
                OriginalArtist = $original.Artist
                OriginalFolder = $original.Folder
                OriginalPath = $original.Path
                DuplicateArtist = $folderInfo.Artist
                DuplicateFolder = $folderInfo.Folder
                DuplicatePath = $folderInfo.Path
                FileCount = $folderInfo.FileCount
            }
        } else {
            $folderHashes[$folderSignature] = $folderInfo
        }
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "Duplicate Folder Analysis Complete"
Write-Host "================================================================================"
Write-Host ""
Write-Host "Total folders analyzed: $totalFolders"
Write-Host "Unique folders: $($folderHashes.Count)"
Write-Host "Duplicate folders found: $($results.Count)"
Write-Host ""

if ($results.Count -gt 0) {
    Write-Host "Duplicate folders:" -ForegroundColor Yellow
    $results | Format-Table -AutoSize
    
    # Export to CSV
    $results | Export-Csv "duplicate-folders.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Duplicate list saved to: duplicate-folders.csv" -ForegroundColor Cyan
    
    # Calculate how many files would be freed
    $totalDuplicateFiles = ($results | Measure-Object -Property FileCount -Sum).Sum
    Write-Host ""
    Write-Host "If all duplicates are removed:"
    Write-Host "  - $($results.Count) folders would be deleted"
    Write-Host "  - $totalDuplicateFiles files would be freed"
    Write-Host "  - Remaining folders: $($totalFolders - $results.Count)"
} else {
    Write-Host "No duplicate folders found!" -ForegroundColor Green
}

Write-Host "================================================================================"
