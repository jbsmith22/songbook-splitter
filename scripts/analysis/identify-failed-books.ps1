# Identify books that show SUCCEEDED but have no output in S3

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

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Identify Failed Books (Succeeded but No Output)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$s3Bucket = "jsmith-output"
$failedBooks = @()

foreach ($exec in $allExecutions) {
    # Check execution status
    $status = aws stepfunctions describe-execution `
        --execution-arn $exec.ExecutionArn `
        --profile default `
        --query 'status' `
        --output text 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        continue
    }
    
    if ($status -ne "SUCCEEDED") {
        continue
    }
    
    # Check if S3 output exists
    $s3Path = "$($exec.Artist)/$($exec.BookName)/Songs/"
    $checkResult = aws s3 ls "s3://$s3Bucket/$s3Path" --profile default 2>&1
    
    if ($LASTEXITCODE -ne 0 -or -not $checkResult) {
        Write-Host "FAILED: $($exec.Artist) - $($exec.BookName)" -ForegroundColor Red
        $failedBooks += [PSCustomObject]@{
            Artist = $exec.Artist
            BookName = $exec.BookName
            ExecutionArn = $exec.ExecutionArn
            ExecutionName = $exec.ExecutionName
            S3Key = $exec.S3Key
        }
    }
}

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Total failed (succeeded but no output): $($failedBooks.Count)" -ForegroundColor Red
Write-Host ""

if ($failedBooks.Count -gt 0) {
    Write-Host "Failed Books:" -ForegroundColor Red
    Write-Host ""
    foreach ($book in $failedBooks) {
        Write-Host "  - $($book.Artist) - $($book.BookName)" -ForegroundColor Red
    }
    Write-Host ""
    
    $failedBooks | Export-Csv "failed-books-no-output.csv" -NoTypeInformation -Encoding UTF8
    Write-Host "Details saved to: failed-books-no-output.csv" -ForegroundColor Cyan
}

Write-Host "================================================================================" -ForegroundColor Cyan
