# Get Missing Files CSV
# This script generates a CSV list of files that are in S3 but not local

param(
    [string]$S3Bucket = "jsmith-output",
    [string]$LocalOutputDir = ".\ProcessedSongs",
    [string]$Region = "us-east-1",
    [string]$OutputCsv = "missing-files-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv"
)

$ErrorActionPreference = "Continue"

Write-Host "Scanning local songs..." -ForegroundColor Cyan
$localSongs = @{}
$localFiles = Get-ChildItem -Path $LocalOutputDir -Recurse -Filter "*.pdf" | Where-Object { $_.Directory.Name -eq "Songs" }

foreach ($file in $localFiles) {
    $fullPath = $file.FullName
    $localRoot = (Resolve-Path $LocalOutputDir).Path
    $relativePath = $fullPath.Substring($localRoot.Length).TrimStart('\', '/')
    # Normalize to forward slashes for comparison with S3
    $normalizedPath = $relativePath.Replace('\', '/')
    $localSongs[$normalizedPath] = $true
}

Write-Host "Local songs: $($localSongs.Count)"

Write-Host "Scanning S3 songs..." -ForegroundColor Cyan
$s3Output = aws s3 ls "s3://$S3Bucket/" --recursive --region $Region

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error accessing S3. Please run: aws sso login" -ForegroundColor Red
    exit 1
}

$missing = @()
foreach ($line in $s3Output) {
    if ($line -match '^\s*([\d-]+)\s+([\d:]+)\s+(\d+)\s+(.+)$') {
        $date = $matches[1]
        $time = $matches[2]
        $size = [int]$matches[3]
        $key = $matches[4].Trim()
        
        # Only include files in Songs folders
        if ($key -match '/Songs/[^/]+\.pdf$') {
            # Normalize key (should already be forward slashes from S3)
            $normalizedKey = $key.Replace('\', '/')
            if (-not $localSongs.ContainsKey($normalizedKey)) {
                # Parse artist and book from path
                $parts = $key -split '/'
                $artist = $parts[0]
                $book = if ($parts.Count -gt 1) { $parts[1] } else { "" }
                $filename = $parts[-1]
                
                $missing += [PSCustomObject]@{
                    Artist = $artist
                    Book = $book
                    Filename = $filename
                    S3Path = $key
                    Size = $size
                    LastModified = "$date $time"
                }
            }
        }
    }
}

Write-Host "Missing songs: $($missing.Count)" -ForegroundColor Yellow

if ($missing.Count -eq 0) {
    Write-Host "No missing files! Everything is in sync." -ForegroundColor Green
    exit 0
}

# Export to CSV
$missing | Export-Csv -Path $OutputCsv -NoTypeInformation -Encoding UTF8

Write-Host "`nCSV saved to: $OutputCsv" -ForegroundColor Green
Write-Host "Total missing: $($missing.Count) files"

# Show summary by artist
Write-Host "`nMissing files by artist:"
$missing | Group-Object Artist | Sort-Object Count -Descending | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Count) files"
}
