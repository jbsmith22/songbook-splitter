# Real-time execution monitoring script
param(
    [Parameter(Mandatory=$false)]
    [string]$ExecutionArn
)

$ErrorActionPreference = "Stop"

# Start execution if no ARN provided
if (-not $ExecutionArn) {
    Write-Host "Starting new execution..." -ForegroundColor Cyan
    $ExecutionArn = aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" --input file://test-execution-input.json --query 'executionArn' --output text
    
    Write-Host "Execution started: $ExecutionArn" -ForegroundColor Green
    Write-Host ""
}

$startTime = Get-Date
$lastState = ""

Write-Host "Monitoring execution in real-time..." -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Gray
Write-Host ""

while ($true) {
    # Get execution status
    $execution = aws stepfunctions describe-execution --execution-arn $ExecutionArn --query '{status:status}' --output json | ConvertFrom-Json
    
    $status = $execution.status
    
    # Get current state
    $history = aws stepfunctions get-execution-history --execution-arn $ExecutionArn --max-results 10 --reverse-order --query 'events[?type==`TaskStateEntered`]' --output json | ConvertFrom-Json
    
    if ($history -and $history.Count -gt 0) {
        $latestEvent = $history[0]
        $currentState = $latestEvent.stateEnteredEventDetails.name
        
        if ($currentState -ne $lastState -and $currentState -ne "") {
            $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
            Write-Host "$elapsed sec - $currentState" -ForegroundColor Cyan
            $lastState = $currentState
        }
    }
    
    # Check if execution is complete
    if ($status -eq "SUCCEEDED") {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
        Write-Host ""
        Write-Host "EXECUTION SUCCEEDED!" -ForegroundColor Green
        Write-Host "Total time: $elapsed seconds" -ForegroundColor Cyan
        Write-Host ""
        
        # Show what was created
        $bookId = (Get-Content test-execution-input.json | ConvertFrom-Json).book_id
        Write-Host "S3 Artifacts:" -ForegroundColor Yellow
        aws s3 ls s3://jsmith-output/ --recursive | Select-String $bookId
        
        break
    } elseif ($status -eq "FAILED" -or $status -eq "TIMED_OUT" -or $status -eq "ABORTED") {
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
        Write-Host ""
        Write-Host "EXECUTION $status!" -ForegroundColor Red
        Write-Host "Total time: $elapsed seconds" -ForegroundColor Cyan
        
        break
    }
    
    # Wait before next check
    Start-Sleep -Seconds 3
}
