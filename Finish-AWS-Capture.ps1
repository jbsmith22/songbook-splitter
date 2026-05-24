<#
.SYNOPSIS
    Phase 2 completion: cleanup duplicates and fill capture gaps.

.DESCRIPTION
    Performs all remaining Phase 2 work in one shot:
      1. Removes the two failed-run timestamp sets (20260523-235921, 20260524-000206)
      2. Captures artifacts bucket inventory (script had wrong name first time)
      3. Captures the 2 Lambda configs that the paginated list-functions call missed
      4. Captures all IAM role policies for the 4 CFN-created roles
      5. Captures all 4 ECS task definitions (including runtime-registered ones)

    All output goes into the existing AWS_Restoration\ folder with the
    20260524-000428 timestamp (same as the authoritative capture).

.NOTES
    Read-only against AWS. No resources are created, modified, or deleted in AWS.
    The only deletions are local files (the duplicate failed-run captures).
#>

[CmdletBinding()]
param(
    [string]$RestoreDir = 'S:\aiwork\songbook-splitter\AWS_Restoration',
    [string]$Region = 'us-east-1',
    [string]$Timestamp = '20260524-000428'
)

$ErrorActionPreference = 'Continue'
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

function Invoke-AwsSilent {
    param([string[]]$AwsArgs)
    $stderrFile = [System.IO.Path]::GetTempFileName()
    try {
        $output = & aws @AwsArgs 2>$stderrFile
        $script:lastAwsExit = $LASTEXITCODE
        return ($output | Out-String)
    } finally {
        Remove-Item $stderrFile -ErrorAction SilentlyContinue
    }
}

function Write-Section($title) {
    Write-Host ""
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host $title -ForegroundColor Cyan
    Write-Host "===============================================================" -ForegroundColor Cyan
}

function Write-Ok($msg)   { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  WARN  $msg" -ForegroundColor Yellow }
function Write-Step($msg) { Write-Host "  -> $msg" -ForegroundColor White }

# ===========================================================================
# Step 1: Cleanup duplicate failed-run files
# ===========================================================================
Write-Section "Step 1: Remove duplicate failed-run output"

$DropTimestamps = @('20260523-235921', '20260524-000206')
$totalRemoved = 0
$bytesRemoved = 0

foreach ($ts in $DropTimestamps) {
    $items = Get-ChildItem -Path $RestoreDir -Recurse -Force | Where-Object { $_.Name -like "*$ts*" }
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            $size = (Get-ChildItem $item.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        } else {
            $size = $item.Length
        }
        if (-not $size) { $size = 0 }
        $bytesRemoved += $size
        $totalRemoved++
        Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
}
Write-Ok "Removed $totalRemoved items, $([math]::Round($bytesRemoved/1MB, 2)) MB"

# ===========================================================================
# Step 2: Artifacts bucket inventory
# ===========================================================================
Write-Section "Step 2: Capture jsmith-jsmith-sheetmusic-splitter-artifacts inventory"

$artifactsBucket = 'jsmith-jsmith-sheetmusic-splitter-artifacts'
$s3InvDir = Join-Path $RestoreDir "s3_inventory_$Timestamp"
if (-not (Test-Path $s3InvDir)) { New-Item -ItemType Directory -Path $s3InvDir -Force | Out-Null }

$invFile = Join-Path $s3InvDir "${artifactsBucket}_inventory.txt"
Write-Step "Listing s3://$artifactsBucket/ ..."

$null = Invoke-AwsSilent @('s3api', 'head-bucket', '--bucket', $artifactsBucket, '--region', $Region)
if ($script:lastAwsExit -ne 0) {
    Write-Warn "Bucket not found (may have been deleted already, that's OK)"
} else {
    & aws s3 ls "s3://$artifactsBucket/" --recursive --human-readable --summarize --region $Region 2>$null > $invFile
    if ($LASTEXITCODE -eq 0 -and (Test-Path $invFile)) {
        $lineCount = (Get-Content $invFile -ErrorAction SilentlyContinue | Measure-Object).Count
        $size = (Get-Item $invFile).Length
        Write-Ok "Captured: $lineCount lines, $size bytes"
    }
    
    # Metadata
    $metaFile = Join-Path $s3InvDir "${artifactsBucket}_metadata.json"
    $loc = Invoke-AwsSilent (@('s3api', 'get-bucket-location', '--bucket', $artifactsBucket, '--region', $Region))
    if ($script:lastAwsExit -ne 0) { $loc = '{}' }
    $vers = Invoke-AwsSilent (@('s3api', 'get-bucket-versioning', '--bucket', $artifactsBucket, '--region', $Region))
    if ($script:lastAwsExit -ne 0) { $vers = '{}' }
    $lifecycle = Invoke-AwsSilent (@('s3api', 'get-bucket-lifecycle-configuration', '--bucket', $artifactsBucket, '--region', $Region))
    if ($script:lastAwsExit -ne 0) { $lifecycle = '{"note":"no lifecycle configuration"}' }
    
    @{ location = $loc; versioning = $vers; lifecycle = $lifecycle } | ConvertTo-Json -Depth 10 | Out-File -FilePath $metaFile -Encoding utf8
    Write-Ok "Metadata captured"
}

# ===========================================================================
# Step 3: Missing Lambda function configs
# ===========================================================================
Write-Section "Step 3: Capture missing Lambda configs (record-start, record-failure)"

$missingLambdas = @('jsmith-sheetmusic-splitter-record-start', 'jsmith-sheetmusic-splitter-record-failure')
foreach ($fn in $missingLambdas) {
    Write-Step "Capturing $fn ..."
    $outFile = Join-Path $RestoreDir "lambda_${fn}_$Timestamp.json"
    $data = Invoke-AwsSilent (@('lambda', 'get-function-configuration', '--function-name', $fn, '--region', $Region))
    if ($script:lastAwsExit -eq 0) {
        $data | Out-File -FilePath $outFile -Encoding utf8
        Write-Ok "$fn"
    } else {
        Write-Warn "Failed to get $fn (may not exist)"
    }
}

# ===========================================================================
# Step 4: IAM role policies (4 roles created by CFN)
# ===========================================================================
Write-Section "Step 4: Capture IAM roles and inline policies"

$roles = @(
    'jsmith-sheetmusic-splitter-ECSTaskExecutionRole-lk6cYO4BePSL',
    'jsmith-sheetmusic-splitter-ECSTaskRole-w6lDb4md62rc',
    'jsmith-sheetmusic-splitter-LambdaExecutionRole-c04M7sd14w1q',
    'jsmith-sheetmusic-splitter-StepFunctionsRole-ORLcHt5KMOi2'
)

$iamDir = Join-Path $RestoreDir "iam_$Timestamp"
if (-not (Test-Path $iamDir)) { New-Item -ItemType Directory -Path $iamDir -Force | Out-Null }

foreach ($r in $roles) {
    Write-Step "Role: $r"
    
    # Role definition (trust policy, basic metadata)
    $roleFile = Join-Path $iamDir "role_$r.json"
    $roleData = Invoke-AwsSilent (@('iam', 'get-role', '--role-name', $r))
    if ($script:lastAwsExit -eq 0) {
        $roleData | Out-File -FilePath $roleFile -Encoding utf8
        
        # Inline policies attached to the role
        $polListData = Invoke-AwsSilent (@('iam', 'list-role-policies', '--role-name', $r))
        if ($script:lastAwsExit -eq 0) {
            $polList = $polListData | ConvertFrom-Json
            foreach ($p in $polList.PolicyNames) {
                $polFile = Join-Path $iamDir "policy_${r}_${p}.json"
                $polData = Invoke-AwsSilent (@('iam', 'get-role-policy', '--role-name', $r, '--policy-name', $p))
                if ($script:lastAwsExit -eq 0) {
                    $polData | Out-File -FilePath $polFile -Encoding utf8
                }
            }
            Write-Ok "  Captured role + $($polList.PolicyNames.Count) inline policies"
        }
        
        # Attached managed policies
        $mpFile = Join-Path $iamDir "managed_policies_$r.json"
        $mpData = Invoke-AwsSilent (@('iam', 'list-attached-role-policies', '--role-name', $r))
        if ($script:lastAwsExit -eq 0) {
            $mpData | Out-File -FilePath $mpFile -Encoding utf8
        }
    } else {
        Write-Warn "  Role not found: $r"
    }
}

# ===========================================================================
# Step 5: ECS task definitions (all 4 families, including runtime-registered)
# ===========================================================================
Write-Section "Step 5: Capture ECS task definitions"

$families = @(
    'jsmith-sheetmusic-splitter-toc-discovery',
    'jsmith-sheetmusic-splitter-toc-parser',
    'jsmith-sheetmusic-splitter-page-analysis',
    'jsmith-sheetmusic-splitter-pdf-splitter'
)

$tdDir = Join-Path $RestoreDir "ecs_task_definitions_$Timestamp"
if (-not (Test-Path $tdDir)) { New-Item -ItemType Directory -Path $tdDir -Force | Out-Null }

$captured = 0
foreach ($f in $families) {
    Write-Step "Task family: $f"
    $tdFile = Join-Path $tdDir "$f.json"
    $tdData = Invoke-AwsSilent (@('ecs', 'describe-task-definition', '--task-definition', $f, '--region', $Region))
    if ($script:lastAwsExit -eq 0) {
        $tdData | Out-File -FilePath $tdFile -Encoding utf8
        $parsed = $tdData | ConvertFrom-Json
        $rev = $parsed.taskDefinition.revision
        $cpu = $parsed.taskDefinition.cpu
        $mem = $parsed.taskDefinition.memory
        Write-Ok "  Revision $rev, CPU $cpu, Memory $mem MB"
        $captured++
    } else {
        Write-Warn "  Not registered (this may be normal for some families)"
    }
}
Write-Ok "Total task definitions captured: $captured of $($families.Count)"

# ===========================================================================
# Final summary
# ===========================================================================
Write-Section "Phase 2 capture follow-ups - complete"

Write-Host ""
Write-Host "Final contents of $RestoreDir :" -ForegroundColor Cyan
Get-ChildItem $RestoreDir -Recurse -File | ForEach-Object {
    $size = if ($_.Length -lt 1KB) { "$($_.Length) B" }
            elseif ($_.Length -lt 1MB) { "$([math]::Round($_.Length/1KB,1)) KB" }
            else { "$([math]::Round($_.Length/1MB,1)) MB" }
    $rel = $_.FullName -replace [regex]::Escape($RestoreDir + '\'), ''
    Write-Host ("  {0,-12} {1}" -f $size, $rel) -ForegroundColor Gray
}

Write-Host ""
Write-Host "Done. Next: commit AWS_Restoration/ to git." -ForegroundColor Green
Write-Host "  cd S:\aiwork\songbook-splitter" -ForegroundColor White
Write-Host "  git add AWS_Restoration/ Capture-AWS-State.ps1 Cleanup-AWS-Restoration-Duplicates.ps1" -ForegroundColor White
Write-Host "  git commit -m 'Phase 2: AWS restoration package captured'" -ForegroundColor White
