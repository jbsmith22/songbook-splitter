# Register all ECS task definitions using template files
$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Registering ECS Task Definitions" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$REGION = "us-east-1"
$ACCOUNT_ID = "227027150061"
$STACK_NAME = "jsmith-sheetmusic-splitter"

# Task definitions to register
$TASKS = @("toc-parser", "page-mapper", "song-verifier", "pdf-splitter", "manifest-generator")

$count = 0
foreach ($taskName in $TASKS) {
    $count++
    $familyName = "${STACK_NAME}-${taskName}"
    
    Write-Host "[$count/$($TASKS.Count)] Registering $familyName..." -ForegroundColor Green
    
    # Get existing toc-discovery task definition as template
    $template = aws ecs describe-task-definition --task-definition "${STACK_NAME}-toc-discovery" --region $REGION --query 'taskDefinition' --output json | ConvertFrom-Json
    
    # Update for new task
    $template.family = $familyName
    $template.containerDefinitions[0].name = $taskName
    $template.containerDefinitions[0].logConfiguration.options.'awslogs-stream-prefix' = $taskName
    $template.containerDefinitions[0].environment[0].value = $taskName.Replace("-", "_")
    
    # Remove fields that shouldn't be in registration
    $template.PSObject.Properties.Remove('taskDefinitionArn')
    $template.PSObject.Properties.Remove('revision')
    $template.PSObject.Properties.Remove('status')
    $template.PSObject.Properties.Remove('requiresAttributes')
    $template.PSObject.Properties.Remove('compatibilities')
    $template.PSObject.Properties.Remove('registeredAt')
    $template.PSObject.Properties.Remove('registeredBy')
    
    # Save to temp file
    $tempFile = "temp-task-def.json"
    $template | ConvertTo-Json -Depth 10 | Out-File -FilePath $tempFile -Encoding utf8
    
    # Register
    aws ecs register-task-definition --cli-input-json file://$tempFile --region $REGION | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Success" -ForegroundColor Green
    } else {
        Write-Host "  Failed" -ForegroundColor Red
    }
    
    Remove-Item $tempFile -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All Task Definitions Registered!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
