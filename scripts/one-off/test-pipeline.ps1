# Test the pipeline with a sample PDF

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing SheetMusic Book Splitter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Upload a test PDF
$TEST_PDF = "SheetMusic/Billy Joel/Books/Billy Joel - 52nd Street.pdf"

if (Test-Path $TEST_PDF) {
    Write-Host "Uploading test PDF to S3..." -ForegroundColor Green
    aws s3 cp $TEST_PDF "s3://jsmith-input/SheetMusic/Billy Joel/books/" --region us-east-1
    
    Write-Host ""
    Write-Host "PDF uploaded successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Triggering Ingest Service Lambda..." -ForegroundColor Yellow
    
    aws lambda invoke `
        --function-name jsmith-sheetmusic-splitter-ingest-service `
        --region us-east-1 `
        response.json
    
    Write-Host ""
    Write-Host "Lambda invoked!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Check Step Functions console to monitor execution:" -ForegroundColor Cyan
    Write-Host "https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Or check DynamoDB for processing status:" -ForegroundColor Cyan
    Write-Host "aws dynamodb scan --table-name jsmith-processing-ledger --region us-east-1" -ForegroundColor Gray
} else {
    Write-Host "Test PDF not found: $TEST_PDF" -ForegroundColor Red
    Write-Host "Please provide a valid PDF path." -ForegroundColor Yellow
}
