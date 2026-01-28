$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:a7952841-2505-4cb8-98f1-6a0d4d6b3616"

Write-Host "Monitoring execution: a7952841-2505-4cb8-98f1-6a0d4d6b3616"
Write-Host "Started at: 2026-01-25 17:04:10"
Write-Host ""

while ($true) {
    $result = aws stepfunctions describe-execution --execution-arn $executionArn --query '{status:status,stopDate:stopDate}' --output json | ConvertFrom-Json
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] Status: $($result.status)"
    
    if ($result.status -ne "RUNNING") {
        Write-Host ""
        Write-Host "Execution completed with status: $($result.status)"
        Write-Host "Stop time: $($result.stopDate)"
        
        # Get full details
        aws stepfunctions describe-execution --execution-arn $executionArn
        break
    }
    
    Start-Sleep -Seconds 30
}
