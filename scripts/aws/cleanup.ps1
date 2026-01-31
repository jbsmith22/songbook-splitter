# Cleanup script - Destroys ALL resources created by deployment
# WARNING: This will delete all data in S3 buckets and DynamoDB!

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Red
Write-Host "CLEANUP - DESTROY ALL RESOURCES" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will delete:" -ForegroundColor Yellow
Write-Host "  - CloudFormation stack: jsmith-sheetmusic-splitter" -ForegroundColor Yellow
Write-Host "  - S3 buckets: jsmith-input, jsmith-output, jsmith-sheetmusic-splitter-artifacts" -ForegroundColor Yellow
Write-Host "  - DynamoDB table: jsmith-processing-ledger" -ForegroundColor Yellow
Write-Host "  - ECR repository: jsmith-sheetmusic-splitter" -ForegroundColor Yellow
Write-Host "  - All Lambda functions, ECS tasks, Step Functions, CloudWatch alarms" -ForegroundColor Yellow
Write-Host ""

$confirmation = Read-Host "Are you sure you want to delete everything? Type 'DELETE' to confirm"

if ($confirmation -ne "DELETE") {
    Write-Host ""
    Write-Host "Cleanup cancelled." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Starting cleanup..." -ForegroundColor Red
Write-Host ""

# Step 1: Empty S3 buckets
Write-Host "Step 1: Emptying S3 buckets..." -ForegroundColor Yellow

$buckets = @("jsmith-input", "jsmith-output", "jsmith-sheetmusic-splitter-artifacts")

foreach ($bucket in $buckets) {
    Write-Host "  Emptying bucket: $bucket" -ForegroundColor Gray
    aws s3 rm "s3://$bucket" --recursive --region us-east-1 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    ✓ Emptied" -ForegroundColor Green
    } else {
        Write-Host "    ⚠ Bucket may not exist or already empty" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 2: Delete CloudFormation stack
Write-Host "Step 2: Deleting CloudFormation stack..." -ForegroundColor Yellow
aws cloudformation delete-stack --stack-name jsmith-sheetmusic-splitter --region us-east-1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  Stack deletion initiated" -ForegroundColor Green
    Write-Host "  Waiting for deletion to complete (this may take 5-10 minutes)..." -ForegroundColor Gray
    
    aws cloudformation wait stack-delete-complete --stack-name jsmith-sheetmusic-splitter --region us-east-1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ Stack deleted successfully" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Stack deletion may have failed or timed out" -ForegroundColor Yellow
        Write-Host "  Check CloudFormation console for details" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ⚠ Failed to initiate stack deletion" -ForegroundColor Red
}

Write-Host ""

# Step 3: Delete ECR repository
Write-Host "Step 3: Deleting ECR repository..." -ForegroundColor Yellow
aws ecr delete-repository --repository-name jsmith-sheetmusic-splitter --force --region us-east-1 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ ECR repository deleted" -ForegroundColor Green
} else {
    Write-Host "  ⚠ ECR repository may not exist or already deleted" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "CLEANUP COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "All resources have been deleted." -ForegroundColor Green
Write-Host "No ongoing charges will occur." -ForegroundColor Green
Write-Host ""
