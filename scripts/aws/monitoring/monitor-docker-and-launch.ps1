# Monitor Docker build and launch Various Artists test when ready

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

Write-Host "Monitoring Docker build process..." -ForegroundColor Cyan
Write-Host ""

while ($true) {
    Start-Sleep -Seconds 30
    
    # Check if Docker process is still running
    $dockerProcess = Get-Process -Name "docker" -ErrorAction SilentlyContinue
    
    if (-not $dockerProcess) {
        Write-Host "Docker build appears complete!" -ForegroundColor Green
        Write-Host ""
        
        # Wait a bit for push to complete
        Write-Host "Waiting 30 seconds for ECR push to complete..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
        
        # Launch Various Artists test
        Write-Host "Launching Various Artists - Classic Rock test..." -ForegroundColor Cyan
        
        $execution = aws stepfunctions start-execution `
            --state-machine-arn $stateMachineArn `
            --input "file://test-various-artists-input.json" | ConvertFrom-Json
        
        $executionArn = $execution.executionArn
        Write-Host "Execution started: $executionArn" -ForegroundColor Green
        Write-Host ""
        
        # Monitor execution
        Write-Host "Monitoring execution..." -ForegroundColor Cyan
        $startTime = Get-Date
        
        while ($true) {
            Start-Sleep -Seconds 30
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
                    aws s3 cp s3://jsmith-output/SheetMusicOut/Various_Artists/books/Classic_Rock_-_73_songs/ various_artists_output_v2/ --recursive
                    aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/page_mapping.json various_artists_output_v2/_page_mapping.json
                    aws s3 cp s3://jsmith-output/artifacts/various-artists-classic-rock-73/verified_songs.json various_artists_output_v2/_verified_songs.json
                    
                    $songCount = (Get-ChildItem "various_artists_output_v2/*.pdf" -ErrorAction SilentlyContinue | Measure-Object).Count
                    Write-Host ""
                    Write-Host "Downloaded $songCount songs to various_artists_output_v2/" -ForegroundColor Green
                }
                break
            }
        }
        break
    }
    
    Write-Host "." -NoNewline
}
