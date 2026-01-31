# Download Missing Files and Integrate into Reorganized Structure
# Uses the fresh comparison CSV to download missing files

param(
    [string]$CsvFile,
    [string]$BucketName = "jsmith-output",
    [string]$Profile = "default",
    [string]$DestinationRoot = ".\ProcessedSongs_Reorganized"
)

# Auto-detect the most recent fresh comparison CSV if not specified
if (-not $CsvFile) {
    $latestCsv = Get-ChildItem -Filter "missing-files-fresh-*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($latestCsv) {
        $CsvFile = $latestCsv.FullName
        Write-Host "Auto-detected CSV: $CsvFile" -ForegroundColor Cyan
    } else {
        Write-Host "ERROR: No CSV file specified and no fresh comparison CSV found" -ForegroundColor Red
        exit 1
    }
}

$ErrorActionPreference = "Continue"
$logFile = "download-missing-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Download Missing Files and Integrate ===" -Color Cyan
Write-Log "CSV File: $CsvFile"
Write-Log "Bucket: s3://$BucketName"
Write-Log "Destination: $DestinationRoot"
Write-Log ""

# Read CSV file
if (-not (Test-Path $CsvFile)) {
    Write-Log "ERROR: CSV file not found: $CsvFile" -Color Red
    exit 1
}

$missingFiles = Import-Csv $CsvFile

Write-Log "Found $($missingFiles.Count) missing files to download" -Color Green
Write-Log ""

$downloaded = 0
$skipped = 0
$errors = 0

foreach ($file in $missingFiles) {
    try {
        $s3Key = $file.S3Key
        $expectedLocalPath = $file.ExpectedLocalPath
        
        # Check if file already exists (using .NET to avoid wildcard issues)
        if ([System.IO.File]::Exists($expectedLocalPath)) {
            $skipped++
            continue
        }
        
        # Create directory if needed
        $destDir = [System.IO.Path]::GetDirectoryName($expectedLocalPath)
        if (-not [System.IO.Directory]::Exists($destDir)) {
            [System.IO.Directory]::CreateDirectory($destDir) | Out-Null
        }
        
        # Download from S3
        $s3Uri = "s3://$BucketName/$s3Key"
        aws s3 cp $s3Uri $expectedLocalPath --profile $Profile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $downloaded++
            if ($downloaded % 100 -eq 0) {
                Write-Log "Progress: $downloaded downloaded, $skipped skipped, $errors errors" -Color Cyan
            }
        } else {
            Write-Log "Error downloading: $s3Uri -> $expectedLocalPath" -Color Red
            $errors++
        }
        
    } catch {
        Write-Log "Error processing $($file.S3Key): $_" -Color Red
        $errors++
    }
}

Write-Log ""
Write-Log "=== Download Complete ===" -Color Cyan
Write-Log "Files downloaded: $downloaded"
Write-Log "Files skipped (already exist): $skipped"
Write-Log "Errors: $errors"
Write-Log ""

if ($downloaded -gt 0) {
    Write-Log "Successfully downloaded $downloaded files into reorganized structure!" -Color Green
}

Write-Log "Log file: $logFile" -Color Green
