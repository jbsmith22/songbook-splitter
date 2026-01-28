$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:6f8e52fd-9c86-4507-8b18-69a0022feae5"

Write-Host "Monitoring Billy Joel Complete Vol 2 execution"
Write-Host "Started at: 2026-01-25 18:47:34"
Write-Host ""

while ($true) {
    $result = aws stepfunctions describe-execution --execution-arn $executionArn --query '{status:status,stopDate:stopDate}' --output json | ConvertFrom-Json
    
    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] Status: $($result.status)"
    
    if ($result.status -ne "RUNNING") {
        Write-Host ""
        Write-Host "Execution completed with status: $($result.status)"
        Write-Host "Stop time: $($result.stopDate)"
        break
    }
    
    Start-Sleep -Seconds 30
}
