# Compare S3 and Local Songs
# This script generates a detailed comparison report between S3 and local ProcessedSongs

param(
    [string]$S3Bucket = "jsmith-output",
    [string]$LocalOutputDir = ".\ProcessedSongs",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Continue"
$reportFile = "s3-local-comparison-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"

function Write-Report {
    param($Message)
    Write-Host $Message
    Add-Content -Path $reportFile -Value $Message
}

Write-Report "=== S3 vs Local Comparison Report ==="
Write-Report "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Report "S3 Bucket: $S3Bucket"
Write-Report "Local Directory: $LocalOutputDir"
Write-Report ""

# Build local song index (normalized paths)
Write-Host "Scanning local songs..." -ForegroundColor Cyan
$localSongs = @{}
$localFiles = Get-ChildItem -Path $LocalOutputDir -Recurse -Filter "*.pdf" | Where-Object { $_.Directory.Name -eq "Songs" }

foreach ($file in $localFiles) {
    # Get path relative to ProcessedSongs, normalize separators
    $fullPath = $file.FullName
    $localRoot = (Resolve-Path $LocalOutputDir).Path
    $relativePath = $fullPath.Substring($localRoot.Length).TrimStart('\', '/').Replace('\', '/')
    
    # Store with normalized path as key
    $localSongs[$relativePath] = $file.Length
}

Write-Report "Local Songs: $($localSongs.Count)"
Write-Report ""

# Get S3 songs
Write-Host "Scanning S3 songs (this may take a minute)..." -ForegroundColor Cyan
$s3Songs = @{}
$s3Output = aws s3 ls "s3://$S3Bucket/" --recursive --region $Region

foreach ($line in $s3Output) {
    # Parse S3 ls output: date time size key
    if ($line -match '^\s*([\d-]+)\s+([\d:]+)\s+(\d+)\s+(.+)$') {
        $size = [int]$matches[3]
        $key = $matches[4].Trim()
        
        # Only include files in Songs folders
        if ($key -match '/Songs/[^/]+\.pdf$') {
            $s3Songs[$key] = $size
        }
    }
}

Write-Report "S3 Songs: $($s3Songs.Count)"
Write-Report ""

# Find missing songs (in S3 but not local)
Write-Host "Finding missing songs..." -ForegroundColor Cyan
$missing = @()
foreach ($s3Key in $s3Songs.Keys) {
    if (-not $localSongs.ContainsKey($s3Key)) {
        $missing += [PSCustomObject]@{
            Path = $s3Key
            Size = $s3Songs[$s3Key]
        }
    }
}

# Find extra songs (in local but not S3)
$extra = @()
foreach ($localKey in $localSongs.Keys) {
    if (-not $s3Songs.ContainsKey($localKey)) {
        $extra += [PSCustomObject]@{
            Path = $localKey
            Size = $localSongs[$localKey]
        }
    }
}

# Summary
Write-Report "=== SUMMARY ==="
Write-Report "Total in S3: $($s3Songs.Count)"
Write-Report "Total Local: $($localSongs.Count)"
Write-Report "Missing (in S3, not local): $($missing.Count)"
Write-Report "Extra (in local, not S3): $($extra.Count)"
Write-Report ""

if ($missing.Count -eq 0 -and $extra.Count -eq 0) {
    Write-Report "✓ PERFECT SYNC - Local and S3 match exactly!"
    Write-Host "`n✓ PERFECT SYNC - Local and S3 match exactly!" -ForegroundColor Green
} else {
    if ($missing.Count -gt 0) {
        Write-Report "=== MISSING SONGS (in S3, not local) ==="
        Write-Report ""
        
        # Group by artist
        $missingByArtist = $missing | Group-Object { $_.Path.Split('/')[0] } | Sort-Object Name
        
        foreach ($group in $missingByArtist) {
            $totalSize = ($group.Group | Measure-Object -Property Size -Sum).Sum
            Write-Report "$($group.Name): $($group.Count) songs ($([math]::Round($totalSize / 1MB, 2)) MB)"
        }
        
        Write-Report ""
        Write-Report "First 50 missing files:"
        $missing | Select-Object -First 50 | ForEach-Object {
            Write-Report "  $($_.Path)"
        }
        
        if ($missing.Count -gt 50) {
            Write-Report "  ... and $($missing.Count - 50) more"
        }
        Write-Report ""
    }
    
    if ($extra.Count -gt 0) {
        Write-Report "=== EXTRA SONGS (in local, not S3) ==="
        Write-Report ""
        
        # Group by artist
        $extraByArtist = $extra | Group-Object { $_.Path.Split('/')[0] } | Sort-Object Name
        
        foreach ($group in $extraByArtist) {
            $totalSize = ($group.Group | Measure-Object -Property Size -Sum).Sum
            Write-Report "$($group.Name): $($group.Count) songs ($([math]::Round($totalSize / 1MB, 2)) MB)"
        }
        
        Write-Report ""
        Write-Report "First 50 extra files:"
        $extra | Select-Object -First 50 | ForEach-Object {
            Write-Report "  $($_.Path)"
        }
        
        if ($extra.Count -gt 50) {
            Write-Report "  ... and $($extra.Count - 50) more"
        }
        Write-Report ""
    }
}

Write-Report "=== END OF REPORT ==="
Write-Host "`nReport saved to: $reportFile" -ForegroundColor Green
Write-Host ""

# Display summary
if ($missing.Count -gt 0) {
    Write-Host "⚠ $($missing.Count) songs are in S3 but not downloaded locally" -ForegroundColor Yellow
    Write-Host "To download them, run: .\download-missing-songs.ps1" -ForegroundColor Cyan
}

if ($extra.Count -gt 0) {
    Write-Host "⚠ $($extra.Count) songs are local but not in S3" -ForegroundColor Yellow
}

if ($missing.Count -eq 0 -and $extra.Count -eq 0) {
    Write-Host "Everything is in sync!" -ForegroundColor Green
}
