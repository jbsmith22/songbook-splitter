# Find folders that are duplicates due to artist prefix variations

Write-Host "Finding artist-prefix duplicate folders..." -ForegroundColor Cyan
Write-Host ""

$csv = Import-Csv "strict-inventory-matched.csv"

# Group by source book
$grouped = $csv | Group-Object SourcePath | Where-Object { $_.Count -gt 1 }

Write-Host "Found $($grouped.Count) source books with multiple folders" -ForegroundColor Yellow
Write-Host ""

$duplicatesToDelete = @()

foreach ($group in $grouped) {
    $folders = $group.Group
    
    # Check if this is an artist-prefix duplicate pattern
    # Pattern: one folder has "Artist - Name", another has just "Name"
    if ($folders.Count -eq 2) {
        $folder1 = $folders[0]
        $folder2 = $folders[1]
        
        $artist = $folder1.Artist
        
        # Check if one has artist prefix and one doesn't
        $hasPrefix1 = $folder1.ProcessedFolder -like "$artist -*"
        $hasPrefix2 = $folder2.ProcessedFolder -like "$artist -*"
        
        if ($hasPrefix1 -and -not $hasPrefix2) {
            # folder1 has prefix, folder2 doesn't - delete folder1
            $duplicatesToDelete += $folder1
        } elseif ($hasPrefix2 -and -not $hasPrefix1) {
            # folder2 has prefix, folder1 doesn't - delete folder2
            $duplicatesToDelete += $folder2
        }
    }
}

Write-Host "Identified $($duplicatesToDelete.Count) duplicate folders to delete" -ForegroundColor Green
Write-Host ""

if ($duplicatesToDelete.Count -gt 0) {
    # Export list
    $duplicatesToDelete | Export-Csv "artist-prefix-duplicates-to-delete.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "List saved to: artist-prefix-duplicates-to-delete.csv" -ForegroundColor Cyan
    
    # Show summary
    $totalSongs = ($duplicatesToDelete | Measure-Object -Property SongCount -Sum).Sum
    Write-Host ""
    Write-Host "Summary:"
    Write-Host "  Folders to delete: $($duplicatesToDelete.Count)"
    Write-Host "  Songs in those folders: $totalSongs"
    Write-Host ""
    
    # Show first 20
    Write-Host "First 20 folders to delete:" -ForegroundColor Yellow
    $duplicatesToDelete | Select-Object -First 20 Artist, ProcessedFolder, SongCount | Format-Table -AutoSize
}
