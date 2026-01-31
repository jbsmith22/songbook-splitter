# Monitor Billy Joel retry executions

$executionsFile = "billy-joel-executions.json"

if (-not (Test-Path $executionsFile)) {
    Write-Host "ERROR: $executionsFile not found" -ForegroundColor Red
    exit 1
}

$executions = Get-Content $executionsFile | ConvertFrom-Json

Write-Host "================================================================================"
Write-Host "Monitoring Billy Joel executions"
Write-Host "================================================================================"
Write-Host ""

$allComplete = $false
$iteration = 0

while (-not $allComplete) {
    $iteration++
    Write-Host "Check #$iteration - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    
    $statuses = @()
    
    foreach ($exec in $executions) {
        $result = aws stepfunctions describe-execution --execution-arn $exec.execution_arn --profile default 2>&1 | ConvertFrom-Json
        
        $status = $result.status
        $statuses += $status
        
        $color = switch ($status) {
            "RUNNING" { "Yellow" }
            "SUCCEEDED" { "Green" }
            "FAILED" { "Red" }
            "TIMED_OUT" { "Red" }
            "ABORTED" { "Red" }
            default { "White" }
        }
        
        Write-Host "  $($exec.book): " -NoNewline
        Write-Host $status -ForegroundColor $color
    }
    
    Write-Host ""
    
    # Check if all complete
    $runningCount = ($statuses | Where-Object { $_ -eq "RUNNING" }).Count
    $allComplete = ($runningCount -eq 0)
    
    if (-not $allComplete) {
        Write-Host "Waiting 30 seconds..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
        Write-Host ""
    }
}

Write-Host "================================================================================"
Write-Host "ALL EXECUTIONS COMPLETE"
Write-Host "================================================================================"
Write-Host ""

# Final summary
$succeeded = 0
$failed = 0

foreach ($exec in $executions) {
    $result = aws stepfunctions describe-execution --execution-arn $exec.execution_arn --profile default 2>&1 | ConvertFrom-Json
    
    if ($result.status -eq "SUCCEEDED") {
        $succeeded++
        Write-Host "SUCCESS: $($exec.book)" -ForegroundColor Green
    } else {
        $failed++
        Write-Host "FAILED: $($exec.book) - $($result.status)" -ForegroundColor Red
    }
}

Write-Host ""
if ($failed -eq 0) {
    Write-Host "Summary: $succeeded succeeded, $failed failed" -ForegroundColor Green
} else {
    Write-Host "Summary: $succeeded succeeded, $failed failed" -ForegroundColor Yellow
}
