# Test processing one book (Steely Dan - The Best)
$ErrorActionPreference = "Stop"

$StateMachineArn = "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"
$InputBucket = "jsmith-input"
$Profile = "default"

# Test with Steely Dan
$pdfPath = "C:\Work\AWSMusic\SheetMusic\Steely Dan\Books\Steely Dan - The Best.pdf"
$artist = "Steely Dan"
$bookName = "Steely Dan - The Best"

Write-Host "================================================================================"
Write-Host "TEST: Processing Single Book"
Write-Host "================================================================================"
Write-Host ""
Write-Host "Book: $bookName"
Write-Host "Artist: $artist"
Write-Host "Path: $pdfPath"
Write-Host ""

# Check file exists
if (-not (Test-Path $pdfPath)) {
    Write-Host "ERROR: File not found: $pdfPath"
    exit 1
}
Write-Host "OK File exists"

# Check AWS credentials
Write-Host "Checking AWS credentials..."
try {
    $identity = aws sts get-caller-identity --profile $Profile | ConvertFrom-Json
    Write-Host "OK Logged in as: $($identity.Arn)"
} catch {
    Write-Host "ERROR: AWS credentials invalid. Please run: aws sso login --profile $Profile"
    exit 1
}
Write-Host ""

# Build S3 URI
$relativePath = $pdfPath -replace "^[Cc]:\\Work\\AWSMusic\\SheetMusic\\", ""
$relativePath = $relativePath -replace "\\", "/"
$s3Uri = "s3://$InputBucket/SheetMusic/$relativePath"

Write-Host "S3 URI: $s3Uri"
Write-Host ""

# Upload to S3
Write-Host "Uploading to S3..."
try {
    aws s3 cp "$pdfPath" "$s3Uri" --profile $Profile 2>&1 | Out-Null
    Write-Host "OK Uploaded"
} catch {
    Write-Host "ERROR uploading: $_"
    exit 1
}
Write-Host ""

# Create execution input
$bookId = "steely-dan-the-best"
$executionInput = @{
    book_id = $bookId
    source_pdf_uri = $s3Uri
    artist = $artist
    book_name = $bookName
}

# Write to temp JSON file (AWS CLI needs file:// protocol for complex JSON)
$tempJsonFile = "temp-steely-dan-input.json"
$executionInput | ConvertTo-Json | Out-File -FilePath $tempJsonFile -Encoding ASCII

Write-Host "Execution Input:"
Get-Content $tempJsonFile
Write-Host ""

# Start execution
Write-Host "Starting Step Functions execution..."
try {
    $executionName = "$bookId-test-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $executionArn = aws stepfunctions start-execution `
        --state-machine-arn $StateMachineArn `
        --name $executionName `
        --input "file://$tempJsonFile" `
        --profile $Profile `
        --query 'executionArn' `
        --output text
    
    Write-Host "OK Execution started!"
    Write-Host ""
    Write-Host "Execution ARN: $executionArn"
    Write-Host ""
    Write-Host "To monitor this execution, run:"
    Write-Host "  .\monitor-execution.ps1 -ExecutionArn '$executionArn'"
} catch {
    Write-Host "ERROR starting execution: $_"
    exit 1
}
