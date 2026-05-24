# AWS Restoration Procedure

This document describes how to rebuild the AWS-side of the songbook-splitter project after teardown.

**Prerequisites**:
- AWS account `227027150061` (or any AWS account, with config adjustments)
- AWS CLI installed and configured
- Docker Desktop installed (for image build)
- PowerShell 7+ (Windows) or PowerShell Core (other platforms)
- Python 3.12+ with packages in `requirements.txt`

## Cost expectations

- Idle: ~`\.50/month` (S3 storage of any preserved content, DynamoDB on-demand baseline)
- Processing run: ~`\.45 per book` (Bedrock vision-heavy)
- A full 342-book reprocessing run will cost roughly the same as the original (`~\`).

If you want to keep AWS storage costs to zero while paused:
1. Empty all S3 buckets before final teardown
2. Delete the CloudFormation stack
3. (Optional) Delete CloudWatch log groups manually if they have content

## Restoration in 8 steps

### Step 1  -  Verify AWS account access

`powershell
aws sts get-caller-identity --region us-east-1
`

Confirm the Account field matches `227027150061` (or your target account if different).

If using a different account:
- Edit `scripts/aws/deploy.ps1` and update the ECR registry URL `CONTAINER_IMAGE`
- Edit `infra/cloudformation_template.yaml` and update default S3 bucket names (must be globally unique)
- Update VPC/subnet IDs in `deploy.ps1` to match the target account's network

### Step 2  -  Create the ECR repository

`powershell
aws ecr create-repository `
    --repository-name jsmith-sheetmusic-splitter `
    --region us-east-1 `
    --image-scanning-configuration scanOnPush=true
`

### Step 3  -  Build and push the Docker container

`powershell
cd S:\aiwork\songbook-splitter
./scripts/aws/deploy-docker.ps1
`

This builds the image from the Dockerfile, tags it with the account-specific ECR URL, and pushes it to ECR.

### Step 4  -  Deploy the CloudFormation stack

`powershell
./scripts/aws/deploy.ps1
`

This creates:
- 3 S3 buckets (input, output, artifacts)
- 1 DynamoDB table (jsmith-processing-ledger)
- 1 ECS Fargate cluster
- 6 Lambda functions (placeholder code at this point  -  Step 5 deploys real code)
- 1 Step Functions state machine
- IAM roles, CloudWatch alarms, SNS topic, EventBridge schedule

Expect 10-15 minutes for stack creation.

### Step 5  -  Deploy real Lambda function code

`powershell
./scripts/aws/deploy-lambda.ps1
`

The CloudFormation template creates Lambda functions with placeholder code. This script replaces them with the actual `lambda/*.py` source.

### Step 6  -  Register ECS task definitions

`powershell
./scripts/aws/register-all-tasks.ps1
`

This registers the 4 ECS task definition variants (TOC discovery, TOC parse, page analysis, PDF splitter) with their specific CPU/memory/environment configurations.

### Step 7  -  Restore DynamoDB data (OPTIONAL)

Only do this if you want to skip already-processed books on a re-run.

`powershell
cd S:\aiwork\songbook-splitter
python scripts/restore_dynamodb.py `
    --backup-file AWS_Restoration/dynamodb_backup_jsmith-processing-ledger_20260524-000428.json `
    --table jsmith-processing-ledger
`

If the table already has data and you want to start fresh, skip this step.

### Step 8  -  Upload source PDFs to S3

`powershell
aws s3 sync `
    "G:\My Drive\Sheet Music\" `
    s3://jsmith-input/SheetMusic_Input/ `
    --exclude "*" --include "*.pdf" `
    --region us-east-1
`

After consolidation, the canonical source PDFs live on Drive at `G:\My Drive\Sheet Music\<Artist>\<Artist> - <Book>.pdf`. The S3 upload pattern may need adjustment to match the post-consolidation layout  -  verify the path in `app/main.py` or the relevant ingest service for current expectations.

### Step 9 (optional)  -  Trigger a pipeline execution

`powershell
aws stepfunctions start-execution `
    --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
    --input '{"book_id": "test-book"}' `
    --region us-east-1
`

Or run a bulk reprocessing:

`powershell
cd S:\aiwork\songbook-splitter
python scripts/run_v3_batch.py --start-fresh
`

## Verification after restoration

1. **CloudFormation stack**  -  should show CREATE_COMPLETE
   `powershell
   aws cloudformation describe-stacks --stack-name jsmith-sheetmusic-splitter --region us-east-1 --query 'Stacks[0].StackStatus'
   `

2. **S3 buckets**  -  should all exist
   `powershell
   aws s3 ls --region us-east-1 | findstr jsmith
   `

3. **DynamoDB table**  -  should be ACTIVE
   `powershell
   aws dynamodb describe-table --table-name jsmith-processing-ledger --region us-east-1 --query 'Table.TableStatus'
   `

4. **ECR repository**  -  should have at least one image
   `powershell
   aws ecr describe-images --repository-name jsmith-sheetmusic-splitter --region us-east-1 --query 'imageDetails[].imageTags'
   `

5. **Step Functions state machine**  -  should be ACTIVE
   `powershell
   aws stepfunctions describe-state-machine `
       --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
       --region us-east-1 `
       --query 'status'
   `

6. **Run a single book** end-to-end as a smoke test (Step 9 above).

## Tearing down again later

`powershell
cd S:\aiwork\songbook-splitter
./scripts/aws/cleanup.ps1
`

This destroys everything created by the deployment. Run this only when you're sure the restoration package is preserved and current.

## Notes and gotchas

- **DynamoDB schema mismatch**: The CloudFormation template creates `jsmith-processing-ledger`, but the existing backup file is for `jsmith-pipeline-ledger` (older table). If you want to restore the legacy data, you may need to put it into `jsmith-processing-ledger` instead. Verify by comparing schemas before restoring.

- **Bedrock model access**: The first time you use Bedrock in an account, you need to request access to the Claude model at https://console.aws.amazon.com/bedrock  -  submit the model-access request for `anthropic.claude-3-5-sonnet-20241022-v2:0`. This is usually approved within an hour.

- **S3 bucket name conflicts**: `jsmith-input`, `jsmith-output`, and `jsmith-sheetmusic-splitter-artifacts` are globally unique S3 bucket names. If you torn-down then immediately try to recreate, you may get name-in-use errors for a brief period (S3 holds bucket names for ~24 hours after deletion). Either wait or change the names.

- **ECS Fargate capacity**: Fargate Spot may not be immediately available in all subnets. If task launches fail with capacity errors, switch the default to FARGATE (not FARGATE_SPOT) in the CloudFormation template.

- **VPC/subnet hardcoding**: `deploy.ps1` has hardcoded VPC and subnet IDs from the original account. Update these to match the restoration target. `vpc_info_20260524-000428.json` shows what was in place at the time this package was generated.
