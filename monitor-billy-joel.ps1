# Monitor Billy Joel executions and report results

$executionsFile = "billy-joel-executions.json"
$executions = Get-Content $executionsFile | ConvertFrom-Json

Write-Host "Monitoring 6 Billy Joel book executions..." -ForegroundColor Cyan
Write-Host ""

$allComplete = $false
$checkCount = 0

while (-not $allComplete) {
    $checkCount++
    Write-Host "Check #$checkCount - $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Yellow
    
    $statuses = @()
    $allComplete = $true
    
    foreach ($exec in $executions) {
        $bookName = $exec.book -replace '\.pdf$', ''
        $arn = $exec.execution_arn
        
        try {
            $result = aws stepfunctions describe-execution `
                --execution-arn $arn `
                --profile default `
                --output json 2>&1 | ConvertFrom-Json
            
            $status = $result.status
            
            $statuses += @{
                book = $bookName
                status = $status
                arn = $arn
            }
            
            $color = switch ($status) {
                "RUNNING" { "Cyan"; $allComplete = $false }
                "SUCCEEDED" { "Green" }
                "FAILED" { "Red" }
                "TIMED_OUT" { "Red" }
                "ABORTED" { "Red" }
                default { "White"; $allComplete = $false }
            }
            
            Write-Host "  $bookName : $status" -ForegroundColor $color
            
        } catch {
            Write-Host "  $bookName : ERROR checking status" -ForegroundColor Red
            $allComplete = $false
        }
    }
    
    Write-Host ""
    
    if (-not $allComplete) {
        Write-Host "Waiting 30 seconds before next check..." -ForegroundColor Gray
        Start-Sleep -Seconds 30
    }
}

Write-Host "=" * 80 -ForegroundColor Green
Write-Host "All executions complete!" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host ""

# Summary
$succeeded = ($statuses | Where-Object { $_.status -eq "SUCCEEDED" }).Count
$failed = ($statuses | Where-Object { $_.status -ne "SUCCEEDED" }).Count

Write-Host "Summary:"
Write-Host "  Succeeded: $succeeded" -ForegroundColor Green
Write-Host "  Failed: $failed" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host ""

# Save final status
$statuses | ConvertTo-Json | Out-File "billy-joel-execution-results.json" -Encoding ASCII

Write-Host "Results saved to: billy-joel-execution-results.json"
