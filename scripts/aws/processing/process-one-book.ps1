# Process a single book through AWS Step Functions pipeline (for testing)
param(
    [Parameter(Mandatory=$true)]
    [string]$BookName
)

$ErrorActionPreference = "Stop"

# Configuration
$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$InputBucket = "jsmith-input"
$Profile = "default"

Write-Host "================================================================================"
Write-Host "PROCESSING SINGLE BOOK: $BookName"
Write-Host "================================================================================"
Write-Host ""

# Find the PDF file
Write-Host "Searching for PDF file..."
$pdfFile = Get-ChildItem "SheetMusic" -Recurse -Filter "*.pdf" | Where-Object { 
    $_.Name -like "*$BookName*" -and $_.FullName -notlike "*_Fake Books*"
} | Select-Object -First 1

if (-not $pdfFile) {
    Write-Host "ERROR: Could not find PDF matching: $BookName"
    exit 1
}

Write-Host "Found: $($pdfFile.FullName)"
Write-Host ""

# Extract artist from path
$relativePath = $pdfFile.FullName -replace "^.*\\SheetMusic\\", ""
$pathParts = $relativePath -split "\\"
$artist = $pathParts[0]
$pdfName = $pdfFile.BaseName

Write-Host "Artist: $artist"
Write-Host "Book Name: $pdfName"
Write-Host ""

# Check AWS credentials
Write-Host "Checking AWS credentials..."
try {
    aws sts get-caller-identity --profile $Profile | Out-Null
    Write-Host "OK AWS credentials valid"
} catch {
    Write-Host "ERROR AWS credentials invalid. Please run: aws sso login --profile $Profile"
    exit 1
}
Write-Host ""

# Convert local path to S3 path
$s3RelativePath = $relativePath -replace "\\", "/"
$s3Uri = "s3://$InputBucket/SheetMusic/$s3RelativePath"

Write-Host "S3 URI: $s3Uri"
Write-Host ""

# Upload to S3
Write-Host "Uploading to S3..."
try {
    aws s3 cp "$($pdfFile.FullName)" "$s3Uri" --profile $Profile
    Write-Host "OK Uploaded"
} catch {
    Write-Host "ERROR uploading: $_"
    exit 1
}
Write-Host ""

# Create execution input
$bookId = $pdfName -replace "[^a-zA-Z0-9-]", "-"
$bookId = $bookId.ToLower()

$executionInput = @{
    book_id = $bookId
    source_pdf_uri = $s3Uri
    artist = $artist
    book_name = $pdfName
}

Write-Host "Execution Input:"
Write-Host ($executionInput | ConvertTo-Json)
Write-Host ""

# Save to temp file
$tempFile = "temp-execution-input-$(Get-Date -Format 'yyyyMMdd-HHmmss').json"
$executionInput | ConvertTo-Json | Out-File -FilePath $tempFile -Encoding UTF8

# Start Step Functions execution
Write-Host "Starting Step Functions execution..."
try {
    $executionArn = aws stepfunctions start-execution `
        --state-machine-arn $StateMachineArn `
        --name "$bookId-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
        --input "file://$tempFile" `
        --profile $Profile `
        --query 'executionArn' `
        --output text
    
    Write-Host "OK Execution started!"
    Write-Host "Execution ARN: $executionArn"
    
    # Clean up temp file
    Remove-Item $tempFile -ErrorAction SilentlyContinue
} catch {
    Write-Host "ERROR starting execution: $_"
    Remove-Item $tempFile -ErrorAction SilentlyContinue
    exit 1
}

Write-Host ""
Write-Host "================================================================================"
Write-Host "To monitor this execution:"
Write-Host "  .\monitor-execution.ps1 -ExecutionArn $executionArn"
Write-Host ""
Write-Host "Or check status:"
Write-Host "  aws stepfunctions describe-execution --execution-arn $executionArn --profile $Profile"
Write-Host "================================================================================"
