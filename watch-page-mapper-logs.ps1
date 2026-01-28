$logGroup = "/aws/ecs/jsmith-sheetmusic-splitter"
$logStreamPrefix = "page-mapper"

Write-Host "Watching CloudWatch logs for page-mapper..." -ForegroundColor Cyan
Write-Host "Log Group: $logGroup" -ForegroundColor Yellow
Write-Host ""

# Get the most recent log stream
$streams = aws logs describe-log-streams --log-group-name $logGroup --log-stream-name-prefix $logStreamPrefix --order-by LastEventTime --descending --max-items 1 | ConvertFrom-Json

if ($streams.logStreams.Count -eq 0) {
    Write-Host "No log streams found yet. Waiting..." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
    $streams = aws logs describe-log-streams --log-group-name $logGroup --log-stream-name-prefix $logStreamPrefix --order-by LastEventTime --descending --max-items 1 | ConvertFrom-Json
}

if ($streams.logStreams.Count -gt 0) {
    $logStreamName = $streams.logStreams[0].logStreamName
    Write-Host "Watching log stream: $logStreamName" -ForegroundColor Green
    Write-Host ""
    
    # Tail the logs
    aws logs tail $logGroup --log-stream-names $logStreamName --follow --format short
} else {
    Write-Host "No log streams found" -ForegroundColor Red
}
