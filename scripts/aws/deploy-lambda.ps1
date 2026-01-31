# Deploy Lambda Functions
# This script packages and deploys all Lambda functions with their dependencies

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Lambda Function Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$region = "us-east-1"
$packageDir = "lambda-package"
$zipFile = "lambda-deployment.zip"
$s3Bucket = "jsmith-jsmith-sheetmusic-splitter-artifacts"
$s3Key = "lambda/$zipFile"

# Lambda function names
$functions = @(
    "jsmith-sheetmusic-splitter-ingest-service",
    "jsmith-sheetmusic-splitter-check-processed",
    "jsmith-sheetmusic-splitter-record-start",
    "jsmith-sheetmusic-splitter-record-success",
    "jsmith-sheetmusic-splitter-record-failure",
    "jsmith-sheetmusic-splitter-record-manual-review"
)

# Step 1: Clean up old package
Write-Host "[1/6] Cleaning up old package..." -ForegroundColor Yellow
if (Test-Path $packageDir) {
    Remove-Item -Recurse -Force $packageDir
}
if (Test-Path $zipFile) {
    Remove-Item -Force $zipFile
}

# Step 2: Create package directory
Write-Host "[2/6] Creating package directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $packageDir | Out-Null

# Step 3: Copy Lambda code and app code
Write-Host "[3/6] Copying Lambda and app code..." -ForegroundColor Yellow
Copy-Item -Path "lambda\*" -Destination $packageDir\ -Recurse
Copy-Item -Path "app" -Destination $packageDir\ -Recurse

# Step 4: Install dependencies
Write-Host "[4/6] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray
py -m pip install -r requirements.txt -t $packageDir\ --quiet

# Step 5: Create ZIP file
Write-Host "[5/6] Creating deployment ZIP..." -ForegroundColor Yellow
Push-Location $packageDir
Compress-Archive -Path * -DestinationPath "..\$zipFile" -Force
Pop-Location

$zipSize = (Get-Item $zipFile).Length / 1MB
Write-Host "  Package size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Gray

# Step 6: Upload to S3
Write-Host "[6/6] Uploading to S3..." -ForegroundColor Yellow
aws s3 cp $zipFile "s3://$s3Bucket/$s3Key" --region $region
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Failed to upload to S3" -ForegroundColor Red
    exit 1
}
Write-Host "  Uploaded to s3://$s3Bucket/$s3Key" -ForegroundColor Gray

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deploying to Lambda Functions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Deploy to each Lambda function
$successCount = 0
$failCount = 0

foreach ($functionName in $functions) {
    Write-Host "Updating $functionName..." -ForegroundColor Yellow
    
    $result = aws lambda update-function-code --function-name $functionName --s3-bucket $s3Bucket --s3-key $s3Key --region $region --no-cli-pager 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Success" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  Failed: $result" -ForegroundColor Red
        $failCount++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Successful: $successCount" -ForegroundColor Green
if ($failCount -eq 0) {
    Write-Host "  Failed: $failCount" -ForegroundColor Green
} else {
    Write-Host "  Failed: $failCount" -ForegroundColor Red
}
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "All Lambda functions updated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "  1. Test the pipeline: .\test-pipeline.ps1" -ForegroundColor White
    Write-Host "  2. Monitor execution in AWS Console" -ForegroundColor White
    Write-Host "  3. Check CloudWatch Logs for details" -ForegroundColor White
} else {
    Write-Host "Some Lambda functions failed to update" -ForegroundColor Yellow
    Write-Host "Check the errors above and retry" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Cleanup:" -ForegroundColor Cyan
Write-Host "  Package directory: $packageDir" -ForegroundColor Gray
Write-Host "  ZIP file: $zipFile" -ForegroundColor Gray
Write-Host "  S3 location: s3://$s3Bucket/$s3Key" -ForegroundColor Gray
Write-Host ""
