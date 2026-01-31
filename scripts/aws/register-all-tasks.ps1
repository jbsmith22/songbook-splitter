# Register all ECS task definitions
$ErrorActionPreference = "Stop"

Write-Host "Registering ECS Task Definitions..." -ForegroundColor Cyan

$tasks = @("toc-parser", "page-mapper", "song-verifier", "pdf-splitter", "manifest-generator")

foreach ($task in $tasks) {
    Write-Host "  Registering $task..." -ForegroundColor Yellow
    
    # Create task definition JSON
    $taskDef = @"
{
  "family": "jsmith-sheetmusic-splitter-$task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::227027150061:role/jsmith-sheetmusic-splitter-ECSTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::227027150061:role/jsmith-sheetmusic-splitter-ECSTaskRole",
  "containerDefinitions": [
    {
      "name": "$task",
      "image": "227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest",
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/aws/ecs/jsmith-sheetmusic-splitter",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "$task"
        }
      },
      "environment": [
        {
          "name": "TASK_TYPE",
          "value": "$($task.Replace('-', '_'))"
        }
      ]
    }
  ]
}
"@
    
    # Save to temp file
    $tempFile = "temp-$task.json"
    $taskDef | Out-File -FilePath $tempFile -Encoding utf8
    
    # Register
    aws ecs register-task-definition --cli-input-json file://$tempFile --region us-east-1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "    Success!" -ForegroundColor Green
    } else {
        Write-Host "    Failed!" -ForegroundColor Red
    }
    
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "All task definitions registered!" -ForegroundColor Green
