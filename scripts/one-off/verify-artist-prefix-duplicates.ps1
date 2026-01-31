# Verify artist-prefix duplicates by comparing file hashes

Write-Host "Verifying artist-prefix duplicate folders with hash comparison..." -ForegroundColor Cyan
Write-Host ""

$csv = Import-Csv "strict-inventory-matched.csv"

# Group by source book
$grouped = $csv | Group-Object SourcePath | Where-Object { $_.Count -gt 1 }

Write-Host "Found $($grouped.Count) source books with multiple folders" -ForegroundColor Yellow
Write-Host ""

$trueDuplicates = @()
$notDuplicates = @()
$processed = 0

foreach ($group in $grouped) {
    $folders = $group.Group
    
    # Only handle pairs for now
    if ($folders.Count -eq 2) {
        $processed++
        if ($processed % 20 -eq 0) {
            Write-Host "Progress: $processed / $($grouped.Count)..." -ForegroundColor Gray
        }
        
        $folder1 = $folders[0]
        $folder2 = $folders[1]
        
        $artist = $folder1.Artist
        
        # Check if one has artist prefix and one doesn't
        $hasPrefix1 = $folder1.ProcessedFolder -like "$artist -*"
        $hasPrefix2 = $folder2.ProcessedFolder -like "$artist -*"
        
        if (($hasPrefix1 -and -not $hasPrefix2) -or ($hasPrefix2 -and -not $hasPrefix1)) {
            # This is an artist-prefix pattern - verify with hashes
            
            # Get all PDFs from both folders
            try {
                $pdfs1 = [System.IO.Directory]::GetFiles($folder1.ProcessedPath, "*.pdf", [System.IO.SearchOption]::AllDirectories)
                $pdfs2 = [System.IO.Directory]::GetFiles($folder2.ProcessedPath, "*.pdf", [System.IO.SearchOption]::AllDirectories)
            } catch {
                continue
            }
            
            # Create signatures for both folders
            $sig1 = @()
            foreach ($pdf in $pdfs1 | Sort-Object) {
                $fileName = [System.IO.Path]::GetFileName($pdf)
                $hash = (Get-FileHash -Path $pdf -Algorithm MD5).Hash
                $sig1 += "$fileName|$hash"
            }
            
            $sig2 = @()
            foreach ($pdf in $pdfs2 | Sort-Object) {
                $fileName = [System.IO.Path]::GetFileName($pdf)
                $hash = (Get-FileHash -Path $pdf -Algorithm MD5).Hash
                $sig2 += "$fileName|$hash"
            }
            
            # Compare signatures
            $signature1 = ($sig1 | Sort-Object) -join "::"
            $signature2 = ($sig2 | Sort-Object) -join "::"
            
            if ($signature1 -eq $signature2) {
                # TRUE DUPLICATE - same files
                # Delete the one with the artist prefix
                if ($hasPrefix1) {
                    $trueDuplicates += $folder1
                } else {
                    $trueDuplicates += $folder2
                }
            } else {
                # NOT a duplicate - different files
                $notDuplicates += [PSCustomObject]@{
                    Artist = $artist
                    SourceBook = $folder1.SourceBook
                    Folder1 = $folder1.ProcessedFolder
                    Folder1Songs = $folder1.SongCount
                    Folder2 = $folder2.ProcessedFolder
                    Folder2Songs = $folder2.SongCount
                }
            }
        }
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "Verification Complete"
Write-Host "================================================================================"
Write-Host ""
Write-Host "TRUE duplicates (identical files): $($trueDuplicates.Count)"
Write-Host "NOT duplicates (different files): $($notDuplicates.Count)"
Write-Host ""

if ($trueDuplicates.Count -gt 0) {
    $trueDuplicates | Export-Csv "verified-duplicates-to-delete.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "True duplicates saved to: verified-duplicates-to-delete.csv" -ForegroundColor Cyan
    
    $totalSongs = ($trueDuplicates | Measure-Object -Property SongCount -Sum).Sum
    Write-Host "  Folders to delete: $($trueDuplicates.Count)"
    Write-Host "  Songs in those folders: $totalSongs"
}

if ($notDuplicates.Count -gt 0) {
    $notDuplicates | Export-Csv "not-duplicates-different-content.csv" -NoTypeInformation -Encoding UTF8
    Write-Host ""
    Write-Host "NOT duplicates saved to: not-duplicates-different-content.csv" -ForegroundColor Yellow
    Write-Host "These folders have different content and should NOT be deleted!"
    Write-Host ""
    Write-Host "First 20 non-duplicates:" -ForegroundColor Yellow
    $notDuplicates | Select-Object -First 20 Artist, Folder1, Folder1Songs, Folder2, Folder2Songs | Format-Table -AutoSize
}

Write-Host "================================================================================"
