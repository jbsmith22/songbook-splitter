# Monitor all new executions (corrected + found)

$ErrorActionPreference = "Stop"

$allExecutions = @()

if (Test-Path "remaining-books-executions-corrected.csv") {
    $corrected = Import-Csv "remaining-books-executions-corrected.csv"
    $allExecutions += $corrected
}

if (Test-Path "found-books-executions.csv") {
    $found = Import-Csv "found-books-executions.csv"
    $allExecutions += $found
}

if ($allExecutions.Count -eq 0) {
    Write-Host "No executions found" -ForegroundColor Red
    exit 1
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Monitoring All New Executions" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total executions: $($allExecutions.Count)" -ForegroundColor Yellow
Write-Host ""

$running = 0
$succeeded = 0
$failed = 0
$timedOut = 0
$aborted = 0

$failedExecutions = @()
$succeededExecutions = @()

foreach ($exec in $allExecutions) {
    $status = aws stepfunctions describe-execution `
        --execution-arn $exec.ExecutionArn `
        --profile default `
        --query 'status' `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "$($exec.Artist) - $($exec.BookName): ERROR querying status" -ForegroundColor Red
        continue
    }
    
    switch ($status) {
        "RUNNING" {
            Write-Host "$($exec.Artist) - $($exec.BookName): RUNNING" -ForegroundColor Yellow
            $running++
        }
        "SUCCEEDED" {
            Write-Host "$($exec.Artist) - $($exec.BookName): SUCCEEDED" -ForegroundColor Green
            $succeeded++
            $succeededExecutions += $exec
        }
        "FAILED" {
            Write-Host "$($exec.Artist) - $($exec.BookName): FAILED" -ForegroundColor Red
            $failed++
            $failedExecutions += $exec
        }
        "TIMED_OUT" {
            Write-Host "$($exec.Artist) - $($exec.BookName): TIMED OUT" -ForegroundColor Magenta
            $timedOut++
        }
        "ABORTED" {
            Write-Host "$($exec.Artist) - $($exec.BookName): ABORTED" -ForegroundColor Magenta
            $aborted++
        }
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Running:   $running" -ForegroundColor Yellow
Write-Host "Succeeded: $succeeded" -ForegroundColor Green
Write-Host "Failed:    $failed" -ForegroundColor Red
Write-Host "Timed Out: $timedOut" -ForegroundColor Magenta
Write-Host "Aborted:   $aborted" -ForegroundColor Magenta
Write-Host ""

if ($succeededExecutions.Count -gt 0) {
    Write-Host "Succeeded Executions:" -ForegroundColor Green
    Write-Host ""
    foreach ($exec in $succeededExecutions) {
        Write-Host "  $($exec.Artist) - $($exec.BookName)" -ForegroundColor Green
    }
    Write-Host ""
}

if ($failedExecutions.Count -gt 0) {
    Write-Host "Failed Executions:" -ForegroundColor Red
    Write-Host ""
    foreach ($exec in $failedExecutions) {
        Write-Host "  $($exec.Artist) - $($exec.BookName)" -ForegroundColor Red
        Write-Host "    Execution: $($exec.ExecutionName)" -ForegroundColor Gray
    }
    Write-Host ""
}

Write-Host "================================================================================" -ForegroundColor Cyan
