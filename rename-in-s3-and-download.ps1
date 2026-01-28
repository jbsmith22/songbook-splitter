# Rename files in S3 to sanitized names, then download them

param(
    [string]$CsvFile = "missing-files-fresh-20260127-113716.csv",
    [string]$BucketName = "jsmith-output",
    [string]$Profile = "default"
)

$ErrorActionPreference = "Continue"
$logFile = "rename-s3-download-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

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
    
    # Replace question marks (placeholder for unrecognized chars)
    $sanitized = $sanitized -replace '\?', 'e'
    
    return $sanitized
}

Write-Log "=== Rename in S3 and Download ===" -Color Cyan
Write-Log "CSV File: $CsvFile"
Write-Log "Bucket: s3://$BucketName"
Write-Log ""

# Read CSV
if (-not (Test-Path $CsvFile)) {
    Write-Log "ERROR: CSV file not found: $CsvFile" -Color Red
    exit 1
}

$missingFiles = Import-Csv $CsvFile

Write-Log "Found $($missingFiles.Count) files to process" -Color Green
Write-Log ""

$renamed = 0
$downloaded = 0
$errors = 0

foreach ($file in $missingFiles) {
    try {
        $s3Key = $file.S3Key
        $expectedLocalPath = $file.ExpectedLocalPath
        
        # Sanitize the S3 key
        $sanitizedS3Key = Sanitize-Filename $s3Key
        $sanitizedLocalPath = Sanitize-Filename $expectedLocalPath
        
        Write-Log "Processing: $s3Key" -Color Cyan
        
        # Step 1: Copy to new sanitized name in S3
        $sourceUri = "s3://$BucketName/$s3Key"
        $destUri = "s3://$BucketName/$sanitizedS3Key"
        
        Write-Log "  Copying in S3: $s3Key -> $sanitizedS3Key" -Color Gray
        aws s3 cp $sourceUri $destUri --profile $Profile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "  ERROR: Failed to copy in S3" -Color Red
            $errors++
            continue
        }
        
        # Step 2: Delete old file in S3
        Write-Log "  Deleting old S3 file: $s3Key" -Color Gray
        aws s3 rm $sourceUri --profile $Profile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -ne 0) {
            Write-Log "  WARNING: Failed to delete old file, but copy succeeded" -Color Yellow
        }
        
        $renamed++
        
        # Step 3: Download the sanitized file
        $destDir = [System.IO.Path]::GetDirectoryName($sanitizedLocalPath)
        if (-not [System.IO.Directory]::Exists($destDir)) {
            [System.IO.Directory]::CreateDirectory($destDir) | Out-Null
        }
        
        Write-Log "  Downloading: $sanitizedS3Key" -Color Gray
        aws s3 cp $destUri $sanitizedLocalPath --profile $Profile 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            $downloaded++
            Write-Log "  SUCCESS: Downloaded to $sanitizedLocalPath" -Color Green
        } else {
            Write-Log "  ERROR: Failed to download" -Color Red
            $errors++
        }
        
        if ($downloaded % 10 -eq 0) {
            Write-Log ""
            Write-Log "Progress: $renamed renamed, $downloaded downloaded, $errors errors" -Color Cyan
            Write-Log ""
        }
        
    } catch {
        Write-Log "ERROR processing $($file.S3Key): $_" -Color Red
        $errors++
    }
}

Write-Log ""
Write-Log "=== Process Complete ===" -Color Cyan
Write-Log "Files renamed in S3: $renamed"
Write-Log "Files downloaded: $downloaded"
Write-Log "Errors: $errors"
Write-Log ""

if ($downloaded -gt 0) {
    Write-Log "Successfully processed $downloaded files!" -Color Green
}

Write-Log "Log file: $logFile" -Color Green
