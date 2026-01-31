# Process all Billy Joel books in bulk
# Already processed: 52nd Street, Complete Vol 2

$books = @(
    @{name="Complete Vol 1"; file="Billy Joel - Complete Vol  1.pdf"; id="billy-joel-complete-vol1"},
    @{name="Anthology"; file="Billy Joel - Anthology.pdf"; id="billy-joel-anthology"},
    @{name="Best Of Piano Solos"; file="Billy Joel - Best Of Piano Solos.pdf"; id="billy-joel-best-piano-solos"},
    @{name="Fantasies & Delusions"; file="Billy Joel - Fantasies & Delusions.pdf"; id="billy-joel-fantasies-delusions"},
    @{name="For Advanced Piano"; file="Billy Joel - For Advanced Piano.pdf"; id="billy-joel-advanced-piano"},
    @{name="Glass Houses"; file="Billy Joel - Glass Houses.pdf"; id="billy-joel-glass-houses"},
    @{name="Greatest Hits Vol I and II"; file="Billy Joel - Greatest Hits Vol I and II.pdf"; id="billy-joel-greatest-hits-1-2"},
    @{name="Greatest Hits Vol III"; file="Billy Joel - Greatest Hits Vol III.pdf"; id="billy-joel-greatest-hits-3"},
    @{name="Greatest Hits"; file="Billy Joel - Greatest Hits.pdf"; id="billy-joel-greatest-hits"},
    @{name="Keyboard Book"; file="Billy Joel - Keyboard Book.pdf"; id="billy-joel-keyboard-book"},
    @{name="My Lives"; file="Billy Joel - My Lives.pdf"; id="billy-joel-my-lives"},
    @{name="Rock Score"; file="Billy Joel - Rock Score.pdf"; id="billy-joel-rock-score"},
    @{name="Songs in the Attic"; file="Billy Joel - Songs in the Attic.pdf"; id="billy-joel-songs-attic"},
    @{name="Turnstiles"; file="Billy Joel - Turnstiles.pdf"; id="billy-joel-turnstiles"}
)

$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$inputBucket = "s3://jsmith-input/SheetMusic/Billy Joel/books/"
$outputBucket = "s3://jsmith-output/SheetMusicOut/Billy Joel/books/"
$localSourcePath = "SheetMusic/Billy Joel/Books/"

Write-Host "Processing $($books.Count) Billy Joel books..." -ForegroundColor Cyan
Write-Host ""

foreach ($book in $books) {
    Write-Host "=" * 80 -ForegroundColor Yellow
    Write-Host "Processing: $($book.name)" -ForegroundColor Green
    Write-Host "=" * 80 -ForegroundColor Yellow
    
    # Upload to S3
    Write-Host "1. Uploading to S3..."
    $sourcePath = Join-Path $localSourcePath $book.file
    aws s3 cp $sourcePath ($inputBucket + $book.file)
    
    # Create execution input
    $inputData = @{
        book_id = $book.id
        source_pdf_uri = $inputBucket + $book.file
        artist = "Billy Joel"
        book_name = $book.name
    }
    
    $inputFile = "temp_input_$($book.id).json"
    $inputData | ConvertTo-Json -Depth 10 | Out-File -FilePath $inputFile -Encoding ASCII -NoNewline
    
    # Start execution using file:// protocol
    Write-Host "2. Starting pipeline execution..."
    $execution = aws stepfunctions start-execution --state-machine-arn $stateMachineArn --input "file://$inputFile" | ConvertFrom-Json
    $executionArn = $execution.executionArn
    Write-Host "   Execution ARN: $executionArn" -ForegroundColor Gray
    
    # Monitor execution
    Write-Host "3. Monitoring execution..."
    $startTime = Get-Date
    while ($true) {
        Start-Sleep -Seconds 30
        $status = aws stepfunctions describe-execution --execution-arn $executionArn --query '{status:status,stopDate:stopDate}' --output json | ConvertFrom-Json
        
        $elapsed = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
        Write-Host "   [$elapsed min] Status: $($status.status)" -ForegroundColor Gray
        
        if ($status.status -ne "RUNNING") {
            Write-Host "   Completed with status: $($status.status)" -ForegroundColor $(if ($status.status -eq "SUCCEEDED") { "Green" } else { "Red" })
            break
        }
    }
    
    # Download results if successful
    if ($status.status -eq "SUCCEEDED") {
        Write-Host "4. Downloading results..."
        $outputDir = "billy_joel_output/$($book.name)"
        New-Item -ItemType Directory -Force -Path $outputDir | Out-Null
        
        $s3Path = $outputBucket + $book.name + "/"
        aws s3 cp $s3Path $outputDir/ --recursive
        
        # Download manifest
        $artifactPath = "s3://jsmith-output/artifacts/$($book.id)/"
        aws s3 cp ($artifactPath + "page_mapping.json") "$outputDir/_page_mapping.json" --quiet
        aws s3 cp ($artifactPath + "verified_songs.json") "$outputDir/_verified_songs.json" --quiet
        
        # Count songs
        $songCount = (Get-ChildItem "$outputDir/*.pdf" | Measure-Object).Count
        Write-Host "   Downloaded $songCount songs to $outputDir" -ForegroundColor Green
    }
    
    # Cleanup
    Remove-Item $inputFile -ErrorAction SilentlyContinue
    
    Write-Host ""
}

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "All books processed!" -ForegroundColor Green
Write-Host "Results are in: billy_joel_output/" -ForegroundColor Cyan
