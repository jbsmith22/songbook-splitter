<#
.SYNOPSIS
    Phase 4: Tear down AWS resources for songbook-splitter.

.DESCRIPTION
    Corrected version of scripts/aws/cleanup.ps1. Fixes:
    - Uses correct artifacts bucket name (jsmith-jsmith-sheetmusic-splitter-artifacts)
    - Handles bucket versioning (deletes version markers, not just current)
    - Uses Invoke-AwsSilent helper to avoid PowerShell native-command stderr issues
    - Doesn't halt on first warning (uses ErrorActionPreference = Continue)
    - Confirms with user before destruction
    - Provides recovery hint if anything fails

.NOTES
    PREREQUISITE: AWS_Restoration package must be committed to git first.
    Verify with: git log -1 --name-only AWS_Restoration/
#>

[CmdletBinding()]
param(
    [string]$Region = 'us-east-1',
    [string]$StackName = 'jsmith-sheetmusic-splitter'
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

function Write-Ok($msg)   { Write-Host "  OK   $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  WARN $msg" -ForegroundColor Yellow }
function Write-Step($msg) { Write-Host "  -> $msg" -ForegroundColor White }
function Write-Err($msg)  { Write-Host "  ERR  $msg" -ForegroundColor Red }

# ===========================================================================
# Big red warning
# ===========================================================================
Write-Host ""
Write-Host "================================================================" -ForegroundColor Red
Write-Host " AWS TEARDOWN  -  PERMANENT DESTRUCTION" -ForegroundColor Red
Write-Host "================================================================" -ForegroundColor Red
Write-Host ""
Write-Host "This will permanently delete:" -ForegroundColor Yellow
Write-Host "  - CloudFormation stack:  $StackName"
Write-Host "  - S3 buckets:"
Write-Host "      jsmith-input  (1,051 files - also on local + Drive)"
Write-Host "      jsmith-output (49,913 files - also on local + Drive)"
Write-Host "      jsmith-jsmith-sheetmusic-splitter-artifacts (empty)"
Write-Host "  - DynamoDB tables:  jsmith-processing-ledger, jsmith-pipeline-ledger"
Write-Host "  - ECR repository:  $StackName (117 images)"
Write-Host "  - Lambda functions, ECS tasks, Step Functions, CloudWatch alarms"
Write-Host "  - IAM roles created by the stack"
Write-Host ""
Write-Host "RECOVERY:  AWS_Restoration\ package on disk + git contains everything" -ForegroundColor Cyan
Write-Host "          needed to rebuild via scripts\aws\deploy*.ps1." -ForegroundColor Cyan
Write-Host ""

$confirmation = Read-Host "Type 'DELETE' to confirm permanent destruction"
if ($confirmation -ne 'DELETE') {
    Write-Host ""
    Write-Host "Teardown cancelled. No changes made." -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "Beginning teardown..." -ForegroundColor Red

# ===========================================================================
# Step 0: Verify auth
# ===========================================================================
Write-Section "Step 0: Verify AWS credentials"
$identity = Invoke-AwsSilent (@('sts', 'get-caller-identity', '--region', $Region)) | ConvertFrom-Json
if ($script:lastAwsExit -ne 0 -or -not $identity) {
    Write-Err "AWS CLI not authenticated. Run 'aws sso login' first."
    exit 1
}
Write-Ok "Authenticated as: $($identity.Arn)"

# ===========================================================================
# Step 1: Empty all S3 buckets (including versioned objects)
# ===========================================================================
Write-Section "Step 1: Empty S3 buckets"

$buckets = @(
    'jsmith-input',
    'jsmith-output',
    'jsmith-jsmith-sheetmusic-splitter-artifacts'
)

foreach ($bucket in $buckets) {
    Write-Step "Bucket: $bucket"
    
    # Check existence
    $null = Invoke-AwsSilent (@('s3api', 'head-bucket', '--bucket', $bucket, '--region', $Region))
    if ($script:lastAwsExit -ne 0) {
        Write-Warn "  Bucket does not exist (may already be deleted)"
        continue
    }
    
    # Delete all current-version objects
    Write-Step "  Removing current objects..."
    $null = Invoke-AwsSilent (@('s3', 'rm', "s3://$bucket", '--recursive', '--region', $Region))
    if ($script:lastAwsExit -eq 0) { Write-Ok "  Current objects removed" } else { Write-Warn "  rm returned non-zero (may have been empty)" }
    
    # Check if versioning is enabled - if so, delete all versions and delete markers
    $versioning = Invoke-AwsSilent (@('s3api', 'get-bucket-versioning', '--bucket', $bucket, '--region', $Region)) | ConvertFrom-Json
    if ($versioning.Status -eq 'Enabled' -or $versioning.Status -eq 'Suspended') {
        Write-Step "  Versioning detected - removing version markers..."
        
        # Get all versions
        $versionsJson = Invoke-AwsSilent (@('s3api', 'list-object-versions', '--bucket', $bucket, '--region', $Region, '--output', 'json'))
        if ($script:lastAwsExit -eq 0 -and $versionsJson) {
            $versions = $versionsJson | ConvertFrom-Json
            
            # Build deletion batch
            $toDelete = @()
            if ($versions.Versions) {
                foreach ($v in $versions.Versions) {
                    $toDelete += @{ Key = $v.Key; VersionId = $v.VersionId }
                }
            }
            if ($versions.DeleteMarkers) {
                foreach ($d in $versions.DeleteMarkers) {
                    $toDelete += @{ Key = $d.Key; VersionId = $d.VersionId }
                }
            }
            
            if ($toDelete.Count -gt 0) {
                Write-Step "    Found $($toDelete.Count) version markers to delete"
                
                # Delete in batches of 1000 (S3 API limit)
                for ($i = 0; $i -lt $toDelete.Count; $i += 1000) {
                    $batch = $toDelete[$i..([Math]::Min($i + 999, $toDelete.Count - 1))]
                    $deleteSpec = @{
                        Objects = $batch
                        Quiet = $true
                    } | ConvertTo-Json -Depth 5 -Compress
                    
                    $tmpFile = [System.IO.Path]::GetTempFileName()
                    try {
                        $deleteSpec | Out-File -FilePath $tmpFile -Encoding utf8 -NoNewline
                        $null = Invoke-AwsSilent (@('s3api', 'delete-objects', '--bucket', $bucket, '--delete', "file://$tmpFile", '--region', $Region))
                    } finally {
                        Remove-Item $tmpFile -ErrorAction SilentlyContinue
                    }
                }
                Write-Ok "  All $($toDelete.Count) version markers removed"
            } else {
                Write-Ok "  No version markers to remove"
            }
        }
    }
}

# ===========================================================================
# Step 2: Delete the CloudFormation stack
# ===========================================================================
Write-Section "Step 2: Delete CloudFormation stack"

Write-Step "Initiating stack delete: $StackName"
$null = Invoke-AwsSilent (@('cloudformation', 'delete-stack', '--stack-name', $StackName, '--region', $Region))
if ($script:lastAwsExit -ne 0) {
    Write-Err "Failed to initiate stack deletion. Stack may not exist."
    Write-Host ""
    Write-Host "If you see this and the stack exists, check IAM permissions or " -ForegroundColor Yellow
    Write-Host "delete via console: https://console.aws.amazon.com/cloudformation/" -ForegroundColor Yellow
    exit 1
}

Write-Ok "Stack deletion initiated"
Write-Step "Waiting for completion (typically 5-10 minutes)..."
Write-Host "  (use Ctrl+C to interrupt - the deletion continues in AWS regardless)" -ForegroundColor Gray

$null = Invoke-AwsSilent (@('cloudformation', 'wait', 'stack-delete-complete', '--stack-name', $StackName, '--region', $Region))
if ($script:lastAwsExit -eq 0) {
    Write-Ok "Stack deleted successfully"
} else {
    Write-Warn "Stack deletion may have failed or timed out"
    Write-Warn "Check status: aws cloudformation describe-stacks --stack-name $StackName --region $Region"
    Write-Warn "Or visit console: https://console.aws.amazon.com/cloudformation/"
}

# ===========================================================================
# Step 3: Delete ECR repository
# ===========================================================================
Write-Section "Step 3: Delete ECR repository"

Write-Step "Deleting repository: $StackName (with --force, 117 images go too)"
$null = Invoke-AwsSilent (@('ecr', 'delete-repository', '--repository-name', $StackName, '--force', '--region', $Region))
if ($script:lastAwsExit -eq 0) {
    Write-Ok "ECR repository deleted"
} else {
    Write-Warn "Repository deletion failed or repo already gone"
}

# ===========================================================================
# Step 4: Delete the legacy V2 DynamoDB table (not in current CFN stack)
# ===========================================================================
Write-Section "Step 4: Delete legacy V2 DynamoDB table"

Write-Step "Checking for jsmith-pipeline-ledger (V2 legacy, not in current CFN stack)..."
$null = Invoke-AwsSilent (@('dynamodb', 'describe-table', '--table-name', 'jsmith-pipeline-ledger', '--region', $Region))
if ($script:lastAwsExit -eq 0) {
    Write-Step "Deleting table..."
    $null = Invoke-AwsSilent (@('dynamodb', 'delete-table', '--table-name', 'jsmith-pipeline-ledger', '--region', $Region))
    if ($script:lastAwsExit -eq 0) {
        Write-Ok "jsmith-pipeline-ledger delete initiated"
    } else {
        Write-Warn "Failed to delete jsmith-pipeline-ledger"
    }
} else {
    Write-Ok "jsmith-pipeline-ledger not present (already deleted or never created)"
}

# ===========================================================================
# Step 5: Verify everything is gone
# ===========================================================================
Write-Section "Step 5: Verify teardown"

$leftovers = @()

# Stack
$null = Invoke-AwsSilent (@('cloudformation', 'describe-stacks', '--stack-name', $StackName, '--region', $Region))
if ($script:lastAwsExit -eq 0) { $leftovers += "CloudFormation stack: $StackName" }

# Buckets
foreach ($bucket in $buckets) {
    $null = Invoke-AwsSilent (@('s3api', 'head-bucket', '--bucket', $bucket, '--region', $Region))
    if ($script:lastAwsExit -eq 0) { $leftovers += "S3 bucket: $bucket" }
}

# DynamoDB
foreach ($table in @('jsmith-processing-ledger', 'jsmith-pipeline-ledger')) {
    $null = Invoke-AwsSilent (@('dynamodb', 'describe-table', '--table-name', $table, '--region', $Region))
    if ($script:lastAwsExit -eq 0) { $leftovers += "DynamoDB table: $table" }
}

# ECR
$null = Invoke-AwsSilent (@('ecr', 'describe-repositories', '--repository-names', $StackName, '--region', $Region))
if ($script:lastAwsExit -eq 0) { $leftovers += "ECR repository: $StackName" }

Write-Host ""
if ($leftovers.Count -eq 0) {
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host " TEARDOWN COMPLETE  -  ALL RESOURCES DELETED" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "No ongoing AWS charges will occur for this project." -ForegroundColor Green
    Write-Host ""
    Write-Host "To restore in the future:" -ForegroundColor Cyan
    Write-Host "  1. aws sso login" -ForegroundColor White
    Write-Host "  2. cd S:\aiwork\songbook-splitter" -ForegroundColor White
    Write-Host "  3. .\scripts\aws\deploy-docker.ps1" -ForegroundColor White
    Write-Host "  4. .\scripts\aws\deploy.ps1" -ForegroundColor White
    Write-Host "  5. .\scripts\aws\deploy-lambda.ps1" -ForegroundColor White
    Write-Host "  6. .\scripts\aws\register-all-tasks.ps1" -ForegroundColor White
    Write-Host "  7. python scripts\restore_dynamodb.py --backup-file AWS_Restoration\dynamodb_backup_jsmith-processing-ledger_20260524-000428.json --table jsmith-processing-ledger" -ForegroundColor White
    Write-Host ""
    Write-Host "See AWS_Restoration\RESTORATION_PROCEDURE.md for full details." -ForegroundColor Cyan
} else {
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host " TEARDOWN PARTIAL  -  $($leftovers.Count) ITEMS REMAIN" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host ""
    foreach ($l in $leftovers) {
        Write-Host "  - $l" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Check the CloudFormation console for details:" -ForegroundColor Yellow
    Write-Host "  https://console.aws.amazon.com/cloudformation/" -ForegroundColor White
    Write-Host ""
    Write-Host "Common causes:" -ForegroundColor Yellow
    Write-Host "  - S3 bucket has objects with retention policies" -ForegroundColor Gray
    Write-Host "  - DynamoDB table has deletion protection enabled" -ForegroundColor Gray
    Write-Host "  - Stack delete is still in progress (DELETE_IN_PROGRESS)" -ForegroundColor Gray
}

Write-Host ""
