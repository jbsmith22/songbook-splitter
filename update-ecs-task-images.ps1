# Update all ECS task definitions to use the latest Docker image

$taskFamilies = @(
    "jsmith-toc-discovery",
    "jsmith-toc-parser",
    "jsmith-page-mapper",
    "jsmith-song-verifier",
    "jsmith-pdf-splitter",
    "jsmith-manifest-generator"
)

$newImage = "227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest"

Write-Host "Updating ECS task definitions to use new image..." -ForegroundColor Cyan
Write-Host "New image: $newImage" -ForegroundColor Yellow
Write-Host ""

foreach ($family in $taskFamilies) {
    Write-Host "Updating $family..." -ForegroundColor Yellow
    
    # Get current task definition
    $taskDef = aws ecs describe-task-definition --task-definition $family --profile default | ConvertFrom-Json | Select-Object -ExpandProperty taskDefinition
    
    # Update image
    $taskDef.containerDefinitions[0].image = $newImage
    
    # Remove fields that can't be in register request
    $taskDef.PSObject.Properties.Remove('taskDefinitionArn')
    $taskDef.PSObject.Properties.Remove('revision')
    $taskDef.PSObject.Properties.Remove('status')
    $taskDef.PSObject.Properties.Remove('requiresAttributes')
    $taskDef.PSObject.Properties.Remove('compatibilities')
    $taskDef.PSObject.Properties.Remove('registeredAt')
    $taskDef.PSObject.Properties.Remove('registeredBy')
    
    # Save to temp file
    $tempFile = "temp_task_def.json"
    $taskDef | ConvertTo-Json -Depth 10 | Out-File $tempFile -Encoding ASCII
    
    # Register new revision
    $result = aws ecs register-task-definition --cli-input-json file://$tempFile --profile default 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        $newRevision = ($result | ConvertFrom-Json).taskDefinition.revision
        Write-Host "  SUCCESS: Registered revision $newRevision" -ForegroundColor Green
    } else {
        Write-Host "  ERROR: $result" -ForegroundColor Red
    }
    
    Write-Host ""
}

# Clean up temp file
if (Test-Path "temp_task_def.json") {
    Remove-Item "temp_task_def.json"
}

Write-Host "================================================================================"
Write-Host "Task definitions updated"
Write-Host "================================================================================"
