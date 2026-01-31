# Monitor the 13 reprocessed books

$csvPath = Get-ChildItem "reprocess-13-executions-*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $csvPath) {
    Write-Host "No execution CSV found!" -ForegroundColor Red
    exit 1
}

Write-Host "Monitoring executions from: $($csvPath.Name)"
Write-Host ""

$executions = Import-Csv $csvPath.FullName

$running = $true
while ($running) {
    Clear-Host
    Write-Host "================================================================================"
    Write-Host "MONITORING 13 REPROCESSED BOOKS - $(Get-Date -Format 'HH:mm:ss')"
    Write-Host "================================================================================"
    Write-Host ""
    
    $statusCounts = @{}
    $allComplete = $true
    
    foreach ($exec in $executions) {
        $status = aws stepfunctions describe-execution --execution-arn $exec.ExecutionArn --query 'status' --output text 2>$null
        
        if (-not $statusCounts.ContainsKey($status)) {
            $statusCounts[$status] = 0
        }
        $statusCounts[$status]++
        
        $color = switch ($status) {
            "SUCCEEDED" { "Green" }
            "FAILED" { "Red" }
            "RUNNING" { "Yellow"; $allComplete = $false }
            default { "Gray"; $allComplete = $false }
        }
        
        $shortName = $exec.BookName
        if ($shortName.Length > 50) {
            $shortName = $shortName.Substring(0, 47) + "..."
        }
        
        Write-Host ("{0,-52} {1}" -f $shortName, $status) -ForegroundColor $color
    }
    
    Write-Host ""
    Write-Host "================================================================================"
    Write-Host "SUMMARY:"
    foreach ($s in $statusCounts.Keys | Sort-Object) {
        Write-Host "  ${s}: $($statusCounts[$s])"
    }
    Write-Host "================================================================================"
    
    if ($allComplete) {
        Write-Host ""
        Write-Host "All executions complete!" -ForegroundColor Green
        $running = $false
    }
    else {
        Write-Host ""
        Write-Host "Press Ctrl+C to stop monitoring..."
        Start-Sleep -Seconds 10
    }
}
