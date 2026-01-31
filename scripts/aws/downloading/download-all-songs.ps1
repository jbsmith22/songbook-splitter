# Download All Processed Songs from S3
# This script downloads all successfully processed songs from S3 to local directories

param(
    [string]$S3Bucket = "jsmith-output",
    [string]$LocalOutputDir = ".\ProcessedSongs",
    [string]$Region = "us-east-1",
    [switch]$DryRun,
    [switch]$SkipExisting
)

$ErrorActionPreference = "Continue"
$logFile = "download-all-songs-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Song Download Script ===" -Color Cyan
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

# Create output directory
if (-not $DryRun) {
    New-Item -ItemType Directory -Path $LocalOutputDir -Force | Out-Null
}

# List all objects in the bucket that match the pattern */Songs/*.pdf
Write-Log "Scanning S3 bucket for song files..." -Color Cyan

$allFiles = aws s3 ls "s3://$S3Bucket/" --recursive --region $Region | 
    Where-Object { $_ -match '/Songs/.*\.pdf$' } |
    ForEach-Object {
        if ($_ -match '^\s*[\d-]+\s+[\d:]+\s+(\d+)\s+(.+)$') {
            [PSCustomObject]@{
                Size = [int]$matches[1]
                Key = $matches[2]
            }
        }
    }

Write-Log "Found $($allFiles.Count) song files" -Color Green
Write-Log ""

$downloaded = 0
$skipped = 0
$failed = 0
$totalSize = 0

foreach ($file in $allFiles) {
    $s3Uri = "s3://$S3Bucket/$($file.Key)"
    $localPath = Join-Path $LocalOutputDir $file.Key
    
    # Check if file already exists locally
    if ($SkipExisting -and (Test-Path $localPath)) {
        Write-Log "Skipping (exists): $($file.Key)" -Color Gray
        $skipped++
        continue
    }
    
    Write-Log "Downloading: $($file.Key)" -Color Cyan
    
    if (-not $DryRun) {
        # Create directory if needed
        $dir = Split-Path $localPath -Parent
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        
        # Download file
        aws s3 cp $s3Uri $localPath --region $Region --only-show-errors
        
        if ($LASTEXITCODE -eq 0) {
            Write-Log "  Downloaded: $([math]::Round($file.Size / 1KB, 2)) KB" -Color Green
            $downloaded++
            $totalSize += $file.Size
        } else {
            Write-Log "  Failed to download" -Color Red
            $failed++
        }
    } else {
        Write-Log "  [DRY RUN] Would download $([math]::Round($file.Size / 1KB, 2)) KB" -Color Yellow
        $downloaded++
        $totalSize += $file.Size
    }
}

Write-Log ""
Write-Log "=== Download Complete ===" -Color Cyan
Write-Log "Total files found: $($allFiles.Count)"
Write-Log "Downloaded: $downloaded"
Write-Log "Skipped: $skipped"
Write-Log "Failed: $failed"
Write-Log "Total size: $([math]::Round($totalSize / 1MB, 2)) MB"
Write-Log ""
Write-Log "Files saved to: $LocalOutputDir" -Color Green
Write-Log "Log file: $logFile" -Color Green
