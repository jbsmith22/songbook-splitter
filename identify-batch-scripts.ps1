# Identify Batch Script Processes
Write-Host "=== Batch Script Process Identification ===" -ForegroundColor Cyan
Write-Host ""

$processes = @(
    @{Id=150168; Started="12:21 PM"; Type="OLD (MaxConcurrent=3)"; Action="KILL THIS ONE"}
    @{Id=83308; Started="1:55 PM"; Type="NEW (MaxConcurrent=20)"; Action="KEEP THIS ONE"}
)

foreach ($proc in $processes) {
    $exists = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
    if ($exists) {
        Write-Host "Process $($proc.Id) - $($proc.Type)" -ForegroundColor Yellow
        Write-Host "  Started: $($proc.Started)" -ForegroundColor Gray
        Write-Host "  Action: $($proc.Action)" -ForegroundColor $(if ($proc.Action -like "*KILL*") { "Red" } else { "Green" })
        Write-Host ""
    } else {
        Write-Host "Process $($proc.Id) - ALREADY KILLED ✓" -ForegroundColor Green
        Write-Host ""
    }
}

Write-Host "To kill process 150168 in Task Manager:" -ForegroundColor Cyan
Write-Host "1. Open Task Manager (Ctrl+Shift+Esc)" -ForegroundColor White
Write-Host "2. Go to Details tab" -ForegroundColor White
Write-Host "3. Find powershell.exe with PID 150168" -ForegroundColor White
Write-Host "4. Right-click and select End Task" -ForegroundColor White
