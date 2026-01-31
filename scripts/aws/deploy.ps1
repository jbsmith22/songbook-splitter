# Deployment script for SheetMusic Book Splitter
# Account: 227027150061
# Region: us-east-1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "SheetMusic Book Splitter - Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$STACK_NAME = "jsmith-sheetmusic-splitter"
$REGION = "us-east-1"
$VPC_ID = "vpc-4c5f5735"
$SUBNET_ID = "subnet-0f6ba7ae50933273e"
$CONTAINER_IMAGE = "227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest"

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Stack Name: $STACK_NAME"
Write-Host "  Region: $REGION"
Write-Host "  VPC: $VPC_ID"
Write-Host "  Subnet: $SUBNET_ID"
Write-Host "  Container Image: $CONTAINER_IMAGE"
Write-Host ""

# Deploy CloudFormation stack
Write-Host "Deploying CloudFormation stack..." -ForegroundColor Green

aws cloudformation create-stack `
    --stack-name $STACK_NAME `
    --template-body file://infra/cloudformation_template.yaml `
    --parameters `
        ParameterKey=VpcId,ParameterValue=$VPC_ID `
        ParameterKey=SubnetIds,ParameterValue=$SUBNET_ID `
        ParameterKey=ContainerImage,ParameterValue=$CONTAINER_IMAGE `
    --capabilities CAPABILITY_IAM `
    --region $REGION

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Stack creation initiated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Waiting for stack creation to complete..." -ForegroundColor Yellow
    Write-Host "(This will take 10-15 minutes)" -ForegroundColor Yellow
    Write-Host ""
    
    aws cloudformation wait stack-create-complete `
        --stack-name $STACK_NAME `
        --region $REGION
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        
        # Get stack outputs
        Write-Host "Stack Outputs:" -ForegroundColor Cyan
        aws cloudformation describe-stacks `
            --stack-name $STACK_NAME `
            --region $REGION `
            --query "Stacks[0].Outputs" `
            --output table
    } else {
        Write-Host ""
        Write-Host "Stack creation failed or timed out." -ForegroundColor Red
        Write-Host "Check CloudFormation console for details." -ForegroundColor Red
    }
} else {
    Write-Host ""
    Write-Host "Failed to initiate stack creation." -ForegroundColor Red
    Write-Host "Check the error message above." -ForegroundColor Red
}
