# Monitor all 19 remaining book executions in real-time

$ErrorActionPreference = "Stop"

$Profile = "default"

Write-Host ("=" * 80)
Write-Host "MONITORING REMAINING 19 BOOKS"
Write-Host ("=" * 80)
Write-Host ""

# Check if executions file exists
if (-not (Test-Path "remaining-19-executions.csv")) {
    Write-Host "No executions file found. Run process-remaining-19-books.ps1 first."
    exit 1
}

# Read executions
$executions = Import-Csv "remaining-19-executions.csv"

Write-Host "Monitoring $($executions.Count) executions..."
Write-Host "Press Ctrl+C to stop monitoring"
Write-Host ""

$startTime = Get-Date
$lastStatus = @{}

# Initialize last status
foreach ($exec in $executions) {
    $lastStatus[$exec.ExecutionArn] = ""
}

while ($true) {
    $allComplete = $true
    $successCount = 0
    $failedCount = 0
    $runningCount = 0
    
    foreach ($exec in $executions) {
        $bookName = $exec.BookName
        $executionArn = $exec.ExecutionArn
        
        try {
            # Get execution status
            $status = aws stepfunctions describe-execution --execution-arn $executionArn --profile $Profile --query 'status' --output text
            
            # Only print if status changed
            if ($status -ne $lastStatus[$executionArn]) {
                $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
                
                if ($status -eq "SUCCEEDED") {
                    Write-Host "$elapsed sec - SUCCESS: $bookName" -ForegroundColor Green
                } elseif ($status -eq "FAILED") {
                    Write-Host "$elapsed sec - FAILED: $bookName" -ForegroundColor Red
                } elseif ($status -eq "RUNNING") {
                    Write-Host "$elapsed sec - RUNNING: $bookName" -ForegroundColor Cyan
                } else {
                    Write-Host "$elapsed sec - $status : $bookName" -ForegroundColor Yellow
                }
                
                $lastStatus[$executionArn] = $status
            }
            
            # Count statuses
            if ($status -eq "SUCCEEDED") {
                $successCount++
            } elseif ($status -eq "FAILED") {
                $failedCount++
            } elseif ($status -eq "RUNNING") {
                $runningCount++
                $allComplete = $false
            } else {
                $allComplete = $false
            }
            
        } catch {
            Write-Host "ERROR checking $bookName : $_" -ForegroundColor Red
        }
    }
    
    # Check if all complete
    if ($allComplete) {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
        Write-Host ""
        Write-Host ("=" * 80)
        Write-Host "ALL EXECUTIONS COMPLETE!"
        Write-Host ("=" * 80)
        Write-Host "Total time: $elapsed seconds"
        Write-Host "Succeeded: $successCount"
        Write-Host "Failed: $failedCount"
        Write-Host ""
        
        if ($successCount -gt 0) {
            Write-Host "To download results, run:" -ForegroundColor Cyan
            Write-Host "  .\download-remaining-19-results.ps1" -ForegroundColor White
        }
        
        break
    }
    
    # Wait before next check
    Start-Sleep -Seconds 5
}
