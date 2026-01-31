# Monitor the 12 failed book executions

$ErrorActionPreference = "Stop"
$Profile = "default"

Write-Host ("=" * 80)
Write-Host "MONITORING 12 FAILED BOOKS"
Write-Host ("=" * 80)
Write-Host ""

if (-not (Test-Path "failed-12-executions.csv")) {
    Write-Host "No executions file found. Run process-12-failed-books.ps1 first."
    exit 1
}

$executions = Import-Csv "failed-12-executions.csv"

Write-Host "Monitoring $($executions.Count) executions..."
Write-Host "Press Ctrl+C to stop monitoring"
Write-Host ""

$startTime = Get-Date
$lastStatus = @{}

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
            $status = aws stepfunctions describe-execution --execution-arn $executionArn --profile $Profile --query 'status' --output text
            
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
            Write-Host "  .\download-failed-12-results.ps1" -ForegroundColor White
        }
        
        break
    }
    
    Start-Sleep -Seconds 5
}
