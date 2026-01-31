# Reprocess Specific Books
# This script allows you to reprocess books that had extraction issues

param(
    [string]$BookListFile = "",  # CSV file with books to reprocess
    [string]$SheetMusicDir = ".\SheetMusic",
    [string]$Region = "us-east-1",
    [string]$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline",
    [string]$DynamoDBTable = "jsmith-sheetmusic-splitter-books",
    [switch]$DryRun
)

$ErrorActionPreference = "Continue"

function Get-BookId {
    param($Artist, $BookName)
    $combined = "$Artist-$BookName"
    $sanitized = $combined -replace '[^a-zA-Z0-9-]', '-' -replace '-+', '-' -replace '^-|-$', ''
    return $sanitized.ToLower()
}

function Delete-DynamoDBRecord {
    param($BookId)
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would delete DynamoDB record for: $BookId" -ForegroundColor Yellow
        return $true
    }
    
    try {
        aws dynamodb delete-item `
            --table-name $DynamoDBTable `
            --key "{`"book_id`":{`"S`":`"$BookId`"}}" `
            --region $Region 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  Deleted DynamoDB record: $BookId" -ForegroundColor Green
            return $true
        } else {
            Write-Host "  Failed to delete DynamoDB record: $BookId" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  Error deleting DynamoDB record: $_" -ForegroundColor Red
        return $false
    }
}

function Start-BookProcessing {
    param($BookId, $S3Uri, $Artist, $BookName)
    
    if ($DryRun) {
        Write-Host "  [DRY RUN] Would start execution for: $BookId" -ForegroundColor Yellow
        return "dry-run"
    }
    
    try {
        $inputObj = @{
            book_id = $BookId
            source_pdf_uri = $S3Uri
            artist = $Artist
            book_name = $BookName
        }
        
        $inputJson = ($inputObj | ConvertTo-Json -Compress -Depth 10)
        $tempFile = [System.IO.Path]::GetTempFileName()
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($tempFile, $inputJson, $utf8NoBom)
        
        try {
            $result = aws stepfunctions start-execution `
                --state-machine-arn $StateMachineArn `
                --input "file://$tempFile" `
                --region $Region 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                $execution = $result | ConvertFrom-Json
                Write-Host "  Started execution: $($execution.executionArn)" -ForegroundColor Green
                return $execution.executionArn
            } else {
                Write-Host "  Failed to start execution: $result" -ForegroundColor Red
                return $null
            }
        } finally {
            Remove-Item -Path $tempFile -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Host "  Error starting execution: $_" -ForegroundColor Red
        return $null
    }
}

# Main script
Write-Host "=== Book Reprocessing Script ===" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "DRY RUN MODE - No actual changes will be made" -ForegroundColor Yellow
}
Write-Host ""

if (-not $BookListFile) {
    Write-Host "ERROR: Please provide a book list file with -BookListFile parameter" -ForegroundColor Red
    Write-Host ""
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  1. Generate report: .\generate-book-report.ps1" -ForegroundColor Gray
    Write-Host "  2. Filter CSV to books needing reprocessing" -ForegroundColor Gray
    Write-Host "  3. Run: .\reprocess-books.ps1 -BookListFile filtered-books.csv" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Or reprocess specific books by creating a CSV with columns:" -ForegroundColor Cyan
    Write-Host "  Artist,BookName" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

if (-not (Test-Path $BookListFile)) {
    Write-Host "ERROR: Book list file not found: $BookListFile" -ForegroundColor Red
    exit 1
}

# Load book list
$books = Import-Csv -Path $BookListFile

Write-Host "Found $($books.Count) books to reprocess" -ForegroundColor Green
Write-Host ""

$processed = 0
$deleted = 0
$started = 0
$failed = 0

foreach ($book in $books) {
    $processed++
    
    $artist = $book.Artist
    $bookName = $book.BookName
    
    Write-Host "[$processed/$($books.Count)] Processing: $artist - $bookName" -ForegroundColor White
    
    # Generate book ID
    $bookId = Get-BookId -Artist $artist -BookName $bookName
    
    # Find PDF file
    $pdfPath = Get-ChildItem -Path "$SheetMusicDir\$artist\Books" -Filter "*.pdf" -File | 
        Where-Object { $_.Name -like "*$bookName*" } | 
        Select-Object -First 1
    
    if (-not $pdfPath) {
        Write-Host "  ERROR: Could not find PDF for $artist - $bookName" -ForegroundColor Red
        $failed++
        continue
    }
    
    # Construct S3 URI
    $s3Key = "SheetMusic/$artist/books/$($pdfPath.Name)"
    $s3Uri = "s3://jsmith-input/$s3Key"
    
    # Delete DynamoDB record
    if (Delete-DynamoDBRecord -BookId $bookId) {
        $deleted++
    } else {
        Write-Host "  Skipping execution due to DynamoDB deletion failure" -ForegroundColor Red
        $failed++
        continue
    }
    
    # Start execution
    $executionArn = Start-BookProcessing -BookId $bookId -S3Uri $s3Uri -Artist $artist -BookName $bookName
    if ($executionArn) {
        $started++
    } else {
        $failed++
    }
    
    Write-Host ""
    Start-Sleep -Seconds 1
}

# Summary
Write-Host "=== Reprocessing Complete ===" -ForegroundColor Cyan
Write-Host "Books processed: $processed"
Write-Host "DynamoDB records deleted: $deleted"
Write-Host "Executions started: $started"
Write-Host "Failed: $failed"
Write-Host ""

if ($started -gt 0) {
    Write-Host "Monitor executions:" -ForegroundColor Cyan
    Write-Host "  aws stepfunctions list-executions --state-machine-arn $StateMachineArn --status-filter RUNNING --region $Region" -ForegroundColor Yellow
}
