# Process the books that failed due to filename mismatches

$ErrorActionPreference = "Stop"

# Books that failed with their search patterns
$booksToFind = @(
    @{Artist="America"; Pattern="*Greatest Hits*Book*"},
    @{Artist="Ben Folds"; Pattern="*Rockin*Suburbs*Book*"},
    @{Artist="Dire Straits"; Pattern="*Mark Knopfler*"},
    @{Artist="ELO"; Pattern="*Elton John*Collection*"},
    @{Artist="Elvis Presley"; Pattern="*Compleat*"},
    @{Artist="Kinks"; Pattern="*Guitar Legends*Tab*"},
    @{Artist="Mamas and the Papas"; Pattern="*Songbook*PVG*"},
    @{Artist="Night Ranger"; Pattern="*Best Of 2*"},
    @{Artist="Robbie Robertson"; Pattern="*Songbook*Tab*"},
    @{Artist="Tom Lehrer"; Pattern="*Too Many Songs*"},
    @{Artist="Wings"; Pattern="*Over America*"},
    @{Artist="_Broadway Shows"; Pattern="*High School Musical 1*Libretto*"; Path="SheetMusic\_Broadway Shows\Books"}
)

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Processing Failed Books (Fixed Filenames)" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$inputBucket = "jsmith-input"
$outputBucket = "jsmith-output"
$stateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"

$executionArns = @()
$successCount = 0
$failCount = 0

foreach ($bookInfo in $booksToFind) {
    $artist = $bookInfo.Artist
    $pattern = $bookInfo.Pattern
    
    # Determine path
    if ($bookInfo.Path) {
        $searchPath = $bookInfo.Path
    } else {
        $searchPath = "SheetMusic\$artist\books"
    }
    
    Write-Host "Searching: $artist - $pattern" -ForegroundColor Yellow
    
    if (-not (Test-Path $searchPath)) {
        Write-Host "  ERROR: Path not found: $searchPath" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    # Find the file
    $files = Get-ChildItem $searchPath -Filter "*.pdf" | Where-Object { $_.Name -like $pattern }
    
    if ($files.Count -eq 0) {
        Write-Host "  ERROR: No file found matching pattern" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    if ($files.Count -gt 1) {
        Write-Host "  WARNING: Multiple files found, using first one" -ForegroundColor Yellow
    }
    
    $file = $files[0]
    $sourcePath = $file.FullName
    $fileName = $file.Name
    $bookName = $file.BaseName
    
    Write-Host "  Found: $fileName"
    
    # Upload to S3
    $s3Key = "books/$artist/$fileName"
    Write-Host "  Uploading to S3: $s3Key"
    
    try {
        $uploadResult = aws s3 cp $sourcePath "s3://$inputBucket/$s3Key" --profile default 2>&1
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  FAILED to upload: $uploadResult" -ForegroundColor Red
            $failCount++
            Write-Host ""
            continue
        }
        
        Write-Host "  Uploaded successfully" -ForegroundColor Green
    } catch {
        Write-Host "  ERROR uploading: $_" -ForegroundColor Red
        $failCount++
        Write-Host ""
        continue
    }
    
    # Start execution
    $executionInput = @{
        input_bucket = $inputBucket
        output_bucket = $outputBucket
        s3_key = $s3Key
        artist = $artist
    }
    
    $tempFile = "temp-exec-$(Get-Date -Format 'yyyyMMddHHmmss').json"
    $executionInput | ConvertTo-Json | Out-File -FilePath $tempFile -Encoding ASCII -NoNewline
    
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss-fff"
    $sanitizedName = ($bookName -replace '[^a-zA-Z0-9-]', '-').ToLower()
    $executionName = "fixed-$sanitizedName-$timestamp"
    
    try {
        $result = aws stepfunctions start-execution `
            --state-machine-arn $stateMachineArn `
            --name $executionName `
            --input file://$tempFile `
            --profile default `
            2>&1
        
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        
        if ($LASTEXITCODE -eq 0) {
            $executionArn = ($result | ConvertFrom-Json).executionArn
            $executionArns += [PSCustomObject]@{
                Artist = $artist
                BookName = $bookName
                ExecutionArn = $executionArn
                ExecutionName = $executionName
                S3Key = $s3Key
            }
            Write-Host "  Started execution: $executionName" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  FAILED to start execution: $result" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  ERROR starting execution: $_" -ForegroundColor Red
        Remove-Item $tempFile -ErrorAction SilentlyContinue
        $failCount++
    }
    
    Write-Host ""
    Start-Sleep -Milliseconds 500
}

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "Summary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Executions started: $successCount" -ForegroundColor Green
Write-Host "Failed: $failCount" -ForegroundColor Red
Write-Host ""

if ($executionArns.Count -gt 0) {
    # Append to existing executions file
    if (Test-Path "remaining-books-executions.csv") {
        $existing = Import-Csv "remaining-books-executions.csv"
        $combined = $existing + $executionArns
        $combined | Export-Csv "remaining-books-executions.csv" -NoTypeInformation -Encoding UTF8
    } else {
        $executionArns | Export-Csv "remaining-books-executions.csv" -NoTypeInformation -Encoding UTF8
    }
    Write-Host "Execution details saved to: remaining-books-executions.csv" -ForegroundColor Cyan
}

Write-Host "================================================================================" -ForegroundColor Cyan
