$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:6f554f3e-1bcf-4321-92d2-f30e73cf2f01"

Write-Host "Monitoring Various Artists - Classic Rock execution..." -ForegroundColor Cyan
Write-Host "Execution ARN: $executionArn" -ForegroundColor Gray
Write-Host ""

$startTime = Get-Date

while ($true) {
    $status = aws stepfunctions describe-execution --execution-arn $executionArn --query '{status:status,stopDate:stopDate}' --output json | ConvertFrom-Json
    
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] [$elapsed min] Status: $($status.status)" -ForegroundColor $(if ($status.status -eq "RUNNING") { "Yellow" } elseif ($status.status -eq "SUCCEEDED") { "Green" } else { "Red" })
    
    if ($status.status -ne "RUNNING") {
        Write-Host ""
        Write-Host "Execution completed with status: $($status.status)" -ForegroundColor $(if ($status.status -eq "SUCCEEDED") { "Green" } else { "Red" })
        
        if ($status.status -eq "SUCCEEDED") {
            Write-Host ""
            Write-Host "Download results with:" -ForegroundColor Cyan
            Write-Host "aws s3 cp s3://jsmith-output/SheetMusicOut/Various_Artists/books/Classic_Rock_-_73_songs/ various_artists_output/ --recursive" -ForegroundColor White
        }
        break
    }
    
    Start-Sleep -Seconds 30
}
