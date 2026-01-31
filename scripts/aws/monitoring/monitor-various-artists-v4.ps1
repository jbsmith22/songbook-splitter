$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:a6237776-58d9-4b49-8c2c-db5bb233bdc3"

Write-Host "Monitoring Various Artists - Classic Rock (with FIXED state machine)..." -ForegroundColor Cyan
Write-Host "Execution ARN: $executionArn" -ForegroundColor Gray
Write-Host "This should take 15-20 minutes to scan all pages with vision..." -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date

while ($true) {
    $status = aws stepfunctions describe-execution --execution-arn $executionArn --query '{status:status}' --output json | ConvertFrom-Json
    
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
    $timestamp = Get-Date -Format "HH:mm:ss"
    
    Write-Host "[$timestamp] [$elapsed min] Status: $($status.status)" -ForegroundColor $(if ($status.status -eq "RUNNING") { "Yellow" } elseif ($status.status -eq "SUCCEEDED") { "Green" } else { "Red" })
    
    if ($status.status -ne "RUNNING") {
        Write-Host ""
        Write-Host "Execution completed with status: $($status.status)" -ForegroundColor $(if ($status.status -eq "SUCCEEDED") { "Green" } else { "Red" })
        
        if ($status.status -eq "SUCCEEDED") {
            Write-Host ""
            Write-Host "Downloading results..." -ForegroundColor Cyan
            
            # Download results
            New-Item -ItemType Directory -Force -Path "various_artists_output_v4" | Out-Null
            aws s3 cp s3://jsmith-output/SheetMusicOut/Various_Artists/books/Classic_Rock_-_73_songs/ various_artists_output_v4/ --recursive
            aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/page_mapping.json various_artists_output_v4/_page_mapping.json
            aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/verified_songs.json various_artists_output_v4/_verified_songs.json
            
            $songCount = (Get-ChildItem "various_artists_output_v4/*.pdf" -ErrorAction SilentlyContinue | Measure-Object).Count
            Write-Host ""
            Write-Host "Downloaded $songCount songs to various_artists_output_v4/" -ForegroundColor Green
            
            # Show page mapping summary
            $pageMapping = Get-Content "various_artists_output_v4/_page_mapping.json" | ConvertFrom-Json
            Write-Host ""
            Write-Host "Page Mapping Summary:" -ForegroundColor Cyan
            Write-Host "  Songs Found: $($pageMapping.song_locations.Count)" -ForegroundColor White
            Write-Host "  Confidence: $($pageMapping.confidence)" -ForegroundColor White
        }
        break
    }
    
    Start-Sleep -Seconds 30
}
