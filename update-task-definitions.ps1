# Update all ECS task definitions to use the new Docker image digest

$imageDigest = "sha256:ab013612b95960e7011c74f91d84b1001b715acebb027fcd4ba5e0c5a72c6605"
$imageUri = "227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter@$imageDigest"

$taskFamilies = @(
    "jsmith-sheetmusic-splitter-toc-discovery",
    "jsmith-sheetmusic-splitter-toc-parser",
    "jsmith-sheetmusic-splitter-page-mapper",
    "jsmith-sheetmusic-splitter-song-verifier",
    "jsmith-sheetmusic-splitter-pdf-splitter",
    "jsmith-sheetmusic-splitter-manifest-generator"
)

Write-Host "Updating task definitions to use new image..." -ForegroundColor Cyan
Write-Host "Image: $imageUri" -ForegroundColor Gray
Write-Host ""

foreach ($family in $taskFamilies) {
    Write-Host "Updating $family..." -ForegroundColor Yellow
    
    # Get current task definition
    $taskDef = aws ecs describe-task-definition --task-definition $family | ConvertFrom-Json
    
    # Update image in container definition
    $taskDef.taskDefinition.containerDefinitions[0].image = $imageUri
    
    # Remove fields that can't be in register-task-definition
    $taskDef.taskDefinition.PSObject.Properties.Remove('taskDefinitionArn')
    $taskDef.taskDefinition.PSObject.Properties.Remove('revision')
    $taskDef.taskDefinition.PSObject.Properties.Remove('status')
    $taskDef.taskDefinition.PSObject.Properties.Remove('requiresAttributes')
    $taskDef.taskDefinition.PSObject.Properties.Remove('compatibilities')
    $taskDef.taskDefinition.PSObject.Properties.Remove('registeredAt')
    $taskDef.taskDefinition.PSObject.Properties.Remove('registeredBy')
    
    # Save to temp file
    $tempFile = "temp_taskdef_$family.json"
    $taskDef.taskDefinition | ConvertTo-Json -Depth 10 | Out-File -FilePath $tempFile -Encoding utf8
    
    # Register new task definition
    aws ecs register-task-definition --cli-input-json "file://$tempFile" | Out-Null
    
    # Cleanup
    Remove-Item $tempFile
    
    Write-Host "  Updated!" -ForegroundColor Green
}

Write-Host ""
Write-Host "All task definitions updated!" -ForegroundColor Green
