# Check execution details for Billy Joel books

$executionsFile = "billy-joel-executions.json"
$executions = Get-Content $executionsFile | ConvertFrom-Json

Write-Host "Checking execution details..." -ForegroundColor Cyan
Write-Host ""

foreach ($exec in $executions) {
    $bookName = $exec.book -replace '\.pdf$', ''
    $arn = $exec.execution_arn
    
    Write-Host "Book: $bookName" -ForegroundColor Yellow
    
    try {
        $result = aws stepfunctions describe-execution `
            --execution-arn $arn `
            --profile default `
            --output json | ConvertFrom-Json
        
        Write-Host "  Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "SUCCEEDED") { "Green" } else { "Red" })
        
        # Get output
        if ($result.output) {
            $output = $result.output | ConvertFrom-Json
            if ($output.song_count) {
                Write-Host "  Songs extracted: $($output.song_count)" -ForegroundColor Cyan
            }
            if ($output.message) {
                Write-Host "  Message: $($output.message)" -ForegroundColor Gray
            }
        }
        
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}
