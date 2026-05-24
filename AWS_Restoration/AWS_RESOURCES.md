# AWS Resources Inventory

Generated: 20260524-000428
Account: 227027150061
Region: us-east-1

## Resource Naming Conventions

All resources are prefixed with `jsmith-` or `jsmith-sheetmusic-splitter-`:

| Resource Type | Name | Purpose |
|---|---|---|
| CloudFormation Stack | jsmith-sheetmusic-splitter | Top-level container for all infrastructure |
| S3 Bucket | jsmith-input | Source PDFs uploaded for processing |
| S3 Bucket | jsmith-output | Split songs and processed artifacts |
| S3 Bucket | jsmith-sheetmusic-splitter-artifacts | Pipeline JSON artifacts (TOC, page analysis, etc.) |
| DynamoDB Table | jsmith-processing-ledger | Per-book processing status (this is the v3 production table) |
| DynamoDB Table | jsmith-pipeline-ledger | Historical pipeline runs (V2 era  -  may be empty) |
| ECR Repository | jsmith-sheetmusic-splitter | Docker container for ECS tasks |
| ECS Cluster | jsmith-sheetmusic-splitter-cluster | Fargate cluster running pipeline tasks |
| Step Functions State Machine | jsmith-sheetmusic-splitter-pipeline | Orchestrates per-book processing flow |
| SNS Topic | jsmith-sheetmusic-splitter-alarms | Alarm notifications |
| Lambda Functions | jsmith-sheetmusic-splitter-* | ingest-service, check-processed, record-start, record-success, record-failure, record-manual-review |
| CloudWatch Log Group | /aws/ecs/jsmith-sheetmusic-splitter | ECS task logs |

## AWS Services Used

- **S3**  -  file storage (input, output, artifacts)
- **DynamoDB**  -  processing ledger (book status, per-step metadata)
- **Step Functions**  -  pipeline orchestration
- **ECS Fargate**  -  containerized tasks for TOC discovery, page analysis, PDF splitting
- **Lambda**  -  lightweight handlers (DynamoDB updates, ingest, decision points)
- **Bedrock**  -  Claude 3.5 Sonnet (model ID `anthropic.claude-3-5-sonnet-20241022-v2:0`) for vision-based page classification
- **Textract**  -  OCR for TOC discovery from page images
- **CloudWatch**  -  logs, metrics, alarms
- **SNS**  -  alarm notifications
- **EventBridge**  -  scheduled triggers
- **ECR**  -  Docker image registry
- **VPC + Security Groups**  -  network isolation for ECS tasks
- **IAM**  -  roles for ECS, Lambda, Step Functions

## Pipeline Cost Profile (Historical)

- Original 342-book V3 run: ~`\` total cost
- Per-book cost: ~`\.45` (varies by book size  -  Bedrock vision calls are the biggest factor)
- Cost breakdown (approximate):
  - Bedrock vision (~85%): page analysis + TOC parsing
  - ECS Fargate (~10%): PDF rendering, splitting, page extraction
  - Textract (~3%): TOC OCR
  - S3 storage + transfer (~1%): minimal
  - Lambda + Step Functions (~1%): control plane

## VPC and Network

See `vpc_info_20260524-000428.json` and `subnets_20260524-000428.json` for VPC ID, subnet IDs, and security group details used by ECS tasks.

The deploy.ps1 script references hardcoded VPC `vpc-4c5f5735` and subnet `subnet-0f6ba7ae50933273e`. These are the defaults at restoration time. If the AWS account VPC topology has changed when restoring, update `scripts/aws/deploy.ps1` to point at the current VPC/subnet.

## IAM Roles

Roles automatically created by the CloudFormation stack:

- ECSTaskExecutionRole  -  pulls container images, writes logs
- ECSTaskRole  -  accesses S3, DynamoDB, Textract, Bedrock from inside containers
- LambdaExecutionRole  -  Lambda execution + S3 + DynamoDB + Step Functions invoke
- StepFunctionsRole  -  invokes Lambda, runs ECS tasks, passes IAM roles

Full role definitions are in `iam_roles_20260524-000428.json`.

## Files in this AWS_Restoration folder

- `AWS_RESOURCES.md`  -  this file
- `RESTORATION_PROCEDURE.md`  -  step-by-step rebuild guide
- `dynamodb_backup_jsmith-processing-ledger_20260524-000428.json`  -  current v3 ledger (this is what to restore)
- `dynamodb_backup_jsmith-pipeline-ledger_20260524-000428.json`  -  V2 legacy table (may be empty)
- `dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json`  -  pre-existing snapshot (older, kept as belt-and-suspenders)
- `cfn_stack_outputs_20260524-000428.json`  -  CloudFormation stack outputs (ARNs, bucket names)
- `cfn_stack_resources_20260524-000428.json`  -  list of all resources created by the CFN stack
- `ecr_images_20260524-000428.json`  -  Docker image versions and tags
- `stepfunctions_executions_20260524-000428.json`  -  recent execution history
- `stepfunctions_execution_details_20260524-000428/`  -  detailed Step Functions logs for 5 successful runs
- `s3_inventory_20260524-000428/`  -  file lists for each S3 bucket
- `lambda_functions_20260524-000428.json`  -  Lambda function configurations
- `ecs_cluster_20260524-000428.json`  -  ECS cluster details
- `ecs_task_definitions_20260524-000428/`  -  all ECS task definition JSONs
- `cloudwatch_loggroups_20260524-000428.json`  -  CloudWatch log group inventory
- `vpc_info_20260524-000428.json` + `subnets_20260524-000428.json`  -  network topology
- `iam_roles_20260524-000428.json`  -  IAM role definitions

Plus from the project repo (NOT in this folder, but referenced by RESTORATION_PROCEDURE.md):

- `../infra/cloudformation_template.yaml`  -  the canonical infrastructure definition
- `../infra/step_functions_complete.json`  -  Step Functions state machine definition
- `../scripts/aws/deploy.ps1`  -  main deployment script
- `../scripts/aws/deploy-docker.ps1`  -  Docker image build and push
- `../scripts/aws/deploy-lambda.ps1`  -  Lambda function code deployment
- `../scripts/aws/register-all-tasks.ps1`  -  ECS task definition registration
- `../scripts/aws/cleanup.ps1`  -  full teardown script (NOT to be run during restoration)
- `../Dockerfile`  -  container image build definition
- `../requirements.txt`  -  Python dependencies
