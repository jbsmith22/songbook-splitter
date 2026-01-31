# Process the remaining 20 unprocessed books through AWS Step Functions pipeline
$ErrorActionPreference = "Stop"

$StateMachineArn = "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine"
$InputBucket = "jsmith-input"
$Profile = "default"

Write-Host "================================================================================"
Write-Host "PROCESSING REMAINING 20 BOOKS"
Write-Host "================================================================================"
Write-Host ""

$books = Import-Csv "ready_for_aws_processing.csv"
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
    
    $relativePath = $pdfPath -replace "^c:\\Work\\AWSMusic\\SheetMusic\\", ""
    $relativePath = $relativePath -replace "\\", "/"
    $s3Uri = "s3://$InputBucket/SheetMusic/$relativePath"
    
    Write-Host "  S3 URI: $s3Uri"
    
    if (-not (Test-Path $pdfPath)) {
        Write-Host "  ERROR: Local file not found: $pdfPath"
        continue
    }
    
    Write-Host "  Uploading to S3..."
    try {
        aws s3 cp "$pdfPath" "$s3Uri" --profile $Profile | Out-Null
        Write-Host "  OK Uploaded"
    } catch {
        Write-Host "  ERROR uploading: $_"
        continue
    }
    
    $bookId = $bookName -replace "[^a-zA-Z0-9-]", "-"
    $bookId = $bookId.ToLower()
    
    $executionInput = @{
        book_id = $bookId
        source_pdf_uri = $s3Uri
        artist = $artist
        book_name = $bookName
    } | ConvertTo-Json -Compress
    
    Write-Host "  Starting Step Functions execution..."
    try {
        $executionArn = aws stepfunctions start-execution --state-machine-arn $StateMachineArn --name "$bookId-$(Get-Date -Format 'yyyyMMdd-HHmmss')" --input $executionInput --profile $Profile --query 'executionArn' --output text
        
        Write-Host "  OK Execution started: $executionArn"
        
        $executions += @{
            BookName = $bookName
            Artist = $artist
            ExecutionArn = $executionArn
            BookId = $bookId
        }
    } catch {
        Write-Host "  ERROR starting execution: $_"
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
    $executions | Export-Csv "remaining-20-executions.csv" -NoTypeInformation
    Write-Host "OK Execution details saved to: remaining-20-executions.csv"
    Write-Host ""
    Write-Host "To monitor executions, run:"
    Write-Host "  .\monitor-remaining-20.ps1"
}

Write-Host ""
Write-Host "Processing initiated for all remaining books!"
