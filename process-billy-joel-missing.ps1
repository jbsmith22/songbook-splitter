# Process missing Billy Joel books through the pipeline

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

$missingBooks = @(
    "Billy Joel - Anthology.pdf",
    "Billy Joel - Fantasies & Delusions.pdf",
    "Billy Joel - Glass Houses.pdf",
    "Billy Joel - Greatest Hits.pdf",
    "Billy Joel - Keyboard Book.pdf"
)

$executions = @()

foreach ($book in $missingBooks) {
    Write-Host "Processing: $book" -ForegroundColor Cyan
    
    # Clean up book name and execution name (remove special characters)
    $cleanName = $book -replace '\.pdf$', '' -replace '  ', ' '
    $safeExecutionName = "BillyJoel-$($cleanName -replace ' ', '-' -replace '[^a-zA-Z0-9-]', '')-$(Get-Date -Format 'yyyyMMddHHmmss')"
    
    # Create execution input with correct format
    $bookId = $cleanName -replace ' ', '-' -replace '[^a-zA-Z0-9-]', '' | ForEach-Object { $_.ToLower() }
    $inputObj = @{
        book_id = $bookId
        source_pdf_uri = "s3://jsmith-input/SheetMusic/Billy Joel/books/$book"
        artist = "Billy Joel"
        book_name = $cleanName
    }
    
    # Save to temp file to avoid command line escaping issues
    $tempFile = "temp-execution-input.json"
    $inputObj | ConvertTo-Json | Out-File $tempFile -Encoding ASCII -NoNewline
    
    # Start execution
    try {
        $result = aws stepfunctions start-execution `
            --state-machine-arn $stateMachineArn `
            --name $safeExecutionName `
            --input file://$tempFile `
            --profile default `
            2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $executionArn = ($result | ConvertFrom-Json).executionArn
            Write-Host "  Started: $executionArn" -ForegroundColor Green
            
            $executions += @{
                book = $book
                execution_arn = $executionArn
            }
        } else {
            Write-Host "  ERROR: $result" -ForegroundColor Red
        }
    } catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

Write-Host "=" * 80
Write-Host "Started $($executions.Count) executions"
Write-Host "=" * 80
Write-Host ""

# Save execution ARNs
$executions | ConvertTo-Json | Out-File "billy-joel-executions.json" -Encoding UTF8

Write-Host "Execution ARNs saved to: billy-joel-executions.json"
Write-Host ""
Write-Host "Monitor executions in AWS Console or use:"
foreach ($exec in $executions) {
    Write-Host "  aws stepfunctions describe-execution --execution-arn `"$($exec.execution_arn)`" --profile default"
}
