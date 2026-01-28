# Process All Sheet Music Books - Overnight Batch Job
# This script scans the local SheetMusic directory, uploads PDFs to S3,
# and submits Step Functions executions for processing.

param(
    [string]$SheetMusicDir = ".\SheetMusic",
    [string]$S3Bucket = "jsmith-input",
    [string]$S3Prefix = "SheetMusic",
    [string]$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline",
    [string]$Region = "us-east-1",
    [int]$MaxConcurrent = 20,
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"
$logFile = "process-all-books-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

function Write-Log {
    param($Message, $Color = "White")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage -ForegroundColor $Color
    Add-Content -Path $logFile -Value $logMessage
}

function Get-BookId {
    param($Artist, $BookName)
    # Create a unique book ID from artist and book name
    $combined = "$Artist-$BookName"
    $sanitized = $combined -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-' -replace '^-|-$', ''
    return $sanitized.ToLower()
}

function Upload-ToS3 {
    param($LocalPath, $S3Uri)
    
    try {
        # Check if file already exists in S3
        $bucket = $S3Uri -replace 's3://([^/]+)/.*', '$1'
        $key = $S3Uri -replace 's3://[^/]+/', ''
        
        $exists = aws s3 ls "s3://$bucket/$key" --region $Region 2>$null
        if ($exists) {
            Write-Log "  File already in S3: $S3Uri" -Color Gray
            return $true
        }
        
        Write-Log "  Uploading to S3: $S3Uri" -Color Cyan
        if (-not $DryRun) {
            aws s3 cp $LocalPath $S3Uri --region $Region --only-show-errors
            if ($LASTEXITCODE -eq 0) {
                Write-Log "  Upload complete" -Color Green
                return $true
            } else {
                Write-Log "  Upload failed" -Color Red
                return $false
            }
        } else {
            Write-Log "  [DRY RUN] Would upload" -Color Yellow
            return $true
        }
    } catch {
        Write-Log "  Error uploading: $_" -Color Red
        return $false
    }
}

function Start-BookProcessing {
    param($BookId, $S3Uri, $Artist, $BookName)
    
    try {
        $inputObj = @{
            book_id = $BookId
            source_pdf_uri = $S3Uri
            artist = $Artist
            book_name = $BookName
        }
        
        # Convert to JSON
        $inputJson = ($inputObj | ConvertTo-Json -Compress -Depth 10)
        
        Write-Log "  Starting execution for: $BookId" -Color Cyan
        
        if (-not $DryRun) {
            # Write JSON to temp file with UTF-8 no BOM encoding
            $tempFile = [System.IO.Path]::GetTempFileName()
            $utf8NoBom = New-Object System.Text.UTF8Encoding $false
            [System.IO.File]::WriteAllText($tempFile, $inputJson, $utf8NoBom)
            
            try {
                $result = aws stepfunctions start-execution `
                    --state-machine-arn $StateMachineArn `
                    --input "file://$tempFile" `
                    --region $Region 2>&1
                
                if ($LASTEXITCODE -eq 0) {
                    $execution = $result | ConvertFrom-Json
                    Write-Log "  Execution started: $($execution.executionArn)" -Color Green
                    return $execution.executionArn
                } else {
                    Write-Log "  Failed to start execution: $result" -Color Red
                    return $null
                }
            } finally {
                Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
            }
        } else {
            Write-Log "  [DRY RUN] Would start execution with input: $inputJson" -Color Yellow
            return "dry-run-execution"
        }
    } catch {
        Write-Log "  Error starting execution: $_" -Color Red
        return $null
    }
}

function Get-RunningExecutions {
    try {
        $result = aws stepfunctions list-executions `
            --state-machine-arn $StateMachineArn `
            --status-filter RUNNING `
            --region $Region `
            --query "executions[].executionArn" `
            --output json 2>$null
        
        if ($LASTEXITCODE -eq 0) {
            $executions = $result | ConvertFrom-Json
            return $executions.Count
        }
        return 0
    } catch {
        return 0
    }
}

# Main script
Write-Log "=== Sheet Music Batch Processor ===" -Color Cyan
Write-Log "Sheet Music Directory: $SheetMusicDir"
Write-Log "S3 Bucket: $S3Bucket"
Write-Log "State Machine: $StateMachineArn"
Write-Log "Max Concurrent: $MaxConcurrent"
if ($DryRun) {
    Write-Log "DRY RUN MODE - No actual changes will be made" -Color Yellow
}
Write-Log ""

# Find all PDF files in Books subdirectories
Write-Log "Scanning for PDF files..." -Color Cyan
$pdfFiles = Get-ChildItem -Path $SheetMusicDir -Recurse -Filter "*.pdf" | 
    Where-Object { $_.Directory.Name -eq "Books" -or $_.Directory.Name -eq "books" }

Write-Log "Found $($pdfFiles.Count) PDF files in Books directories" -Color Green
Write-Log ""

# Process each PDF
$processed = 0
$uploaded = 0
$started = 0
$skipped = 0
$failed = 0

foreach ($pdf in $pdfFiles) {
    $processed++
    
    # Extract artist and book name from path
    # Expected: SheetMusic\<Artist>\Books\<BookFile>.pdf
    $fullPath = $pdf.FullName
    $sheetMusicPath = (Resolve-Path $SheetMusicDir).Path
    
    if (-not $fullPath.StartsWith($sheetMusicPath)) {
        Write-Log "[$processed/$($pdfFiles.Count)] Skipping (path mismatch): $fullPath" -Color Yellow
        $skipped++
        continue
    }
    
    $relativePath = $fullPath.Substring($sheetMusicPath.Length).TrimStart('\', '/')
    $pathParts = $relativePath -split '[/\\]'
    
    if ($pathParts.Count -lt 3) {
        Write-Log "[$processed/$($pdfFiles.Count)] Skipping (invalid path): $relativePath" -Color Yellow
        $skipped++
        continue
    }
    
    $artist = $pathParts[0]
    $bookFileName = $pdf.Name
    
    # Extract book name from filename (remove .pdf extension)
    $bookName = $bookFileName -replace '\.pdf$', ''
    
    # Try to remove artist prefix if present
    if ($bookName -match "^$([regex]::Escape($artist))\s*-\s*(.+)$") {
        $bookName = $matches[1]
    }
    
    Write-Log "[$processed/$($pdfFiles.Count)] Processing: $artist - $bookName" -Color White
    
    # Generate book ID
    $bookId = Get-BookId -Artist $artist -BookName $bookName
    
    # Construct S3 URI
    $s3Key = "$S3Prefix/$artist/books/$bookFileName"
    $s3Uri = "s3://$S3Bucket/$s3Key"
    
    # Upload to S3
    $uploadSuccess = Upload-ToS3 -LocalPath $pdf.FullName -S3Uri $s3Uri
    if ($uploadSuccess) {
        $uploaded++
    } else {
        Write-Log "  Skipping execution due to upload failure" -Color Red
        $failed++
        continue
    }
    
    # Wait if too many concurrent executions
    while ((Get-RunningExecutions) -ge $MaxConcurrent) {
        Write-Log "  Waiting for execution slots (current: $MaxConcurrent)..." -Color Yellow
        Start-Sleep -Seconds 30
    }
    
    # Start Step Functions execution
    $executionArn = Start-BookProcessing -BookId $bookId -S3Uri $s3Uri -Artist $artist -BookName $bookName
    if ($executionArn) {
        $started++
    } else {
        $failed++
    }
    
    Write-Log ""
    
    # Small delay between submissions
    Start-Sleep -Seconds 2
}

# Summary
Write-Log "=== Processing Complete ===" -Color Cyan
Write-Log "Total PDFs found: $($pdfFiles.Count)"
Write-Log "Processed: $processed"
Write-Log "Uploaded: $uploaded"
Write-Log "Executions started: $started"
Write-Log "Skipped: $skipped"
Write-Log "Failed: $failed"
Write-Log ""
Write-Log "Log file: $logFile" -Color Green
Write-Log ""
Write-Log "To monitor executions, run:" -Color Cyan
Write-Log "  aws stepfunctions list-executions --state-machine-arn $StateMachineArn --region $Region" -Color Yellow
