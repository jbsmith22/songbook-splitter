# Download files with special characters and save with sanitized names locally

param(
    [string]$CsvFile = "missing-files-fresh-20260127-113716.csv",
    [string]$BucketName = "jsmith-output",
    [string]$Profile = "default"
)

$ErrorActionPreference = "Continue"
$logFile = "download-sanitized-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Sanitize-Filename {
    param($Filename)
    
    # Replace special characters with ASCII equivalents
    $sanitized = $Filename
    
    # Common accented characters
    $sanitized = $sanitized -replace 'é', 'e'
    $sanitized = $sanitized -replace 'è', 'e'
    $sanitized = $sanitized -replace 'ê', 'e'
    $sanitized = $sanitized -replace 'ë', 'e'
    $sanitized = $sanitized -replace 'á', 'a'
    $sanitized = $sanitized -replace 'à', 'a'
    $sanitized = $sanitized -replace 'â', 'a'
    $sanitized = $sanitized -replace 'ä', 'a'
    $sanitized = $sanitized -replace 'ó', 'o'
    $sanitized = $sanitized -replace 'ò', 'o'
    $sanitized = $sanitized -replace 'ô', 'o'
    $sanitized = $sanitized -replace 'ö', 'o'
    $sanitized = $sanitized -replace 'ú', 'u'
    $sanitized = $sanitized -replace 'ù', 'u'
    $sanitized = $sanitized -replace 'û', 'u'
    $sanitized = $sanitized -replace 'ü', 'u'
    $sanitized = $sanitized -replace 'ñ', 'n'
    $sanitized = $sanitized -replace 'ç', 'c'
    $sanitized = $sanitized -replace 'ï', 'i'
    $sanitized = $sanitized -replace 'í', 'i'
    
    # Replace question marks (often used as placeholder for unrecognized chars)
    $sanitized = $sanitized -replace '\?', 'e'
    
    return $sanitized
}

Write-Log "=== Download Files with Sanitized Names ===" -Color Cyan
Write-Log "CSV File: $CsvFile"
Write-Log "Bucket: s3://$BucketName"
Write-Log ""

# Read CSV
if (-not (Test-Path $CsvFile)) {
    Write-Log "ERROR: CSV file not found: $CsvFile" -Color Red
    exit 1
}

$missingFiles = Import-Csv $CsvFile

Write-Log "Found $($missingFiles.Count) files to download with sanitized names" -Color Green
Write-Log ""

$downloaded = 0
$skipped = 0
$errors = 0

foreach ($file in $missingFiles) {
    try {
        $s3Key = $file.S3Key
        $expectedLocalPath = $file.ExpectedLocalPath
        
        # Sanitize the filename
        $sanitizedPath = Sanitize-Filename $expectedLocalPath
        
        # Check if sanitized file already exists
        if ([System.IO.File]::Exists($sanitizedPath)) {
            Write-Log "Skipping (already exists): $sanitizedPath" -Color Gray
            $skipped++
            continue
        }
        
        # Create directory if needed
        $destDir = [System.IO.Path]::GetDirectoryName($sanitizedPath)
        if (-not [System.IO.Directory]::Exists($destDir)) {
            [System.IO.Directory]::CreateDirectory($destDir) | Out-Null
        }
        
        # Download from S3 to sanitized local path
        $s3Uri = "s3://$BucketName/$s3Key"
        aws s3 cp $s3Uri $sanitizedPath --profile $Profile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $downloaded++
            Write-Log "Downloaded: $sanitizedPath" -Color Green
            if ($downloaded % 10 -eq 0) {
                Write-Log "Progress: $downloaded downloaded, $skipped skipped, $errors errors" -Color Cyan
            }
        } else {
            Write-Log "Error downloading: $s3Uri -> $sanitizedPath" -Color Red
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
    Write-Log "Successfully downloaded $downloaded files with sanitized names!" -Color Green
}

Write-Log "Log file: $logFile" -Color Green
