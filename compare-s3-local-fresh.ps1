# Fresh Comparison: S3 vs Local Reorganized Folder
# This will tell us exactly what files are in S3 but not in our reorganized local folder

param(
    [string]$BucketName = "jsmith-output",
    [string]$Profile = "default",
    [string]$LocalRoot = ".\ProcessedSongs_Reorganized"
)

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = "fresh-comparison-$timestamp.log"
$csvFile = "missing-files-fresh-$timestamp.csv"

function Write-Log {
    param($Message, $Color = "White")
    $logTimestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$logTimestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

Write-Log "=== Fresh S3 vs Local Comparison ===" -Color Cyan
Write-Log "S3 Bucket: s3://$BucketName"
Write-Log "Local Root: $LocalRoot"
Write-Log ""

# Step 1: Get all S3 files
Write-Log "Step 1: Listing all S3 files..." -Color Cyan
$s3Objects = aws s3api list-objects-v2 --bucket $BucketName --profile $Profile --output json | ConvertFrom-Json

if (-not $s3Objects.Contents) {
    Write-Log "ERROR: Failed to list S3 objects" -Color Red
    exit 1
}

# Filter for PDF files in Songs folders
$s3SongFiles = $s3Objects.Contents | Where-Object { 
    $_.Key -match '/Songs/.+\.pdf$' 
}

Write-Log "Found $($s3SongFiles.Count) song files in S3" -Color Green
Write-Log ""

# Step 2: Build expected local paths for each S3 file
Write-Log "Step 2: Building expected local paths..." -Color Cyan

$s3FileMap = @{}
foreach ($s3File in $s3SongFiles) {
    $key = $s3File.Key
    
    # Parse: artist/book/Songs/filename.pdf
    $parts = $key -split '/'
    if ($parts.Count -lt 4) { continue }
    
    $artist = $parts[0]
    $book = $parts[1]
    $filename = $parts[-1]
    
    # Determine expected filename in reorganized structure
    $expectedFilename = $filename
    
    # For non-Various Artists, we rename to use artist name
    $keepOriginalArtist = @('Various Artists', '_broadway Shows', '_movie And Tv', '_Fake Books')
    if ($keepOriginalArtist -notcontains $artist) {
        # Extract song title
        if ($filename -match ' - (.+)\.pdf$') {
            $songTitle = $matches[1]
            $expectedFilename = "$artist - $songTitle.pdf"
        }
    }
    
    # Expected local path
    $expectedLocalPath = Join-Path $LocalRoot "$artist\$book\$expectedFilename"
    
    $s3FileMap[$key] = @{
        Artist = $artist
        Book = $book
        OriginalFilename = $filename
        ExpectedFilename = $expectedFilename
        ExpectedLocalPath = $expectedLocalPath
        S3Key = $key
        Size = $s3File.Size
        LastModified = $s3File.LastModified
    }
}

Write-Log "Mapped $($s3FileMap.Count) S3 files to expected local paths" -Color Green
Write-Log ""

# Step 3: Check which files are missing locally
Write-Log "Step 3: Checking which files exist locally..." -Color Cyan

$missingFiles = @()
$existingFiles = 0

foreach ($key in $s3FileMap.Keys) {
    $fileInfo = $s3FileMap[$key]
    $localPath = $fileInfo.ExpectedLocalPath
    
    # Use .NET method to avoid wildcard issues with Test-Path
    if (-not [System.IO.File]::Exists($localPath)) {
        $missingFiles += $fileInfo
    } else {
        $existingFiles++
    }
}

Write-Log ""
Write-Log "=== Comparison Results ===" -Color Cyan
Write-Log "Total S3 files: $($s3FileMap.Count)"
Write-Log "Files found locally: $existingFiles" -Color Green
Write-Log "Files MISSING locally: $($missingFiles.Count)" -Color Yellow
Write-Log ""

# Step 4: Export missing files to CSV
if ($missingFiles.Count -gt 0) {
    Write-Log "Exporting missing files to CSV: $csvFile" -Color Cyan
    
    $csvData = $missingFiles | ForEach-Object {
        [PSCustomObject]@{
            Artist = $_.Artist
            Book = $_.Book
            OriginalFilename = $_.OriginalFilename
            ExpectedFilename = $_.ExpectedFilename
            S3Key = $_.S3Key
            ExpectedLocalPath = $_.ExpectedLocalPath
            Size = $_.Size
            LastModified = $_.LastModified
        }
    }
    
    $csvData | Export-Csv -Path $csvFile -NoTypeInformation
    Write-Log "Missing files exported to: $csvFile" -Color Green
} else {
    Write-Log "No missing files found! Local and S3 are in sync." -Color Green
}

Write-Log ""
Write-Log "Log file: $logFile" -Color Green
