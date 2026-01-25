# Register all ECS task definitions
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Registering ECS Task Definitions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$REGION = "us-east-1"
$ACCOUNT_ID = "227027150061"
$STACK_NAME = "jsmith-sheetmusic-splitter"
$IMAGE_URI = "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/jsmith-sheetmusic-splitter:latest"

# Get IAM role ARNs from CloudFormation stack
Write-Host "Getting IAM role ARNs from CloudFormation..." -ForegroundColor Yellow
$EXECUTION_ROLE_ARN = aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ECSTaskExecutionRoleArn'].OutputValue" --output text 2>$null
$TASK_ROLE_ARN = aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION --query "Stacks[0].Outputs[?OutputKey=='ECSTaskRoleArn'].OutputValue" --output text 2>$null

# If not in outputs, construct them
if ([string]::IsNullOrEmpty($EXECUTION_ROLE_ARN)) {
    $EXECUTION_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${STACK_NAME}-ECSTaskExecutionRole"
}
if ([string]::IsNullOrEmpty($TASK_ROLE_ARN)) {
    $TASK_ROLE_ARN = "arn:aws:iam::${ACCOUNT_ID}:role/${STACK_NAME}-ECSTaskRole"
}

Write-Host "  Execution Role: $EXECUTION_ROLE_ARN" -ForegroundColor Gray
Write-Host "  Task Role: $TASK_ROLE_ARN" -ForegroundColor Gray
Write-Host ""

# Task definitions to register
$TASKS = @(
    @{Name="toc-parser"; Type="toc_parser"},
    @{Name="page-mapper"; Type="page_mapper"},
    @{Name="song-verifier"; Type="song_verifier"},
    @{Name="pdf-splitter"; Type="pdf_splitter"},
    @{Name="manifest-generator"; Type="manifest_generator"}
)

foreach ($task in $TASKS) {
    $taskName = $task.Name
    $taskType = $task.Type
    $familyName = "${STACK_NAME}-${taskName}"
    
    Write-Host "[$($TASKS.IndexOf($task) + 1)/$($TASKS.Count)] Registering $familyName..." -ForegroundColor Green
    
    # Create task definition JSON
    $taskDef = @{
        family = $familyName
        networkMode = "awsvpc"
        requiresCompatibilities = @("FARGATE")
        cpu = "1024"
        memory = "2048"
        executionRoleArn = $EXECUTION_ROLE_ARN
        taskRoleArn = $TASK_ROLE_ARN
        containerDefinitions = @(
            @{
                name = $taskName
                image = $IMAGE_URI
                logConfiguration = @{
                    logDriver = "awslogs"
                    options = @{
                        "awslogs-group" = "/aws/ecs/$STACK_NAME"
                        "awslogs-region" = $REGION
                        "awslogs-stream-prefix" = $taskName
                    }
                }
                environment = @(
                    @{
                        name = "TASK_TYPE"
                        value = $taskType
                    }
                )
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress
    
    # Register task definition
    $result = aws ecs register-task-definition --cli-input-json $taskDef --region $REGION 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Success: $familyName registered" -ForegroundColor Green
    } else {
        Write-Host "  Failed: $result" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "ECS Task Definitions Registered!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Registered task definitions:" -ForegroundColor Cyan
foreach ($task in $TASKS) {
    Write-Host "  - ${STACK_NAME}-$($task.Name)" -ForegroundColor Gray
}
Write-Host ""
