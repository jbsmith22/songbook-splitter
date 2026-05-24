<#
.SYNOPSIS
    Phase 2: Build the AWS restoration package.
    Captures live state of all AWS resources before teardown so the project can
    be rebuilt in the future.

.DESCRIPTION
    The CloudFormation template, Step Functions JSON, deployment scripts, and
    Docker image build instructions already exist in source control. What this
    script captures is the *current runtime state* of the deployed system:

    - DynamoDB ledger contents (current snapshot, not the Feb 2026 backup)
    - CloudFormation stack outputs (actual ARNs, bucket names with account-specific suffixes)
    - ECR image manifest (current tags, digests, when last pushed)
    - Step Functions recent execution history (5 successful runs for reference)
    - S3 inventory diff (files in S3 not present locally)
    - CloudWatch log group list

    Output goes to: S:\aiwork\songbook-splitter\AWS_Restoration\

    This is READ-ONLY against AWS. No resources are created, modified, or deleted.
    It only reads the current state and saves it locally.

.NOTES
    Requires AWS CLI configured with credentials for account 227027150061.
    Verify: aws sts get-caller-identity
    
    If you get auth errors, run: aws sso login --profile <your-profile>
    Or set AWS_PROFILE environment variable before running this script.
#>

[CmdletBinding()]
param(
    [string]$AwsProfile = '',
    [string]$Region = 'us-east-1',
    [string]$AccountId = '227027150061',
    [string]$StackName = 'jsmith-sheetmusic-splitter',
    [string]$ProjectRoot = 'S:\aiwork\songbook-splitter'
)

$ErrorActionPreference = 'Continue'
# PS 7+: don't treat aws.exe stderr as terminating errors
if ($PSVersionTable.PSVersion.Major -ge 7) {
    $PSNativeCommandUseErrorActionPreference = $false
}

# Helper: invoke aws CLI capturing stdout, swallowing stderr completely.
# Returns the stdout string, sets $script:lastAwsExit to the exit code.
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

# Resolve restoration directory
$RestoreDir = Join-Path $ProjectRoot 'AWS_Restoration'
if (-not (Test-Path $RestoreDir)) {
    New-Item -ItemType Directory -Path $RestoreDir -Force | Out-Null
}

# AWS CLI prefix
$awsArgs = @('--region', $Region)
if ($AwsProfile) { $awsArgs += @('--profile', $AwsProfile) }

function Invoke-AwsCli {
    param([string[]]$Arguments)
    $allArgs = $Arguments + $awsArgs
    & aws @allArgs 2>&1
    return $LASTEXITCODE
}

function Write-Section($title) {
    Write-Host ""
    Write-Host "===============================================================" -ForegroundColor Cyan
    Write-Host $title -ForegroundColor Cyan
    Write-Host "===============================================================" -ForegroundColor Cyan
}

function Write-Step($msg)    { Write-Host "  -> $msg" -ForegroundColor White }
function Write-Ok($msg)      { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)    { Write-Host "  WARN  $msg" -ForegroundColor Yellow }
function Write-Err($msg)     { Write-Host "  ERROR  $msg" -ForegroundColor Red }

$ts = Get-Date -Format 'yyyyMMdd-HHmmss'

Write-Section "AWS Restoration Package  -  capture live state"
Write-Host "Account: $AccountId" -ForegroundColor Gray
Write-Host "Region:  $Region" -ForegroundColor Gray
Write-Host "Stack:   $StackName" -ForegroundColor Gray
Write-Host "Output:  $RestoreDir" -ForegroundColor Gray
Write-Host "Timestamp: $ts" -ForegroundColor Gray

# ===========================================================================
# Step 0: Verify AWS CLI auth
# ===========================================================================
Write-Section "Step 0: Verify AWS credentials"
Write-Step "Checking caller identity..."

$identity = & aws sts get-caller-identity @awsArgs 2>$null | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or -not $identity) {
    Write-Err "AWS CLI not authenticated. Run 'aws sso login' or set AWS_PROFILE."
    Write-Host ""
    Write-Host "Test with: aws sts get-caller-identity --region $Region" -ForegroundColor Yellow
    exit 1
}

Write-Ok "Authenticated as: $($identity.Arn)"
if ($identity.Account -ne $AccountId) {
    Write-Warn "Account mismatch! Expected $AccountId, got $($identity.Account)"
    $confirm = Read-Host "Continue anyway? (y/n)"
    if ($confirm -ne 'y') { exit 1 }
}

# ===========================================================================
# Step 1: Fresh DynamoDB ledger backup
# ===========================================================================
Write-Section "Step 1: DynamoDB ledger snapshot"

$tables = @('jsmith-processing-ledger', 'jsmith-pipeline-ledger')
foreach ($table in $tables) {
    Write-Step "Checking table: $table"
    $exists = & aws dynamodb describe-table --table-name $table @awsArgs 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Table not found: $table (skipping)"
        continue
    }
    
    $outFile = Join-Path $RestoreDir "dynamodb_backup_${table}_${ts}.json"
    Write-Step "Exporting to: $(Split-Path $outFile -Leaf)"
    
    & aws dynamodb scan --table-name $table --output json @awsArgs > $outFile 2>$null
    if ($LASTEXITCODE -eq 0 -and (Test-Path $outFile) -and (Get-Item $outFile).Length -gt 0) {
        $content = Get-Content $outFile -Raw | ConvertFrom-Json
        Write-Ok "Backed up $($content.Count) items, $((Get-Item $outFile).Length) bytes"
    } else {
        Write-Err "Failed to backup table $table"
    }
}

# ===========================================================================
# Step 2: CloudFormation stack outputs
# ===========================================================================
Write-Section "Step 2: CloudFormation stack outputs"
Write-Step "Describing stack: $StackName"

$cfnFile = Join-Path $RestoreDir "cfn_stack_outputs_${ts}.json"
$stackData = & aws cloudformation describe-stacks --stack-name $StackName @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $stackData | Out-File -FilePath $cfnFile -Encoding utf8
    $parsed = $stackData | ConvertFrom-Json
    $outputs = $parsed.Stacks[0].Outputs
    Write-Ok "Stack found, $($outputs.Count) outputs captured"
    Write-Host ""
    Write-Host "  Stack outputs:" -ForegroundColor Gray
    foreach ($o in $outputs) {
        Write-Host "    $($o.OutputKey) = $($o.OutputValue)" -ForegroundColor Gray
    }
} else {
    Write-Warn "Stack not found (maybe already torn down?)"
}

# Stack resources detail
Write-Step "Capturing stack resources..."
$resFile = Join-Path $RestoreDir "cfn_stack_resources_${ts}.json"
$resources = & aws cloudformation list-stack-resources --stack-name $StackName @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $resources | Out-File -FilePath $resFile -Encoding utf8
    $parsed = $resources | ConvertFrom-Json
    Write-Ok "Captured $($parsed.StackResourceSummaries.Count) stack resources"
} else {
    Write-Warn "Could not list stack resources"
}

# ===========================================================================
# Step 3: ECR image manifest
# ===========================================================================
Write-Section "Step 3: ECR image manifest"

$ecrFile = Join-Path $RestoreDir "ecr_images_${ts}.json"
Write-Step "Listing images in repository: $StackName"
$ecrData = & aws ecr describe-images --repository-name $StackName @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $ecrData | Out-File -FilePath $ecrFile -Encoding utf8
    $parsed = $ecrData | ConvertFrom-Json
    Write-Ok "Captured $($parsed.imageDetails.Count) image versions"
    Write-Host ""
    Write-Host "  Recent images:" -ForegroundColor Gray
    $parsed.imageDetails | Sort-Object imagePushedAt -Descending | Select-Object -First 5 | ForEach-Object {
        $tags = if ($_.imageTags) { $_.imageTags -join ',' } else { '<untagged>' }
        Write-Host "    $($_.imagePushedAt)  $tags  ($([math]::Round($_.imageSizeInBytes/1MB,1)) MB)" -ForegroundColor Gray
    }
} else {
    Write-Warn "ECR repository not found or no images"
}

# ===========================================================================
# Step 4: Step Functions execution history sample
# ===========================================================================
Write-Section "Step 4: Step Functions execution history"

$smArn = "arn:aws:states:${Region}:${AccountId}:stateMachine:${StackName}-pipeline"
Write-Step "State machine: $smArn"

$execFile = Join-Path $RestoreDir "stepfunctions_executions_${ts}.json"
$execData = & aws stepfunctions list-executions --state-machine-arn $smArn --max-items 50 @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $execData | Out-File -FilePath $execFile -Encoding utf8
    $parsed = $execData | ConvertFrom-Json
    Write-Ok "Captured $($parsed.executions.Count) recent executions"
    
    # Save detailed history for 5 successful executions
    $successful = $parsed.executions | Where-Object { $_.status -eq 'SUCCEEDED' } | Select-Object -First 5
    Write-Step "Saving detailed history for $($successful.Count) successful executions..."
    
    $detailDir = Join-Path $RestoreDir "stepfunctions_execution_details_${ts}"
    New-Item -ItemType Directory -Path $detailDir -Force | Out-Null
    
    foreach ($e in $successful) {
        $execId = ($e.executionArn -split ':')[-1]
        $detailFile = Join-Path $detailDir "exec_${execId}.json"
        & aws stepfunctions describe-execution --execution-arn $e.executionArn @awsArgs > $detailFile 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Ok "  $execId"
        }
    }
} else {
    Write-Warn "State machine not found or no executions"
}

# ===========================================================================
# Step 5: S3 inventory
# ===========================================================================
Write-Section "Step 5: S3 bucket inventory"

$buckets = @('jsmith-input', 'jsmith-output', 'jsmith-sheetmusic-splitter-artifacts')
$s3InvDir = Join-Path $RestoreDir "s3_inventory_${ts}"
New-Item -ItemType Directory -Path $s3InvDir -Force | Out-Null

foreach ($bucket in $buckets) {
    Write-Step "Listing s3://$bucket/ ..."
    $exists = & aws s3api head-bucket --bucket $bucket @awsArgs 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Bucket not found: $bucket"
        continue
    }
    
    $invFile = Join-Path $s3InvDir "${bucket}_inventory.txt"
    & aws s3 ls "s3://$bucket/" --recursive --human-readable --summarize @awsArgs > $invFile 2>$null
    if ($LASTEXITCODE -eq 0) {
        $lineCount = (Get-Content $invFile -ErrorAction SilentlyContinue | Measure-Object).Count
        $size = (Get-Item $invFile).Length
        Write-Ok "  Inventory captured: $lineCount lines, $size bytes"
        
        # Also get bucket metadata - use Invoke-AwsSilent to fully isolate stderr
        # (NoSuchLifecycleConfiguration is normal when no lifecycle is set)
        $metaFile = Join-Path $s3InvDir "${bucket}_metadata.json"
        
        $loc = Invoke-AwsSilent (@('s3api', 'get-bucket-location', '--bucket', $bucket) + $awsArgs)
        if ($script:lastAwsExit -ne 0) { $loc = '{}' }
        
        $vers = Invoke-AwsSilent (@('s3api', 'get-bucket-versioning', '--bucket', $bucket) + $awsArgs)
        if ($script:lastAwsExit -ne 0) { $vers = '{}' }
        
        $lifecycle = Invoke-AwsSilent (@('s3api', 'get-bucket-lifecycle-configuration', '--bucket', $bucket) + $awsArgs)
        if ($script:lastAwsExit -ne 0) { $lifecycle = '{"note":"no lifecycle configuration"}' }
        
        $meta = @{
            location = $loc
            versioning = $vers
            lifecycle = $lifecycle
        }
        $meta | ConvertTo-Json -Depth 10 | Out-File -FilePath $metaFile -Encoding utf8
        Write-Ok "  Metadata captured"
    } else {
        Write-Warn "  Could not list bucket"
    }
}

# ===========================================================================
# Step 6: Lambda function inventory
# ===========================================================================
Write-Section "Step 6: Lambda function details"

$lambdaFile = Join-Path $RestoreDir "lambda_functions_${ts}.json"
Write-Step "Listing Lambda functions matching $StackName-*"
$lambdas = & aws lambda list-functions --max-items 100 @awsArgs 2>$null | ConvertFrom-Json
if ($lambdas -and $lambdas.Functions) {
    $matched = $lambdas.Functions | Where-Object { $_.FunctionName -like "*$StackName*" -or $_.FunctionName -like "jsmith-*" }
    if ($matched) {
        $matched | ConvertTo-Json -Depth 10 | Out-File -FilePath $lambdaFile -Encoding utf8
        Write-Ok "Captured $($matched.Count) Lambda functions"
        foreach ($l in $matched) {
            Write-Host "    $($l.FunctionName)  ($($l.Runtime), $($l.MemorySize)MB)" -ForegroundColor Gray
        }
    } else {
        Write-Warn "No matching Lambda functions"
    }
}

# ===========================================================================
# Step 7: ECS cluster + task definitions
# ===========================================================================
Write-Section "Step 7: ECS cluster and task definitions"

$ecsClusterName = "$StackName-cluster"
Write-Step "Describing cluster: $ecsClusterName"
$ecsFile = Join-Path $RestoreDir "ecs_cluster_${ts}.json"
$ecsData = & aws ecs describe-clusters --clusters $ecsClusterName @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $ecsData | Out-File -FilePath $ecsFile -Encoding utf8
    Write-Ok "Cluster captured"
}

Write-Step "Listing task definitions..."
$taskdefList = & aws ecs list-task-definitions --family-prefix $StackName @awsArgs 2>$null | ConvertFrom-Json
if ($taskdefList -and $taskdefList.taskDefinitionArns) {
    $taskdefDir = Join-Path $RestoreDir "ecs_task_definitions_${ts}"
    New-Item -ItemType Directory -Path $taskdefDir -Force | Out-Null
    
    foreach ($arn in $taskdefList.taskDefinitionArns) {
        $name = ($arn -split '/')[-1] -replace ':', '_'
        $tdFile = Join-Path $taskdefDir "${name}.json"
        & aws ecs describe-task-definition --task-definition $arn @awsArgs > $tdFile 2>$null
    }
    Write-Ok "Captured $($taskdefList.taskDefinitionArns.Count) task definitions"
}

# ===========================================================================
# Step 8: CloudWatch log group inventory
# ===========================================================================
Write-Section "Step 8: CloudWatch log groups"

$logsFile = Join-Path $RestoreDir "cloudwatch_loggroups_${ts}.json"
Write-Step "Listing log groups matching $StackName"
$logsData = & aws logs describe-log-groups --log-group-name-prefix "/aws/" --max-items 100 @awsArgs 2>$null
if ($LASTEXITCODE -eq 0) {
    $parsed = $logsData | ConvertFrom-Json
    $matched = $parsed.logGroups | Where-Object { $_.logGroupName -like "*$StackName*" -or $_.logGroupName -like "*jsmith*" }
    if ($matched) {
        $matched | ConvertTo-Json -Depth 10 | Out-File -FilePath $logsFile -Encoding utf8
        Write-Ok "Captured $($matched.Count) log groups"
        foreach ($lg in $matched) {
            $size = if ($lg.storedBytes) { [math]::Round($lg.storedBytes/1MB,1) } else { 0 }
            Write-Host "    $($lg.logGroupName)  ($size MB)" -ForegroundColor Gray
        }
    } else {
        Write-Warn "No matching log groups"
    }
}

# ===========================================================================
# Step 9: AWS account-level info we may need
# ===========================================================================
Write-Section "Step 9: Account-level resources"

# VPC and subnet info (used by deploy.ps1  -  need these for restoration)
$vpcFile = Join-Path $RestoreDir "vpc_info_${ts}.json"
Write-Step "Capturing VPC info"
& aws ec2 describe-vpcs @awsArgs > $vpcFile 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "VPCs captured" }

$subnetFile = Join-Path $RestoreDir "subnets_${ts}.json"
Write-Step "Capturing subnet info"
& aws ec2 describe-subnets @awsArgs > $subnetFile 2>$null
if ($LASTEXITCODE -eq 0) { Write-Ok "Subnets captured" }

# IAM roles created by the stack
$iamFile = Join-Path $RestoreDir "iam_roles_${ts}.json"
Write-Step "Capturing IAM roles"
$roles = & aws iam list-roles --max-items 200 @awsArgs 2>$null | ConvertFrom-Json
if ($roles -and $roles.Roles) {
    $matched = $roles.Roles | Where-Object { $_.RoleName -like "*$StackName*" -or $_.RoleName -like "*jsmith*" }
    if ($matched) {
        $matched | ConvertTo-Json -Depth 10 | Out-File -FilePath $iamFile -Encoding utf8
        Write-Ok "Captured $($matched.Count) IAM roles"
    }
}

# ===========================================================================
# Step 10: Write the AWS_RESOURCES.md and RESTORATION_PROCEDURE.md
# ===========================================================================
Write-Section "Step 10: Generate restoration documentation"

$resourcesMd = @"
# AWS Resources Inventory

Generated: $ts
Account: $AccountId
Region: $Region

## Resource Naming Conventions

All resources are prefixed with ``jsmith-`` or ``$StackName-``:

| Resource Type | Name | Purpose |
|---|---|---|
| CloudFormation Stack | $StackName | Top-level container for all infrastructure |
| S3 Bucket | jsmith-input | Source PDFs uploaded for processing |
| S3 Bucket | jsmith-output | Split songs and processed artifacts |
| S3 Bucket | jsmith-sheetmusic-splitter-artifacts | Pipeline JSON artifacts (TOC, page analysis, etc.) |
| DynamoDB Table | jsmith-processing-ledger | Per-book processing status (this is the v3 production table) |
| DynamoDB Table | jsmith-pipeline-ledger | Historical pipeline runs (V2 era  -  may be empty) |
| ECR Repository | $StackName | Docker container for ECS tasks |
| ECS Cluster | $StackName-cluster | Fargate cluster running pipeline tasks |
| Step Functions State Machine | $StackName-pipeline | Orchestrates per-book processing flow |
| SNS Topic | $StackName-alarms | Alarm notifications |
| Lambda Functions | $StackName-* | ingest-service, check-processed, record-start, record-success, record-failure, record-manual-review |
| CloudWatch Log Group | /aws/ecs/$StackName | ECS task logs |

## AWS Services Used

- **S3**  -  file storage (input, output, artifacts)
- **DynamoDB**  -  processing ledger (book status, per-step metadata)
- **Step Functions**  -  pipeline orchestration
- **ECS Fargate**  -  containerized tasks for TOC discovery, page analysis, PDF splitting
- **Lambda**  -  lightweight handlers (DynamoDB updates, ingest, decision points)
- **Bedrock**  -  Claude 3.5 Sonnet (model ID ``anthropic.claude-3-5-sonnet-20241022-v2:0``) for vision-based page classification
- **Textract**  -  OCR for TOC discovery from page images
- **CloudWatch**  -  logs, metrics, alarms
- **SNS**  -  alarm notifications
- **EventBridge**  -  scheduled triggers
- **ECR**  -  Docker image registry
- **VPC + Security Groups**  -  network isolation for ECS tasks
- **IAM**  -  roles for ECS, Lambda, Step Functions

## Pipeline Cost Profile (Historical)

- Original 342-book V3 run: ~``\$154`` total cost
- Per-book cost: ~``\$0.45`` (varies by book size  -  Bedrock vision calls are the biggest factor)
- Cost breakdown (approximate):
  - Bedrock vision (~85%): page analysis + TOC parsing
  - ECS Fargate (~10%): PDF rendering, splitting, page extraction
  - Textract (~3%): TOC OCR
  - S3 storage + transfer (~1%): minimal
  - Lambda + Step Functions (~1%): control plane

## VPC and Network

See ``vpc_info_${ts}.json`` and ``subnets_${ts}.json`` for VPC ID, subnet IDs, and security group details used by ECS tasks.

The deploy.ps1 script references hardcoded VPC ``vpc-4c5f5735`` and subnet ``subnet-0f6ba7ae50933273e``. These are the defaults at restoration time. If the AWS account VPC topology has changed when restoring, update ``scripts/aws/deploy.ps1`` to point at the current VPC/subnet.

## IAM Roles

Roles automatically created by the CloudFormation stack:

- ECSTaskExecutionRole  -  pulls container images, writes logs
- ECSTaskRole  -  accesses S3, DynamoDB, Textract, Bedrock from inside containers
- LambdaExecutionRole  -  Lambda execution + S3 + DynamoDB + Step Functions invoke
- StepFunctionsRole  -  invokes Lambda, runs ECS tasks, passes IAM roles

Full role definitions are in ``iam_roles_${ts}.json``.

## Files in this AWS_Restoration folder

- ``AWS_RESOURCES.md``  -  this file
- ``RESTORATION_PROCEDURE.md``  -  step-by-step rebuild guide
- ``dynamodb_backup_jsmith-processing-ledger_${ts}.json``  -  current v3 ledger (this is what to restore)
- ``dynamodb_backup_jsmith-pipeline-ledger_${ts}.json``  -  V2 legacy table (may be empty)
- ``dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json``  -  pre-existing snapshot (older, kept as belt-and-suspenders)
- ``cfn_stack_outputs_${ts}.json``  -  CloudFormation stack outputs (ARNs, bucket names)
- ``cfn_stack_resources_${ts}.json``  -  list of all resources created by the CFN stack
- ``ecr_images_${ts}.json``  -  Docker image versions and tags
- ``stepfunctions_executions_${ts}.json``  -  recent execution history
- ``stepfunctions_execution_details_${ts}/``  -  detailed Step Functions logs for 5 successful runs
- ``s3_inventory_${ts}/``  -  file lists for each S3 bucket
- ``lambda_functions_${ts}.json``  -  Lambda function configurations
- ``ecs_cluster_${ts}.json``  -  ECS cluster details
- ``ecs_task_definitions_${ts}/``  -  all ECS task definition JSONs
- ``cloudwatch_loggroups_${ts}.json``  -  CloudWatch log group inventory
- ``vpc_info_${ts}.json`` + ``subnets_${ts}.json``  -  network topology
- ``iam_roles_${ts}.json``  -  IAM role definitions

Plus from the project repo (NOT in this folder, but referenced by RESTORATION_PROCEDURE.md):

- ``../infra/cloudformation_template.yaml``  -  the canonical infrastructure definition
- ``../infra/step_functions_complete.json``  -  Step Functions state machine definition
- ``../scripts/aws/deploy.ps1``  -  main deployment script
- ``../scripts/aws/deploy-docker.ps1``  -  Docker image build and push
- ``../scripts/aws/deploy-lambda.ps1``  -  Lambda function code deployment
- ``../scripts/aws/register-all-tasks.ps1``  -  ECS task definition registration
- ``../scripts/aws/cleanup.ps1``  -  full teardown script (NOT to be run during restoration)
- ``../Dockerfile``  -  container image build definition
- ``../requirements.txt``  -  Python dependencies
"@

$resourcesMdFile = Join-Path $RestoreDir 'AWS_RESOURCES.md'
$resourcesMd | Out-File -FilePath $resourcesMdFile -Encoding utf8
Write-Ok "Wrote AWS_RESOURCES.md"

$procedureMd = @"
# AWS Restoration Procedure

This document describes how to rebuild the AWS-side of the songbook-splitter project after teardown.

**Prerequisites**:
- AWS account ``$AccountId`` (or any AWS account, with config adjustments)
- AWS CLI installed and configured
- Docker Desktop installed (for image build)
- PowerShell 7+ (Windows) or PowerShell Core (other platforms)
- Python 3.12+ with packages in ``requirements.txt``

## Cost expectations

- Idle: ~``\$0.50/month`` (S3 storage of any preserved content, DynamoDB on-demand baseline)
- Processing run: ~``\$0.45 per book`` (Bedrock vision-heavy)
- A full 342-book reprocessing run will cost roughly the same as the original (``~\$154``).

If you want to keep AWS storage costs to zero while paused:
1. Empty all S3 buckets before final teardown
2. Delete the CloudFormation stack
3. (Optional) Delete CloudWatch log groups manually if they have content

## Restoration in 8 steps

### Step 1  -  Verify AWS account access

```powershell
aws sts get-caller-identity --region $Region
```

Confirm the Account field matches ``$AccountId`` (or your target account if different).

If using a different account:
- Edit ``scripts/aws/deploy.ps1`` and update the ECR registry URL ``CONTAINER_IMAGE``
- Edit ``infra/cloudformation_template.yaml`` and update default S3 bucket names (must be globally unique)
- Update VPC/subnet IDs in ``deploy.ps1`` to match the target account's network

### Step 2  -  Create the ECR repository

```powershell
aws ecr create-repository ``
    --repository-name $StackName ``
    --region $Region ``
    --image-scanning-configuration scanOnPush=true
```

### Step 3  -  Build and push the Docker container

```powershell
cd $ProjectRoot
./scripts/aws/deploy-docker.ps1
```

This builds the image from the Dockerfile, tags it with the account-specific ECR URL, and pushes it to ECR.

### Step 4  -  Deploy the CloudFormation stack

```powershell
./scripts/aws/deploy.ps1
```

This creates:
- 3 S3 buckets (input, output, artifacts)
- 1 DynamoDB table (jsmith-processing-ledger)
- 1 ECS Fargate cluster
- 6 Lambda functions (placeholder code at this point  -  Step 5 deploys real code)
- 1 Step Functions state machine
- IAM roles, CloudWatch alarms, SNS topic, EventBridge schedule

Expect 10-15 minutes for stack creation.

### Step 5  -  Deploy real Lambda function code

```powershell
./scripts/aws/deploy-lambda.ps1
```

The CloudFormation template creates Lambda functions with placeholder code. This script replaces them with the actual ``lambda/*.py`` source.

### Step 6  -  Register ECS task definitions

```powershell
./scripts/aws/register-all-tasks.ps1
```

This registers the 4 ECS task definition variants (TOC discovery, TOC parse, page analysis, PDF splitter) with their specific CPU/memory/environment configurations.

### Step 7  -  Restore DynamoDB data (OPTIONAL)

Only do this if you want to skip already-processed books on a re-run.

```powershell
cd $ProjectRoot
python scripts/restore_dynamodb.py ``
    --backup-file AWS_Restoration/dynamodb_backup_jsmith-processing-ledger_${ts}.json ``
    --table jsmith-processing-ledger
```

If the table already has data and you want to start fresh, skip this step.

### Step 8  -  Upload source PDFs to S3

```powershell
aws s3 sync ``
    "G:\My Drive\Sheet Music\" ``
    s3://jsmith-input/SheetMusic_Input/ ``
    --exclude "*" --include "*.pdf" ``
    --region $Region
```

After consolidation, the canonical source PDFs live on Drive at ``G:\My Drive\Sheet Music\<Artist>\<Artist> - <Book>.pdf``. The S3 upload pattern may need adjustment to match the post-consolidation layout  -  verify the path in ``app/main.py`` or the relevant ingest service for current expectations.

### Step 9 (optional)  -  Trigger a pipeline execution

```powershell
aws stepfunctions start-execution ``
    --state-machine-arn "arn:aws:states:${Region}:${AccountId}:stateMachine:${StackName}-pipeline" ``
    --input '{"book_id": "test-book"}' ``
    --region $Region
```

Or run a bulk reprocessing:

```powershell
cd $ProjectRoot
python scripts/run_v3_batch.py --start-fresh
```

## Verification after restoration

1. **CloudFormation stack**  -  should show CREATE_COMPLETE
   ```powershell
   aws cloudformation describe-stacks --stack-name $StackName --region $Region --query 'Stacks[0].StackStatus'
   ```

2. **S3 buckets**  -  should all exist
   ```powershell
   aws s3 ls --region $Region | findstr jsmith
   ```

3. **DynamoDB table**  -  should be ACTIVE
   ```powershell
   aws dynamodb describe-table --table-name jsmith-processing-ledger --region $Region --query 'Table.TableStatus'
   ```

4. **ECR repository**  -  should have at least one image
   ```powershell
   aws ecr describe-images --repository-name $StackName --region $Region --query 'imageDetails[].imageTags'
   ```

5. **Step Functions state machine**  -  should be ACTIVE
   ```powershell
   aws stepfunctions describe-state-machine ``
       --state-machine-arn "arn:aws:states:${Region}:${AccountId}:stateMachine:${StackName}-pipeline" ``
       --region $Region ``
       --query 'status'
   ```

6. **Run a single book** end-to-end as a smoke test (Step 9 above).

## Tearing down again later

```powershell
cd $ProjectRoot
./scripts/aws/cleanup.ps1
```

This destroys everything created by the deployment. Run this only when you're sure the restoration package is preserved and current.

## Notes and gotchas

- **DynamoDB schema mismatch**: The CloudFormation template creates ``jsmith-processing-ledger``, but the existing backup file is for ``jsmith-pipeline-ledger`` (older table). If you want to restore the legacy data, you may need to put it into ``jsmith-processing-ledger`` instead. Verify by comparing schemas before restoring.

- **Bedrock model access**: The first time you use Bedrock in an account, you need to request access to the Claude model at https://console.aws.amazon.com/bedrock  -  submit the model-access request for ``anthropic.claude-3-5-sonnet-20241022-v2:0``. This is usually approved within an hour.

- **S3 bucket name conflicts**: ``jsmith-input``, ``jsmith-output``, and ``jsmith-sheetmusic-splitter-artifacts`` are globally unique S3 bucket names. If you torn-down then immediately try to recreate, you may get name-in-use errors for a brief period (S3 holds bucket names for ~24 hours after deletion). Either wait or change the names.

- **ECS Fargate capacity**: Fargate Spot may not be immediately available in all subnets. If task launches fail with capacity errors, switch the default to FARGATE (not FARGATE_SPOT) in the CloudFormation template.

- **VPC/subnet hardcoding**: ``deploy.ps1`` has hardcoded VPC and subnet IDs from the original account. Update these to match the restoration target. ``vpc_info_${ts}.json`` shows what was in place at the time this package was generated.
"@

$procedureMdFile = Join-Path $RestoreDir 'RESTORATION_PROCEDURE.md'
$procedureMd | Out-File -FilePath $procedureMdFile -Encoding utf8
Write-Ok "Wrote RESTORATION_PROCEDURE.md"

# ===========================================================================
# Summary
# ===========================================================================
Write-Section "Done"
Write-Host ""
Write-Host "AWS restoration package created at:" -ForegroundColor Green
Write-Host "  $RestoreDir" -ForegroundColor Green
Write-Host ""
Write-Host "Contents:" -ForegroundColor Gray
Get-ChildItem $RestoreDir -Recurse -File | ForEach-Object {
    $size = if ($_.Length -lt 1KB) { "$($_.Length) B" }
            elseif ($_.Length -lt 1MB) { "$([math]::Round($_.Length/1KB,1)) KB" }
            else { "$([math]::Round($_.Length/1MB,1)) MB" }
    $rel = $_.FullName -replace [regex]::Escape($RestoreDir + '\'), ''
    Write-Host ("  {0,-12} {1}" -f $size, $rel) -ForegroundColor Gray
}
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Review AWS_RESOURCES.md and RESTORATION_PROCEDURE.md" -ForegroundColor White
Write-Host "  2. Verify the captured data looks complete" -ForegroundColor White
Write-Host "  3. Commit the AWS_Restoration/ folder to git" -ForegroundColor White
Write-Host "  4. Once verified, you can proceed with Phase 4 (AWS teardown)" -ForegroundColor White
