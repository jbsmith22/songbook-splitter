# Monitor all running executions in the pipeline

$ErrorActionPreference = "Stop"
$Profile = "default"
$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

Write-Host ("=" * 80)
Write-Host "MONITORING ALL PIPELINE EXECUTIONS"
Write-Host ("=" * 80)
Write-Host ""

$startTime = Get-Date
$lastStatus = @{}

Write-Host "Monitoring all executions in the pipeline..."
Write-Host "Press Ctrl+C to stop monitoring"
Write-Host ""

while ($true) {
    # Get all executions from the last hour
    $allExecutions = aws stepfunctions list-executions `
        --state-machine-arn $StateMachineArn `
        --profile $Profile `
        --max-results 50 `
        --query 'executions[*].{name:name,arn:executionArn,status:status,startDate:startDate}' `
        --output json | ConvertFrom-Json
    
    # Filter to only recent ones (last hour)
    $recentExecutions = $allExecutions | Where-Object { 
        $startDate = [DateTime]::Parse($_.startDate)
        $startDate -gt (Get-Date).AddHours(-1)
    }
    
    $runningCount = 0
    $succeededCount = 0
    $failedCount = 0
    
    foreach ($exec in $recentExecutions) {
        $execName = $exec.name
        $execArn = $exec.arn
        $status = $exec.status
        
        # Initialize if new
        if (-not $lastStatus.ContainsKey($execArn)) {
            $lastStatus[$execArn] = ""
        }
        
        # Only print if status changed
        if ($status -ne $lastStatus[$execArn]) {
            $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
            
            if ($status -eq "SUCCEEDED") {
                Write-Host "$elapsed sec - SUCCESS: $execName" -ForegroundColor Green
            } elseif ($status -eq "FAILED") {
                Write-Host "$elapsed sec - FAILED: $execName" -ForegroundColor Red
            } elseif ($status -eq "RUNNING") {
                Write-Host "$elapsed sec - RUNNING: $execName" -ForegroundColor Cyan
            } else {
                Write-Host "$elapsed sec - $status : $execName" -ForegroundColor Yellow
            }
            
            $lastStatus[$execArn] = $status
        }
        
        # Count statuses
        if ($status -eq "RUNNING") {
            $runningCount++
        } elseif ($status -eq "SUCCEEDED") {
            $succeededCount++
        } elseif ($status -eq "FAILED") {
            $failedCount++
        }
    }
    
    # Check if all complete
    if ($runningCount -eq 0 -and $recentExecutions.Count -gt 0) {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
        Write-Host ""
        Write-Host ("=" * 80)
        Write-Host "ALL EXECUTIONS COMPLETE!"
        Write-Host ("=" * 80)
        Write-Host "Total time: $elapsed seconds"
        Write-Host "Total executions: $($recentExecutions.Count)"
        Write-Host "Succeeded: $succeededCount"
        Write-Host "Failed: $failedCount"
        Write-Host ""
        break
    }
    
    Start-Sleep -Seconds 5
}
