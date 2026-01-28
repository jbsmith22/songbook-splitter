$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:57cb0781-ca4c-4e00-9388-fbd9b54ba339"

Write-Host "Monitoring Various Artists - Classic Rock (with fallback fix)..." -ForegroundColor Cyan
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
            Write-Host "Downloading results..." -ForegroundColor Cyan
            
            # Download results
            New-Item -ItemType Directory -Force -Path "various_artists_output_v2" | Out-Null
            aws s3 cp s3://jsmith-output/SheetMusicOut/Various_Artists/books/Classic_Rock_-_73_songs/ various_artists_output_v2/ --recursive
            aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/page_mapping.json various_artists_output_v2/_page_mapping.json
            aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/verified_songs.json various_artists_output_v2/_verified_songs.json
            
            $songCount = (Get-ChildItem "various_artists_output_v2/*.pdf" -ErrorAction SilentlyContinue | Measure-Object).Count
            Write-Host ""
            Write-Host "Downloaded $songCount songs to various_artists_output_v2/" -ForegroundColor Green
        }
        break
    }
    
    Start-Sleep -Seconds 30
}
