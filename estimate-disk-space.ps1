# Estimate disk space needed for PDF verification

Write-Host "=== Disk Space Estimation for PDF Verification ===" -ForegroundColor Cyan
Write-Host ""

$pdfCount = 11976
$avgPagesPerPdf = 3.5  # Conservative estimate
$totalPages = [math]::Ceiling($pdfCount * $avgPagesPerPdf)

Write-Host "Assumptions:" -ForegroundColor Yellow
Write-Host "  Total PDFs: $pdfCount"
Write-Host "  Average pages per PDF: $avgPagesPerPdf"
Write-Host "  Total pages to render: $totalPages"
Write-Host ""

# PNG file size estimates (300 DPI)
$avgPngSizeKB = 150  # ~150KB per page at 300 DPI
$totalPngSizeGB = [math]::Round(($totalPages * $avgPngSizeKB) / 1024 / 1024, 2)

Write-Host "Rendered PNG Storage:" -ForegroundColor Yellow
Write-Host "  Average PNG size: $avgPngSizeKB KB"
Write-Host "  Total storage needed: $totalPngSizeGB GB"
Write-Host ""

# Progress/results storage
$resultsStorageGB = 0.5

Write-Host "Results Storage:" -ForegroundColor Yellow
Write-Host "  CSV files, logs, cache: $resultsStorageGB GB"
Write-Host ""

$totalNeededGB = [math]::Round($totalPngSizeGB + $resultsStorageGB, 2)
$recommendedGB = [math]::Round($totalNeededGB * 1.2, 2)  # 20% buffer

Write-Host "Total Disk Space:" -ForegroundColor Cyan
Write-Host "  Minimum needed: $totalNeededGB GB" -ForegroundColor Yellow
Write-Host "  Recommended (with buffer): $recommendedGB GB" -ForegroundColor Green
Write-Host ""

Write-Host "Options to reduce disk usage:" -ForegroundColor Yellow
Write-Host "  1. Process in batches and clean up between batches"
Write-Host "  2. Don't cache PNGs (re-render if needed)"
Write-Host "  3. Use lower DPI (150 instead of 300) - saves ~75% space"
Write-Host "  4. Use a different drive (D:, E:, external, etc.)"
Write-Host ""

# Check available drives
Write-Host "Available Drives:" -ForegroundColor Yellow
Get-WmiObject Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $freeGB = [math]::Round($_.FreeSpace / 1GB, 2)
    $totalGB = [math]::Round($_.Size / 1GB, 2)
    $pct = [math]::Round(($_.FreeSpace / $_.Size) * 100, 1)
    
    $color = "Green"
    if ($freeGB -lt $recommendedGB) { $color = "Yellow" }
    if ($freeGB -lt $totalNeededGB) { $color = "Red" }
    
    Write-Host "  $($_.DeviceID) - $freeGB GB free / $totalGB GB total ($pct%)" -ForegroundColor $color
}
