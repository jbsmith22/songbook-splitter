# Monitor the progress of the remaining 20 book executions

$ErrorActionPreference = "Stop"

$Profile = "default"

Write-Host "=" * 80
Write-Host "MONITORING REMAINING 20 BOOKS"
Write-Host "=" * 80
Write-Host ""

# Check if executions file exists
if (-not (Test-Path "remaining-20-executions.csv")) {
    Write-Host "✗ No executions file found. Run process-remaining-20-books.ps1 first."
    exit 1
}

# Read executions
$executions = Import-Csv "remaining-20-executions.csv"

Write-Host "Monitoring $($executions.Count) executions..."
Write-Host ""

# Track status
$statusCounts = @{
    RUNNING = 0
    SUCCEEDED = 0
    FAILED = 0
    TIMED_OUT = 0
    ABORTED = 0
}

$results = @()

foreach ($exec in $executions) {
    $bookName = $exec.BookName
    $executionArn = $exec.ExecutionArn
    
    try {
        $status = aws stepfunctions describe-execution `
            --execution-arn $executionArn `
            --profile $Profile `
            --query 'status' `
            --output text
        
        $statusCounts[$status]++
        
        $statusIcon = switch ($status) {
            "SUCCEEDED" { "✓" }
            "FAILED" { "✗" }
            "RUNNING" { "⟳" }
            "TIMED_OUT" { "⏱" }
            "ABORTED" { "⊗" }
            default { "?" }
        }
        
        Write-Host "$statusIcon $status : $bookName"
        
        $results += @{
            BookName = $bookName
            Artist = $exec.Artist
            Status = $status
            ExecutionArn = $executionArn
        }
        
    } catch {
        Write-Host "✗ ERROR : $bookName (Could not get status)"
        $results += @{
            BookName = $bookName
            Artist = $exec.Artist
            Status = "ERROR"
            ExecutionArn = $executionArn
        }
    }
}

Write-Host ""
Write-Host "=" * 80
Write-Host "SUMMARY"
Write-Host "=" * 80
Write-Host "Total:      $($executions.Count)"
Write-Host "Running:    $($statusCounts.RUNNING)"
Write-Host "Succeeded:  $($statusCounts.SUCCEEDED)"
Write-Host "Failed:     $($statusCounts.FAILED)"
Write-Host "Timed Out:  $($statusCounts.TIMED_OUT)"
Write-Host "Aborted:    $($statusCounts.ABORTED)"
Write-Host ""

# Calculate progress
$completed = $statusCounts.SUCCEEDED + $statusCounts.FAILED + $statusCounts.TIMED_OUT + $statusCounts.ABORTED
$percentComplete = [math]::Round(($completed / $executions.Count) * 100, 1)

Write-Host "Progress: $completed/$($executions.Count) ($percentComplete%)"
Write-Host ""

# Save results
$results | Export-Csv "remaining-20-status.csv" -NoTypeInformation
Write-Host "✓ Status saved to: remaining-20-status.csv"
Write-Host ""

# Show failed executions if any
if ($statusCounts.FAILED -gt 0) {
    Write-Host "=" * 80
    Write-Host "FAILED EXECUTIONS"
    Write-Host "=" * 80
    $results | Where-Object { $_.Status -eq "FAILED" } | ForEach-Object {
        Write-Host "✗ $($_.BookName)"
        Write-Host "  ARN: $($_.ExecutionArn)"
    }
    Write-Host ""
}

# Auto-refresh option
if ($statusCounts.RUNNING -gt 0) {
    Write-Host "Some executions are still running."
    Write-Host "Run this script again to refresh status, or use:"
    Write-Host "  while (`$true) { cls; .\monitor-remaining-20.ps1; Start-Sleep -Seconds 30 }"
}
