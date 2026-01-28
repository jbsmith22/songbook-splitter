# Reorganize S3 Bucket to Match Local Structure
# This script reorganizes S3 files from:
#   s3://bucket/artist/book/Songs/file.pdf
# To:
#   s3://bucket/artist/book/file.pdf
# And renames files to use artist name instead of composer (except Various Artists, Broadway, Movie/TV)

param(
    [string]$BucketName = "jsmith-output",
    [string]$Profile = "default",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$logFile = "reorganize-s3-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Get-SongTitle {
    param($Filename)
    # Extract song title from filename
    if ($Filename -match ' - (.+)\.pdf$') {
        return $matches[1]
    }
    return $Filename -replace '\.pdf$', ''
}

function Should-Keep-Original-Artist {
    param($Artist)
    $keepOriginal = @(
        'Various Artists',
        '_broadway Shows',
        '_movie And Tv',
        '_Fake Books'
    )
    return $keepOriginal -contains $Artist
}

Write-Log "=== Reorganize S3 Bucket ===" -Color Cyan
Write-Log "Bucket: s3://$BucketName"
Write-Log "Profile: $Profile"
if ($DryRun) {
    Write-Log "DRY RUN MODE - No changes will be made" -Color Yellow
}
Write-Log ""

# List all objects in the bucket
Write-Log "Listing all objects in S3 bucket..." -Color Cyan
$allObjects = aws s3api list-objects-v2 --bucket $BucketName --profile $Profile --output json | ConvertFrom-Json

if (-not $allObjects.Contents) {
    Write-Log "No objects found in bucket or error listing objects" -Color Red
    exit 1
}

Write-Log "Found $($allObjects.Contents.Count) total objects" -Color Green

# Filter for PDF files in Songs folders
$songFiles = $allObjects.Contents | Where-Object { 
    $_.Key -match '/Songs/.+\.pdf$' 
}

Write-Log "Found $($songFiles.Count) song files to reorganize" -Color Green
Write-Log ""

$processed = 0
$renamed = 0
$moved = 0
$errors = 0
$skipped = 0

foreach ($obj in $songFiles) {
    $processed++
    
    if ($processed % 100 -eq 0) {
        Write-Log "Progress: $processed / $($songFiles.Count)" -Color Cyan
    }
    
    try {
        $oldKey = $obj.Key
        
        # Parse the path: artist/book/Songs/filename.pdf
        $pathParts = $oldKey -split '/'
        
        if ($pathParts.Count -lt 4) {
            Write-Log "Skipping invalid path: $oldKey" -Color Yellow
            $skipped++
            continue
        }
        
        $artist = $pathParts[0]
        $book = $pathParts[1]
        $originalFilename = $pathParts[-1]
        
        # Determine new filename
        $newFilename = $originalFilename
        $willRename = $false
        
        if (-not (Should-Keep-Original-Artist $artist)) {
            $songTitle = Get-SongTitle $originalFilename
            $newFilename = "$artist - $songTitle.pdf"
            
            if ($newFilename -ne $originalFilename) {
                $renamed++
                $willRename = $true
            }
        }
        
        # Construct new key: artist/book/filename.pdf (no Songs folder)
        $newKey = "$artist/$book/$newFilename"
        
        if ($oldKey -eq $newKey) {
            Write-Log "Skipping unchanged: $oldKey" -Color Gray
            $skipped++
            continue
        }
        
        if ($DryRun) {
            Write-Log "[DRY RUN] Would copy: $oldKey -> $newKey" -Color Yellow
        } else {
            # Copy object to new location
            aws s3 cp "s3://$BucketName/$oldKey" "s3://$BucketName/$newKey" --profile $Profile 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                $moved++
                
                # Delete old object
                aws s3 rm "s3://$BucketName/$oldKey" --profile $Profile 2>&1 | Out-Null
                
                if ($LASTEXITCODE -ne 0) {
                    Write-Log "Warning: Copied but failed to delete old: $oldKey" -Color Yellow
                }
            } else {
                Write-Log "Error copying: $oldKey -> $newKey" -Color Red
                $errors++
            }
        }
        
    } catch {
        Write-Log "Error processing $($obj.Key): $_" -Color Red
        $errors++
    }
}

Write-Log ""
Write-Log "=== Reorganization Complete ===" -Color Cyan
Write-Log "Total files processed: $processed"
Write-Log "Files renamed: $renamed"
Write-Log "Files moved: $moved"
Write-Log "Files skipped: $skipped"
Write-Log "Errors: $errors"
Write-Log ""

if (-not $DryRun) {
    Write-Log "S3 bucket reorganized successfully!" -Color Green
    Write-Log ""
    Write-Log "NEXT STEPS:" -Color Yellow
    Write-Log "1. Verify the new structure in S3" -Color Yellow
    Write-Log "2. Clean up any remaining empty 'Songs' folders if needed" -Color Yellow
}

Write-Log ""
Write-Log "Log file: $logFile" -Color Green
