# Docker Image Build and Push Script
# Builds the Docker image and pushes it to ECR

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Image Build and Push" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$REGION = "us-east-1"
$ACCOUNT_ID = "227027150061"
$REPOSITORY_NAME = "jsmith-sheetmusic-splitter"
$IMAGE_TAG = "latest"
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPOSITORY_NAME"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Region: $REGION"
Write-Host "  Account: $ACCOUNT_ID"
Write-Host "  Repository: $REPOSITORY_NAME"
Write-Host "  Image Tag: $IMAGE_TAG"
Write-Host "  ECR URI: $ECR_URI"
Write-Host ""

# Step 1: Login to ECR
Write-Host "[1/4] Logging in to ECR..." -ForegroundColor Green
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to login to ECR" -ForegroundColor Red
    exit 1
}

Write-Host "Successfully logged in to ECR" -ForegroundColor Green
Write-Host ""

# Step 2: Build Docker image
Write-Host "[2/4] Building Docker image..." -ForegroundColor Green
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

docker build -t $REPOSITORY_NAME .

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to build Docker image" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Successfully built Docker image" -ForegroundColor Green
Write-Host ""

# Step 3: Tag image for ECR
Write-Host "[3/4] Tagging image for ECR..." -ForegroundColor Green
docker tag "${REPOSITORY_NAME}:latest" "${ECR_URI}:${IMAGE_TAG}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to tag Docker image" -ForegroundColor Red
    exit 1
}

Write-Host "Successfully tagged image" -ForegroundColor Green
Write-Host ""

# Step 4: Push to ECR
Write-Host "[4/4] Pushing image to ECR..." -ForegroundColor Green
Write-Host "This may take a few minutes..." -ForegroundColor Yellow
Write-Host ""

docker push "${ECR_URI}:${IMAGE_TAG}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to push Docker image to ECR" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "DOCKER IMAGE DEPLOYED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Image URI: ${ECR_URI}:${IMAGE_TAG}" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. ECS tasks will automatically use the new image on next execution"
Write-Host "2. Trigger a new Step Functions execution to test"
Write-Host "3. Check CloudWatch logs for task output"
Write-Host ""
