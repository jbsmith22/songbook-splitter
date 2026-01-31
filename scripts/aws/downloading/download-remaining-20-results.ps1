# Download the processed results for the remaining 20 books

$ErrorActionPreference = "Stop"

$Profile = "default"
$OutputBucket = "jsmith-output"
$LocalOutputPath = "ProcessedSongs"

Write-Host "=" * 80
Write-Host "DOWNLOADING RESULTS FOR REMAINING 20 BOOKS"
Write-Host "=" * 80
Write-Host ""

# Check if executions file exists
if (-not (Test-Path "remaining-20-executions.csv")) {
    Write-Host "✗ No executions file found. Run process-remaining-20-books.ps1 first."
    exit 1
}

# Read executions
$executions = Import-Csv "remaining-20-executions.csv"

Write-Host "Checking $($executions.Count) executions..."
Write-Host ""

$successCount = 0
$failedCount = 0
$downloadedCount = 0

foreach ($exec in $executions) {
    $bookName = $exec.BookName
    $artist = $exec.Artist
    $executionArn = $exec.ExecutionArn
    
    Write-Host "Checking: $bookName"
    
    try {
        # Check execution status
        $status = aws stepfunctions describe-execution `
            --execution-arn $executionArn `
            --profile $Profile `
            --query 'status' `
            --output text
        
        if ($status -eq "SUCCEEDED") {
            $successCount++
            Write-Host "  ✓ Execution succeeded"
            
            # Construct S3 path
            # Output is at: s3://jsmith-output/s3://jsmith-output/SheetMusicOut/{Artist}/books/{BookName}/
            # (Note the duplicate bucket name in the path - this is a known issue)
            $s3Path = "s3://$OutputBucket/s3://$OutputBucket/SheetMusicOut/$artist/books/$bookName/"
            
            # Construct local path
            $localPath = Join-Path $LocalOutputPath "$artist\$bookName"
            
            Write-Host "  Downloading from: $s3Path"
            Write-Host "  To: $localPath"
            
            # Create directory if it doesn't exist
            if (-not (Test-Path $localPath)) {
                New-Item -ItemType Directory -Path $localPath -Force | Out-Null
            }
            
            # Download files
            try {
                aws s3 cp $s3Path $localPath --recursive --profile $Profile
                
                # Check if files were downloaded
                $fileCount = (Get-ChildItem $localPath -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
                if ($fileCount -gt 0) {
                    Write-Host "  ✓ Downloaded $fileCount PDF files"
                    $downloadedCount++
                } else {
                    Write-Host "  ⚠ No PDF files found at S3 location"
                }
            } catch {
                Write-Host "  ✗ ERROR downloading: $_"
            }
            
        } elseif ($status -eq "FAILED") {
            $failedCount++
            Write-Host "  ✗ Execution failed"
        } elseif ($status -eq "RUNNING") {
            Write-Host "  ⟳ Still running..."
        } else {
            Write-Host "  ? Status: $status"
        }
        
    } catch {
        Write-Host "  ✗ ERROR checking status: $_"
    }
    
    Write-Host ""
}

Write-Host "=" * 80
Write-Host "SUMMARY"
Write-Host "=" * 80
Write-Host "Total books:        $($executions.Count)"
Write-Host "Succeeded:          $successCount"
Write-Host "Failed:             $failedCount"
Write-Host "Downloaded:         $downloadedCount"
Write-Host ""

if ($downloadedCount -eq $successCount -and $successCount -gt 0) {
    Write-Host "✓ All successful executions have been downloaded!"
} elseif ($successCount -gt $downloadedCount) {
    Write-Host "⚠ Some successful executions were not downloaded. Check S3 paths."
}

Write-Host ""
Write-Host "Results downloaded to: $LocalOutputPath"
