# Reprocess the 12 books that are actually missing locally

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# Only the 12 books that are NOT on the local drive
$books = @(
    @{Artist="Eric Clapton"; BookName="Eric Clapton - The Cream Of Clapton"; S3Path="SheetMusic/Eric Clapton/Books/Eric Clapton - The Cream Of Clapton.pdf"}
    @{Artist="John Denver"; BookName="John Denver - Back Home Again"; S3Path="SheetMusic/John Denver/Books/John Denver - Back Home Again.pdf"}
    @{Artist="Mamas and the Papas"; BookName="Mamas And The Papas - Songbook _PVG_"; S3Path="SheetMusic/Mamas and the Papas/Books/Mamas And The Papas - Songbook _PVG_.pdf"}
    @{Artist="Robbie Robertson"; BookName="Robbie Robertson - Songbook _Guitar Tab_"; S3Path="SheetMusic/Robbie Robertson/Books/Robbie Robertson - Songbook _Guitar Tab_.pdf"}
    @{Artist="Various Artists"; BookName="Various Artists - Ultimate 80s Songs"; S3Path="SheetMusic/Various Artists/Books/Various Artists - Ultimate 80s Songs.pdf"}
    @{Artist="_Broadway Shows"; BookName="Various Artists - 25th Annual Putnam County Spelling Bee"; S3Path="SheetMusic/_Broadway Shows/Books/Various Artists - 25th Annual Putnam County Spelling Bee.pdf"}
    @{Artist="_Broadway Shows"; BookName="Various Artists - Little Shop Of Horrors Script"; S3Path="SheetMusic/_Broadway Shows/Books/Various Artists - Little Shop Of Horrors Script.pdf"}
    @{Artist="_Movie and TV"; BookName="The Wizard Of Oz Script"; S3Path="SheetMusic/_Movie and TV/Others/Books/The Wizard Of Oz Script.pdf"}
    @{Artist="_Movie and TV"; BookName="Various Artists - Complete TV And Film"; S3Path="SheetMusic/_Movie and TV/Others/Books/Various Artists - Complete TV And Film.pdf"}
    @{Artist="Crosby Stills and Nash"; BookName="Crosby Stills Nash And Young - The Guitar Collection"; S3Path="SheetMusic/Crosby Stills and Nash/Books/Crosby Stills Nash And Young - The Guitar Collection.pdf"}
    @{Artist="Dire Straits"; BookName="Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"; S3Path="SheetMusic/Dire Straits/Books/Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_.pdf"}
    @{Artist="Elvis Presley"; BookName="Elvis Presley - The Compleat _PVG Book_"; S3Path="SheetMusic/Elvis Presley/Books/Elvis Presley - The Compleat _PVG Book_.pdf"}
)

Write-Host "================================================================================"
Write-Host "REPROCESSING 12 MISSING BOOKS"
Write-Host "================================================================================"
Write-Host "These books are not found locally and need to be processed"
Write-Host ""

$executionData = @()

foreach ($book in $books) {
    $bookId = [System.Guid]::NewGuid().ToString("N").Substring(0, 16)
    $executionName = "reprocess-$timestamp-$bookId"
    $jsonFile = "temp-$bookId.json"
    
    # Create JSON file with ASCII encoding
    $jsonContent = @"
{
  "stateMachineArn": "$stateMachineArn",
  "name": "$executionName",
  "input": "{\"artist\":\"$($book.Artist)\",\"book_id\":\"$bookId\",\"source_pdf_uri\":\"s3://jsmith-input/$($book.S3Path)\",\"book_name\":\"$($book.BookName)\"}"
}
"@
    
    $jsonContent | Set-Content -Path $jsonFile -Encoding ASCII
    
    Write-Host "[$($executionData.Count + 1)/$($books.Count)] $($book.BookName)"
    
    try {
        $result = aws stepfunctions start-execution --cli-input-json "file://$jsonFile" --output json 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $resultObj = $result | ConvertFrom-Json
            $executionArn = $resultObj.executionArn
            
            $executionData += [PSCustomObject]@{
                Artist = $book.Artist
                BookName = $book.BookName
                ExecutionArn = $executionArn
                ExecutionName = $executionName
                BookId = $bookId
            }
            
            Write-Host "  SUCCESS" -ForegroundColor Green
        } else {
            Write-Host "  ERROR: $result" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
    }
    finally {
        Remove-Item $jsonFile -ErrorAction SilentlyContinue
    }
    
    # Wait 30 seconds between executions
    if ($book -ne $books[-1]) {
        Start-Sleep -Seconds 30
    }
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "COMPLETE"
Write-Host "================================================================================"
Write-Host "Started: $($executionData.Count) / $($books.Count) executions"
Write-Host ""

$csvPath = "reprocess-12-executions-$timestamp.csv"
$executionData | Export-Csv -Path $csvPath -NoTypeInformation
Write-Host "Execution data saved to: $csvPath"
Write-Host ""
Write-Host "To monitor: .\monitor-all-running.ps1"
