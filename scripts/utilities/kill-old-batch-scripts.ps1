# Kill Old Batch Processing Scripts
# Run this to stop the competing batch scripts

Write-Host "Finding batch processing scripts..." -ForegroundColor Cyan

# Find PowerShell processes running the batch scripts
$processes = Get-Process powershell -ErrorAction SilentlyContinue | Where-Object {
    $_.StartTime -lt (Get-Date).AddMinutes(-5)  # Older than 5 minutes
}

if ($processes) {
    Write-Host "Found $($processes.Count) PowerShell processes:" -ForegroundColor Yellow
    $processes | Select-Object Id, StartTime | Format-Table -AutoSize
    
    Write-Host ""
    Write-Host "To kill these processes, run AS ADMINISTRATOR:" -ForegroundColor Red
    Write-Host ""
    foreach ($proc in $processes) {
        Write-Host "  Stop-Process -Id $($proc.Id) -Force" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Or use Task Manager to end the processes." -ForegroundColor Cyan
} else {
    Write-Host "No old PowerShell processes found." -ForegroundColor Green
}

Write-Host ""
Write-Host "After killing the old scripts, start a new one with:" -ForegroundColor Cyan
Write-Host "  .\process-all-books.ps1 -MaxConcurrent 20" -ForegroundColor Yellow
