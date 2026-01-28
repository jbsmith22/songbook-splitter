$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:dc4b8779-a93c-438b-9e7b-dc5a92e19580"

Write-Host "Monitoring execution: $executionArn" -ForegroundColor Cyan
Write-Host ""

while ($true) {
    $status = aws stepfunctions describe-execution --execution-arn $executionArn --query 'status' --output text
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] Status: $status" -ForegroundColor Yellow
    
    if ($status -eq "SUCCEEDED" -or $status -eq "FAILED" -or $status -eq "TIMED_OUT" -or $status -eq "ABORTED") {
        Write-Host ""
        Write-Host "Execution completed with status: $status" -ForegroundColor $(if ($status -eq "SUCCEEDED") { "Green" } else { "Red" })
        
        # Get output
        Write-Host ""
        Write-Host "Getting execution output..." -ForegroundColor Cyan
        aws stepfunctions describe-execution --execution-arn $executionArn --query 'output' --output text | ConvertFrom-Json | ConvertTo-Json -Depth 10
        
        break
    }
    
    Start-Sleep -Seconds 30
}
