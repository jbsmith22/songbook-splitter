# Process the remaining 19 unprocessed books through AWS Step Functions pipeline
$ErrorActionPreference = "Stop"

$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$InputBucket = "jsmith-input"
$Profile = "default"

Write-Host "================================================================================"
Write-Host "PROCESSING REMAINING 19 BOOKS"
Write-Host "================================================================================"
Write-Host ""

# Use the CSV with 19 remaining books (Steely Dan removed)
$books = Import-Csv "ready_for_aws_processing_remaining_19.csv"
Write-Host "Found $($books.Count) books to process"
Write-Host ""

Write-Host "Checking AWS credentials..."
try {
    aws sts get-caller-identity --profile $Profile | Out-Null
    Write-Host "OK AWS credentials valid"
} catch {
    Write-Host "ERROR AWS credentials invalid. Please run: aws sso login --profile $Profile"
    exit 1
}
Write-Host ""

$executions = @()
$counter = 0

foreach ($book in $books) {
    $counter++
    $pdfPath = $book.PDF_Path
    $artist = $book.Artist
    $bookName = $book.Book_Name
    
    Write-Host "[$counter/$($books.Count)] Processing: $bookName"
    Write-Host "  Artist: $artist"
    
    # Build S3 URI from the actual file path
    $relativePath = $pdfPath -replace "^[Cc]:\\Work\\AWSMusic\\SheetMusic\\", ""
    $relativePath = $relativePath -replace "\\", "/"
    $s3Uri = "s3://$InputBucket/SheetMusic/$relativePath"
    
    Write-Host "  S3 URI: $s3Uri"
    
    if (-not (Test-Path $pdfPath)) {
        Write-Host "  ERROR: Local file not found: $pdfPath"
        continue
    }
    
    Write-Host "  Uploading to S3..."
    try {
        aws s3 cp "$pdfPath" "$s3Uri" --profile $Profile 2>&1 | Out-Null
        Write-Host "  OK Uploaded"
    } catch {
        Write-Host "  ERROR uploading: $_"
        continue
    }
    
    # Create book_id from book name
    $bookId = $bookName -replace "[^a-zA-Z0-9-]", "-"
    $bookId = $bookId.ToLower()
    
    # Build execution input JSON and write to temp file
    $executionInput = @{
        book_id = $bookId
        source_pdf_uri = $s3Uri
        artist = $artist
        book_name = $bookName
    }
    
    $tempJsonFile = "temp-execution-input-$(Get-Date -Format 'yyyyMMdd-HHmmss')-$(Get-Random).json"
    $executionInput | ConvertTo-Json | Out-File -FilePath $tempJsonFile -Encoding ASCII
    
    Write-Host "  Starting Step Functions execution..."
    try {
        $executionName = "$bookId-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        $executionArn = aws stepfunctions start-execution `
            --state-machine-arn $StateMachineArn `
            --name $executionName `
            --input "file://$tempJsonFile" `
            --profile $Profile `
            --query 'executionArn' `
            --output text
        
        # Clean up temp file
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
        
        Write-Host "  OK Execution started: $executionArn"
        
        $executions += [PSCustomObject]@{
            BookName = $bookName
            Artist = $artist
            ExecutionArn = $executionArn
            BookId = $bookId
        }
    } catch {
        Write-Host "  ERROR starting execution: $_"
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
        continue
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500
}

Write-Host "================================================================================"
Write-Host "SUMMARY"
Write-Host "================================================================================"
Write-Host "Total books: $($books.Count)"
Write-Host "Executions started: $($executions.Count)"
Write-Host ""

if ($executions.Count -gt 0) {
    $executions | Export-Csv "remaining-19-executions.csv" -NoTypeInformation
    Write-Host "OK Execution details saved to: remaining-19-executions.csv"
    Write-Host ""
    Write-Host "To monitor executions, run:"
    Write-Host "  .\monitor-remaining-19.ps1"
}

Write-Host ""
Write-Host "Processing initiated for all remaining books!"
