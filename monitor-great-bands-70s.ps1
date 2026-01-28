# Monitor Step Functions execution for Great Bands of the 70s test
$executionArn = "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:6b67f6c4-ceeb-42c6-a351-8f7b1a81dbf7"

Write-Host "Monitoring execution: Great Bands Of The 70s" -ForegroundColor Cyan
Write-Host "Execution ARN: $executionArn" -ForegroundColor Gray
Write-Host ""

while ($true) {
    $status = aws stepfunctions describe-execution --execution-arn $executionArn --region us-east-1 | ConvertFrom-Json
    
    $currentStatus = $status.status
    $startDate = $status.startDate
    
    Clear-Host
    Write-Host "=== Great Bands Of The 70s - Execution Monitor ===" -ForegroundColor Cyan
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
            $output = $status.output | ConvertFrom-Json
            Write-Host "Book ID: $($output.book_id)" -ForegroundColor White
            Write-Host "Songs Extracted: $($output.songs_extracted)" -ForegroundColor White
            Write-Host "Manifest URI: $($output.manifest_uri)" -ForegroundColor White
        }
        
        if ($status.error) {
            Write-Host ""
            Write-Host "Error:" -ForegroundColor Red
            Write-Host $status.error
        }
        
        # Show CloudWatch logs link
        Write-Host ""
        Write-Host "CloudWatch Logs:" -ForegroundColor Cyan
        Write-Host "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/`$252Faws`$252Fecs`$252Fjsmith-sheetmusic-splitter" -ForegroundColor Blue
        
        break
    }
    
    Write-Host "Refreshing in 10 seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

Write-Host ""
Write-Host "Monitoring complete." -ForegroundColor Green
Write-Host ""
Write-Host "To download results, run:" -ForegroundColor Cyan
Write-Host "aws s3 sync s3://jsmith-output/Various`%20Artists/Great`%20Bands`%20Of`%20The`%2070s/Songs/ ./great_bands_70s_output/songs/ --region us-east-1" -ForegroundColor Yellow
