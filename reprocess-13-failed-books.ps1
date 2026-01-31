# Reprocess the 13 books that failed in the original batch
# These books failed due to the page_mapper bug which is now fixed

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

# The 13 books that failed (excluding the 6 that succeeded)
$books = @(
    @{Artist="_Broadway Shows"; BookName="Various Artists - 25th Annual Putnam County Spelling Bee"; S3Path="SheetMusic/_Broadway Shows/Books/Various Artists - 25th Annual Putnam County Spelling Bee.pdf"}
    @{Artist="_Broadway Shows"; BookName="Various Artists - Little Shop Of Horrors Script"; S3Path="SheetMusic/_Broadway Shows/Books/Various Artists - Little Shop Of Horrors Script.pdf"}
    @{Artist="_Movie and TV"; BookName="The Wizard Of Oz Script"; S3Path="SheetMusic/_Movie and TV/Others/Books/The Wizard Of Oz Script.pdf"}
    @{Artist="_Movie and TV"; BookName="Various Artists - Complete TV And Film"; S3Path="SheetMusic/_Movie and TV/Others/Books/Various Artists - Complete TV And Film.pdf"}
    @{Artist="Crosby Stills and Nash"; BookName="Crosby Stills Nash And Young - The Guitar Collection"; S3Path="SheetMusic/Crosby Stills and Nash/Books/Crosby Stills Nash And Young - The Guitar Collection.pdf"}
    @{Artist="Dire Straits"; BookName="Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_"; S3Path="SheetMusic/Dire Straits/Books/Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_.pdf"}
    @{Artist="Elvis Presley"; BookName="Elvis Presley - The Compleat _PVG Book_"; S3Path="SheetMusic/Elvis Presley/Books/Elvis Presley - The Compleat _PVG Book_.pdf"}
    @{Artist="Eric Clapton"; BookName="Eric Clapton - The Cream Of Clapton"; S3Path="SheetMusic/Eric Clapton/Books/Eric Clapton - The Cream Of Clapton.pdf"}
    @{Artist="John Denver"; BookName="John Denver - Back Home Again"; S3Path="SheetMusic/John Denver/Books/John Denver - Back Home Again.pdf"}
    @{Artist="Mamas and the Papas"; BookName="Mamas And The Papas - Songbook _PVG_"; S3Path="SheetMusic/Mamas and the Papas/Books/Mamas And The Papas - Songbook _PVG_.pdf"}
    @{Artist="Robbie Robertson"; BookName="Robbie Robertson - Songbook _Guitar Tab_"; S3Path="SheetMusic/Robbie Robertson/Books/Robbie Robertson - Songbook _Guitar Tab_.pdf"}
    @{Artist="Tom Waits"; BookName="Tom Waits - Tom Waits Anthology"; S3Path="SheetMusic/Tom Waits/Books/Tom Waits - Tom Waits Anthology.pdf"}
    @{Artist="Various Artists"; BookName="Various Artists - Ultimate 80s Songs"; S3Path="SheetMusic/Various Artists/Books/Various Artists - Ultimate 80s Songs.pdf"}
)

Write-Host "================================================================================"
Write-Host "REPROCESSING 13 FAILED BOOKS WITH BUG FIX"
Write-Host "================================================================================"
Write-Host "Total books to process: $($books.Count)"
Write-Host "Starting all executions simultaneously"
Write-Host ""

$executionArns = @()
$executionData = @()

foreach ($book in $books) {
    $bookId = [System.Guid]::NewGuid().ToString("N").Substring(0, 16)
    $executionName = "reprocess-fix-$timestamp-$bookId"
    
    $inputJson = @"
{"artist":"$($book.Artist)","book_id":"$bookId","source_pdf_uri":"s3://jsmith-input/$($book.S3Path)","book_name":"$($book.BookName)"}
"@
    
    Write-Host "Processing: $($book.BookName)"
    Write-Host "  Artist: $($book.Artist)"
    Write-Host "  Book ID: $bookId"
    
    try {
        $result = aws stepfunctions start-execution --state-machine-arn $stateMachineArn --name $executionName --input $inputJson --output json 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ERROR: $result" -ForegroundColor Red
            Write-Host ""
            continue
        }
        
        $resultObj = $result | ConvertFrom-Json
        $executionArn = $resultObj.executionArn
        $executionArns += $executionArn
        
        $executionData += [PSCustomObject]@{
            Artist = $book.Artist
            BookName = $book.BookName
            ExecutionArn = $executionArn
            ExecutionName = $executionName
            S3Path = $book.S3Path
            BookId = $bookId
        }
        
        Write-Host "  SUCCESS: Started $executionName" -ForegroundColor Green
        Write-Host ""
    }
    catch {
        Write-Host "  ERROR: $_" -ForegroundColor Red
        Write-Host ""
    }
}

Write-Host "================================================================================"
Write-Host "ALL EXECUTIONS STARTED"
Write-Host "================================================================================"
Write-Host "Total executions: $($executionArns.Count)"
Write-Host ""

$csvPath = "reprocess-13-failed-books-$timestamp.csv"
$executionData | Export-Csv -Path $csvPath -NoTypeInformation
Write-Host "Execution data saved to: $csvPath"
Write-Host ""
Write-Host "To monitor all executions, run: monitor-all-running.ps1"
