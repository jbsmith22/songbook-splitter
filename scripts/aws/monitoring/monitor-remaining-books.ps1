# Monitor the remaining books processing

$ErrorActionPreference = "Continue"

if (-not (Test-Path "remaining-books-executions.csv")) {
    Write-Host "No executions file found. Run process-remaining-books.ps1 first." -ForegroundColor Red
    exit 1
}

$executions = Import-Csv "remaining-books-executions.csv"

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Monitoring Remaining Books Processing" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total executions: $($executions.Count)" -ForegroundColor Yellow
Write-Host ""

$running = 0
$succeeded = 0
$failed = 0
$aborted = 0
$timedOut = 0

foreach ($exec in $executions) {
    $executionArn = $exec.ExecutionArn
    
    try {
        $result = aws stepfunctions describe-execution `
            --execution-arn $executionArn `
            --profile default `
            2>&1 | ConvertFrom-Json
        
        $status = $result.status
        
        switch ($status) {
            "RUNNING" { 
                $running++
                Write-Host "$($exec.Artist) - $($exec.BookName): RUNNING" -ForegroundColor Yellow
            }
            "SUCCEEDED" { 
                $succeeded++
                Write-Host "$($exec.Artist) - $($exec.BookName): SUCCEEDED" -ForegroundColor Green
            }
            "FAILED" { 
                $failed++
                Write-Host "$($exec.Artist) - $($exec.BookName): FAILED" -ForegroundColor Red
            }
            "ABORTED" { 
                $aborted++
                Write-Host "$($exec.Artist) - $($exec.BookName): ABORTED" -ForegroundColor Red
            }
            "TIMED_OUT" { 
                $timedOut++
                Write-Host "$($exec.Artist) - $($exec.BookName): TIMED OUT" -ForegroundColor Red
            }
            default {
                Write-Host "$($exec.Artist) - $($exec.BookName): $status" -ForegroundColor Gray
            }
        }
    } catch {
        Write-Host "$($exec.Artist) - $($exec.BookName): ERROR checking status" -ForegroundColor Red
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
Write-Host "Aborted:   $aborted" -ForegroundColor Red
Write-Host "Timed Out: $timedOut" -ForegroundColor Red
Write-Host ""

if ($running -gt 0) {
    Write-Host "Still processing... Run this script again to check progress." -ForegroundColor Yellow
} elseif ($succeeded -eq $executions.Count) {
    Write-Host "All executions completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Download the processed files" -ForegroundColor Yellow
    Write-Host "  .\download-remaining-books.ps1" -ForegroundColor White
} else {
    Write-Host "Some executions failed. Check the AWS console for details." -ForegroundColor Red
}

Write-Host "================================================================================" -ForegroundColor Cyan
