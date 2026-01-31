# Process the 12 failed books one at a time with delays to avoid throttling

$ErrorActionPreference = "Stop"

$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$InputBucket = "jsmith-input"
$Profile = "default"

Write-Host ("=" * 80)
Write-Host "PROCESSING 12 FAILED BOOKS (ONE AT A TIME)"
Write-Host ("=" * 80)
Write-Host ""

# The 12 books that failed
$books = @(
    @{Path="C:\Work\AWSMusic\SheetMusic\_Broadway Shows\Books\Various Artists - 25th Annual Putnam County Spelling Bee.pdf"; Artist="_Broadway Shows"; Name="Various Artists - 25th Annual Putnam County Spelling Bee"}
    @{Path="C:\Work\AWSMusic\SheetMusic\_Broadway Shows\Books\Various Artists - Little Shop Of Horrors Script.pdf"; Artist="_Broadway Shows"; Name="Various Artists - Little Shop Of Horrors Script"}
    @{Path="C:\Work\AWSMusic\SheetMusic\_Movie and TV\Others\Books\The Wizard Of Oz Script.pdf"; Artist="_Movie and TV"; Name="The Wizard Of Oz Script"}
    @{Path="C:\Work\AWSMusic\SheetMusic\_Movie and TV\Others\Books\Various Artists - Complete TV And Film.pdf"; Artist="_Movie and TV"; Name="Various Artists - Complete TV And Film"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Crosby Stills and Nash\Books\Crosby Stills Nash And Young - The Guitar Collection.pdf"; Artist="Crosby Stills and Nash"; Name="Crosby Stills Nash And Young - The Guitar Collection"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Dire Straits\Books\Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_.pdf"; Artist="Dire Straits"; Name="Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Elvis Presley\Books\Elvis Presley - The Compleat _PVG Book_.pdf"; Artist="Elvis Presley"; Name="Elvis Presley - The Compleat _PVG Book_"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Eric Clapton\Books\Eric Clapton - The Cream Of Clapton.pdf"; Artist="Eric Clapton"; Name="Eric Clapton - The Cream Of Clapton"}
    @{Path="C:\Work\AWSMusic\SheetMusic\John Denver\Books\John Denver - Back Home Again.pdf"; Artist="John Denver"; Name="John Denver - Back Home Again"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Mamas and the Papas\Books\Mamas And The Papas - Songbook _PVG_.pdf"; Artist="Mamas and the Papas"; Name="Mamas And The Papas - Songbook _PVG_"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Night Ranger\Books\Night Ranger - Seven Wishes _Jap Score_.pdf"; Artist="Night Ranger"; Name="Night Ranger - Seven Wishes _Jap Score_"}
    @{Path="C:\Work\AWSMusic\SheetMusic\Robbie Robertson\Books\Robbie Robertson - Songbook _Guitar Tab_.pdf"; Artist="Robbie Robertson"; Name="Robbie Robertson - Songbook _Guitar Tab_"}
)

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
    $pdfPath = $book.Path
    $artist = $book.Artist
    $bookName = $book.Name
    
    Write-Host ("=" * 80)
    Write-Host "[$counter/$($books.Count)] Processing: $bookName"
    Write-Host ("=" * 80)
    Write-Host "  Artist: $artist"
    
    # Build S3 URI
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
    
    # Create book_id
    $bookId = $bookName -replace "[^a-zA-Z0-9-]", "-"
    $bookId = $bookId.ToLower()
    
    # Build execution input
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
        $executionName = "$bookId-retry-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        $executionArn = aws stepfunctions start-execution `
            --state-machine-arn $StateMachineArn `
            --name $executionName `
            --input "file://$tempJsonFile" `
            --profile $Profile `
            --query 'executionArn' `
            --output text
        
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
        
        Write-Host "  OK Execution started"
        Write-Host "  Execution ARN: $executionArn"
        
        $executions += [PSCustomObject]@{
            BookName = $bookName
            Artist = $artist
            ExecutionArn = $executionArn
            BookId = $bookId
        }
        
        # Wait 30 seconds before starting next book to avoid throttling
        if ($counter -lt $books.Count) {
            Write-Host ""
            Write-Host "  Waiting 30 seconds before next book to avoid API throttling..."
            Start-Sleep -Seconds 30
        }
        
    } catch {
        Write-Host "  ERROR starting execution: $_"
        Remove-Item $tempJsonFile -ErrorAction SilentlyContinue
        continue
    }
    
    Write-Host ""
}

Write-Host ("=" * 80)
Write-Host "SUMMARY"
Write-Host ("=" * 80)
Write-Host "Total books: $($books.Count)"
Write-Host "Executions started: $($executions.Count)"
Write-Host ""

if ($executions.Count -gt 0) {
    $executions | Export-Csv "failed-12-executions.csv" -NoTypeInformation
    Write-Host "OK Execution details saved to: failed-12-executions.csv"
    Write-Host ""
    Write-Host "To monitor executions, run:"
    Write-Host "  .\monitor-failed-12.ps1"
}

Write-Host ""
Write-Host "Processing initiated for all 12 books!"
Write-Host "Each book waits 30 seconds before starting the next to avoid throttling."
