# Sync from S3 with Proper Structure
# This script downloads all songs from S3 with the correct folder structure and naming

param(
    [string]$S3Bucket = "jsmith-output",
    [string]$LocalOutputDir = ".\ProcessedSongs",
    [string]$Region = "us-east-1",
    [switch]$DryRun,
    [switch]$BackupOld
)

$ErrorActionPreference = "Continue"
$logFile = "sync-from-s3-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Sync from S3 with Proper Structure ===" -Color Cyan
Write-Log "S3 Bucket: $S3Bucket"
Write-Log "Local Output: $LocalOutputDir"
Write-Log "Region: $Region"
if ($DryRun) {
    Write-Log "DRY RUN MODE - No changes will be made" -Color Yellow
}
if ($BackupOld) {
    Write-Log "Backup Old: Enabled" -Color Yellow
}
Write-Log ""

# Backup existing structure if requested
if ($BackupOld -and -not $DryRun) {
    $backupDir = ".\ProcessedSongs_backup_$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    Write-Log "Creating backup: $backupDir" -Color Yellow
    Copy-Item -Path $LocalOutputDir -Destination $backupDir -Recurse -Force
    Write-Log "Backup complete" -Color Green
    Write-Log ""
}

# Use AWS CLI sync to download everything with proper structure
Write-Log "Syncing from S3..." -Color Cyan
Write-Log "This will download all files and organize them properly" -Color Cyan
Write-Log ""

if (-not $DryRun) {
    # Sync from S3 - this will download everything with the correct structure
    aws s3 sync "s3://$S3Bucket/" $LocalOutputDir --region $Region --exclude "*" --include "*/Songs/*.pdf"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Log "Sync complete!" -Color Green
    } else {
        Write-Log "Sync failed with exit code: $LASTEXITCODE" -Color Red
        exit 1
    }
} else {
    Write-Log "[DRY RUN] Would execute:" -Color Yellow
    Write-Log "  aws s3 sync s3://$S3Bucket/ $LocalOutputDir --region $Region --exclude '*' --include '*/Songs/*.pdf'" -Color Yellow
}

Write-Log ""
Write-Log "=== Sync Complete ===" -Color Cyan
Write-Log "Files are now organized with proper book folders" -Color Green
Write-Log "Log file: $logFile" -Color Green
