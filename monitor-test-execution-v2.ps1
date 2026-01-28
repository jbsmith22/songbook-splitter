# Monitor Step Functions execution for Various Artists test
$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:ef03a7a5-1421-49ba-9960-5866111cc714"

Write-Host "Monitoring execution: $executionArn" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    $status = aws stepfunctions describe-execution --execution-arn $executionArn --region us-east-1 | ConvertFrom-Json
    
    $currentStatus = $status.status
    $startDate = $status.startDate
    
    Clear-Host
    Write-Host "=== Step Functions Execution Monitor ===" -ForegroundColor Cyan
    Write-Host "Execution ARN: $executionArn" -ForegroundColor Gray
    Write-Host "Start Time: $startDate" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Status: $currentStatus" -ForegroundColor $(if ($currentStatus -eq "RUNNING") { "Yellow" } elseif ($currentStatus -eq "SUCCEEDED") { "Green" } else { "Red" })
    Write-Host ""
    
    if ($currentStatus -ne "RUNNING") {
        Write-Host "Execution completed with status: $currentStatus" -ForegroundColor $(if ($currentStatus -eq "SUCCEEDED") { "Green" } else { "Red" })
        
        if ($status.output) {
            Write-Host ""
            Write-Host "Output:" -ForegroundColor Cyan
            Write-Host $status.output
        }
        
        if ($status.error) {
            Write-Host ""
            Write-Host "Error:" -ForegroundColor Red
            Write-Host $status.error
        }
        
        break
    }
    
    Write-Host "Refreshing in 10 seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "Monitoring complete." -ForegroundColor Green
