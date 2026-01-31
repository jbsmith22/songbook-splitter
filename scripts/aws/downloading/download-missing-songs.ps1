# Download Missing Songs from S3
# This script downloads songs that are in S3 but not in the local ProcessedSongs folder

param(
    [string]$S3Bucket = "jsmith-output",
    [string]$LocalOutputDir = ".\ProcessedSongs",
    [string]$Region = "us-east-1",
    [switch]$DryRun,
    [switch]$SkipExisting
)

$ErrorActionPreference = "Continue"
$logFile = "download-missing-songs-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Download Missing Songs ===" -Color Cyan
Write-Log "S3 Bucket: $S3Bucket"
Write-Log "Local Output: $LocalOutputDir"
Write-Log "Region: $Region"
if ($DryRun) {
    Write-Log "DRY RUN MODE - No files will be downloaded" -Color Yellow
}
if ($SkipExisting) {
    Write-Log "Skip Existing: Enabled" -Color Yellow
}
Write-Log ""

# Get all local songs
Write-Log "Scanning local songs..." -Color Cyan
$localSongs = @{}
$localFiles = Get-ChildItem -Path $LocalOutputDir -Recurse -Filter "*.pdf" | Where-Object { $_.Directory.Name -eq "Songs" }
foreach ($file in $localFiles) {
    $relativePath = $file.FullName.Replace((Resolve-Path $LocalOutputDir).Path, "").TrimStart('\', '/')
    $localSongs[$relativePath.ToLower()] = $true
}
Write-Log "Local songs: $($localSongs.Count)" -Color Green

# Get all S3 songs
Write-Log "Scanning S3 songs..." -Color Cyan
$s3Songs = aws s3 ls "s3://$S3Bucket/" --recursive --region $Region | Where-Object { $_ -match '/Songs/[^/]+\.pdf\s*$' }
$s3Count = ($s3Songs | Measure-Object).Count
Write-Log "S3 songs: $s3Count" -Color Green

# Find missing songs
Write-Log "`nFinding missing songs..." -Color Cyan
$missing = @()
foreach ($line in $s3Songs) {
    if ($line -match '^\s*[\d-]+\s+[\d:]+\s+(\d+)\s+(.+)$') {
        $size = [int]$matches[1]
        $s3Key = $matches[2].Trim()
        
        # Check if exists locally
        $localPath = $s3Key.ToLower()
        if (-not $localSongs.ContainsKey($localPath)) {
            $missing += [PSCustomObject]@{
                S3Key = $s3Key
                Size = $size
                LocalPath = Join-Path $LocalOutputDir $s3Key
            }
        }
    }
}

Write-Log "Missing songs: $($missing.Count)" -Color Yellow
Write-Log ""

if ($missing.Count -eq 0) {
    Write-Log "No missing songs found! Local and S3 are in sync." -Color Green
    exit 0
}

# Download missing songs
$downloaded = 0
$skipped = 0
$failed = 0
$totalSize = 0

foreach ($song in $missing) {
    $s3Uri = "s3://$S3Bucket/$($song.S3Key)"
    $localPath = $song.LocalPath
    
    # Check if file already exists (if SkipExisting is enabled)
    if ($SkipExisting -and (Test-Path $localPath)) {
        Write-Log "Skipping (exists): $($song.S3Key)" -Color Gray
        $skipped++
        continue
    }
    
    Write-Log "Downloading: $($song.S3Key)" -Color Cyan
    
    if (-not $DryRun) {
        # Create directory if needed
        $dir = Split-Path $localPath -Parent
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
        
        # Download file
        aws s3 cp $s3Uri $localPath --region $Region --only-show-errors
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  Downloaded: $([math]::Round($song.Size / 1KB, 2)) KB" -Color Green
            $downloaded++
            $totalSize += $song.Size
        } else {
            Write-Log "  Failed to download" -Color Red
            $failed++
        }
    } else {
        Write-Log "  [DRY RUN] Would download $([math]::Round($song.Size / 1KB, 2)) KB" -Color Yellow
        $downloaded++
        $totalSize += $song.Size
    }
}

Write-Log ""
Write-Log "=== Download Complete ===" -Color Cyan
Write-Log "Missing songs found: $($missing.Count)"
Write-Log "Downloaded: $downloaded"
Write-Log "Skipped: $skipped"
Write-Log "Failed: $failed"
Write-Log "Total size: $([math]::Round($totalSize / 1MB, 2)) MB"
Write-Log ""
Write-Log "Files saved to: $LocalOutputDir" -Color Green
Write-Log "Log file: $logFile" -Color Green
