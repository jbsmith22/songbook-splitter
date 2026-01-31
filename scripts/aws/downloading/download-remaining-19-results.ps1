# Download the processed results for the remaining 19 books

$ErrorActionPreference = "Stop"

$Profile = "default"
$OutputBucket = "jsmith-output"
$LocalOutputPath = "ProcessedSongs"

Write-Host ("=" * 80)
Write-Host "DOWNLOADING RESULTS FOR REMAINING 19 BOOKS"
Write-Host ("=" * 80)
Write-Host ""

# Check if executions file exists
if (-not (Test-Path "remaining-19-executions.csv")) {
    Write-Host "No executions file found. Run process-remaining-19-books.ps1 first."
    exit 1
}

# Read executions
$executions = Import-Csv "remaining-19-executions.csv"

Write-Host "Checking $($executions.Count) executions..."
Write-Host ""

$successCount = 0
$failedCount = 0
$downloadedCount = 0
$runningCount = 0

foreach ($exec in $executions) {
    $bookName = $exec.BookName
    $artist = $exec.Artist
    $executionArn = $exec.ExecutionArn
    
    Write-Host "Checking: $bookName"
    
    try {
        # Check execution status
        $status = aws stepfunctions describe-execution --execution-arn $executionArn --profile $Profile --query 'status' --output text
        
        if ($status -eq "SUCCEEDED") {
            $successCount++
            Write-Host "  SUCCESS - Execution succeeded"
            
            # Construct S3 path - files are at root level under artist/book/Songs/
            $artistPath = $artist -replace " ", " "
            $bookPath = $bookName -replace " ", " "
            $s3Path = "s3://$OutputBucket/$artistPath/$bookPath/Songs/"
            
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
                aws s3 cp $s3Path $localPath --recursive --profile $Profile 2>&1 | Out-Null
                
                # Check if files were downloaded
                $fileCount = (Get-ChildItem $localPath -Filter "*.pdf" -ErrorAction SilentlyContinue).Count
                if ($fileCount -gt 0) {
                    Write-Host "  SUCCESS - Downloaded $fileCount PDF files"
                    $downloadedCount++
                } else {
                    Write-Host "  WARNING - No PDF files found at S3 location"
                }
            } catch {
                Write-Host "  ERROR downloading: $_"
            }
            
        } elseif ($status -eq "FAILED") {
            $failedCount++
            Write-Host "  FAILED - Execution failed"
        } elseif ($status -eq "RUNNING") {
            $runningCount++
            Write-Host "  RUNNING - Still running..."
        } else {
            Write-Host "  Status: $status"
        }
        
    } catch {
        Write-Host "  ERROR checking status: $_"
    }
    
    Write-Host ""
}

Write-Host ("=" * 80)
Write-Host "SUMMARY"
Write-Host ("=" * 80)
Write-Host "Total books:        $($executions.Count)"
Write-Host "Succeeded:          $successCount"
Write-Host "Failed:             $failedCount"
Write-Host "Running:            $runningCount"
Write-Host "Downloaded:         $downloadedCount"
Write-Host ""

if ($runningCount -gt 0) {
    Write-Host "RUNNING: $runningCount executions still running. Wait and run this script again."
} elseif ($downloadedCount -eq $successCount -and $successCount -gt 0) {
    Write-Host "SUCCESS: All successful executions have been downloaded!"
} elseif ($successCount -gt $downloadedCount) {
    Write-Host "WARNING: Some successful executions were not downloaded. Check S3 paths."
}

Write-Host ""
Write-Host "Results downloaded to: $LocalOutputPath"
