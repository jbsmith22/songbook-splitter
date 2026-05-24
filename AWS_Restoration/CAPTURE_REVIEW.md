# AWS Restoration Capture - Final Review

Final state after `Capture-AWS-State.ps1`, `Finish-AWS-Capture.ps1`, and `Finish-AWS-Capture-TaskDefs.ps1` all ran successfully.

Authoritative capture timestamp: **`20260524-000428`** (with task-defs follow-up appended same timestamp).

## What got captured

All AWS resources for `jsmith-sheetmusic-splitter` (us-east-1, account 227027150061):

### DynamoDB (current state)

- `jsmith-processing-ledger` (V3 production) - 1,249 items, 3.78 MB
- `jsmith-pipeline-ledger` (V2 legacy) - 399 items, 3.28 MB

### CloudFormation

- Stack outputs (6 outputs)
- All 29 stack resources, all CREATE_COMPLETE

### S3 inventory

- `jsmith-input` - 1,051 entries (177 KB inventory)
- `jsmith-output` - 49,913 entries (10.8 MB inventory)
- `jsmith-jsmith-sheetmusic-splitter-artifacts` - 0 entries (empty - pipeline idle)

Plus per-bucket metadata (location, versioning, lifecycle config).

### ECR

- 117 image versions, latest pushed 2026-02-05 (`latest` tag, 248.3 MB)

### Lambda (6 of 6)

- ingest-service (512 MB)
- check-processed (128 MB)
- record-start (128 MB) - captured via Finish-AWS-Capture.ps1
- record-success (128 MB)
- record-failure (128 MB) - captured via Finish-AWS-Capture.ps1
- record-manual-review (128 MB)

### ECS

- Cluster: `jsmith-sheetmusic-splitter-cluster`
- Task definitions (6 of 6):
  - toc-discovery (revision 1) - from CFN
  - toc-parser (revision 2) - registered by register-all-tasks.ps1
  - page-mapper (revision 4)
  - song-verifier (revision 2)
  - pdf-splitter (revision 3)
  - manifest-generator (revision 2)

All 1024 CPU / 2048 MB memory, Fargate.

### Step Functions

- State machine ARN captured
- 0 recent executions (project idle since Feb 2026 - within 90-day API window)

### IAM (4 of 4)

All roles + inline policies + managed policy attachments:

- `jsmith-sheetmusic-splitter-ECSTaskExecutionRole-lk6cYO4BePSL` - 1 inline policy (ECRAccess) + 1 managed policy (AmazonECSTaskExecutionRolePolicy)
- `jsmith-sheetmusic-splitter-ECSTaskRole-w6lDb4md62rc` - 4 inline policies (S3Access, BedrockAccess, TextractAccess, CloudWatchAccess)
- `jsmith-sheetmusic-splitter-LambdaExecutionRole-c04M7sd14w1q` - 3 inline policies (S3Access, DynamoDBAccess, StepFunctionsAccess) + 1 managed (AWSLambdaBasicExecutionRole)
- `jsmith-sheetmusic-splitter-StepFunctionsRole-ORLcHt5KMOi2` - 2 inline policies (StepFunctionsExecutionPolicy, PassRolePolicy)

### CloudWatch

- 1 log group: `/aws/ecs/jsmith-sheetmusic-splitter` (0 MB - no recent logs)

### Network

- VPC info (7.47 KB)
- All subnets in the account (70.85 KB)

### Documentation

- `AWS_RESOURCES.md` - resource inventory
- `RESTORATION_PROCEDURE.md` - step-by-step rebuild guide
- `CAPTURE_REVIEW.md` - this file

## Files (final listing)

```
AWS_Restoration/
  AWS_RESOURCES.md                                                          5.6 KB
  CAPTURE_REVIEW.md                                                        ~6 KB
  RESTORATION_PROCEDURE.md                                                  6.7 KB
  
  cfn_stack_outputs_20260524-000428.json                                    3.3 KB
  cfn_stack_resources_20260524-000428.json                                 12.7 KB
  
  dynamodb_backup_jsmith-processing-ledger_20260524-000428.json             3.6 MB
  dynamodb_backup_jsmith-pipeline-ledger_20260524-000428.json               3.1 MB
  
  ecr_images_20260524-000428.json                                          63.9 KB
  
  lambda_functions_20260524-000428.json                                       7 KB
  lambda_jsmith-sheetmusic-splitter-record-start_20260524-000428.json       1.4 KB
  lambda_jsmith-sheetmusic-splitter-record-failure_20260524-000428.json     1.4 KB
  
  ecs_cluster_20260524-000428.json                                          868 B
  ecs_task_definitions_20260524-000428/
    jsmith-sheetmusic-splitter-toc-discovery.json                           3.4 KB
    jsmith-sheetmusic-splitter-toc-parser.json                              2.8 KB
    jsmith-sheetmusic-splitter-page-mapper.json                            ~2.8 KB
    jsmith-sheetmusic-splitter-song-verifier.json                          ~2.8 KB
    jsmith-sheetmusic-splitter-pdf-splitter.json                              3 KB
    jsmith-sheetmusic-splitter-manifest-generator.json                     ~2.8 KB
  
  iam_20260524-000428/  (4 role files + 10 inline policies + 4 managed)
  
  s3_inventory_20260524-000428/
    jsmith-input_inventory.txt                                            177.4 KB
    jsmith-input_metadata.json                                              584 B
    jsmith-output_inventory.txt                                            10.8 MB
    jsmith-output_metadata.json                                             205 B
    jsmith-jsmith-sheetmusic-splitter-artifacts_inventory.txt                90 B
    jsmith-jsmith-sheetmusic-splitter-artifacts_metadata.json               517 B
  
  stepfunctions_executions_20260524-000428.json                              31 B
  
  cloudwatch_loggroups_20260524-000428.json                                 472 B
  
  vpc_info_20260524-000428.json                                             7.5 KB
  subnets_20260524-000428.json                                             70.9 KB
```

Total package size: roughly 20 MB.

## What's NOT in this package (and why)

| Not captured | Why it's fine |
|---|---|
| Step Functions execution history | None recent (90-day window). State machine definition is in CFN. |
| CloudWatch log content | Log group is empty (0 MB). |
| S3 bucket contents themselves | We have inventories. Input PDFs are also on G:\ Drive. Output songs are at D:\ Work\songbook-splitter\SheetMusic_Output (cloud-synced to Drive). Artifacts bucket is empty. |
| ECR image binaries | Dockerfile is in source control. Can rebuild from source. Latest image is 4 months old anyway. |
| Lambda zip code | Source is in lambda/*.py. deploy-lambda.ps1 will repackage and deploy. |

## Ready for teardown

The restoration package is complete. After committing to git, the AWS resources can be safely torn down via `scripts/aws/cleanup.ps1`.

## Commit command

```powershell
cd S:\aiwork\songbook-splitter
git add AWS_Restoration/ Capture-AWS-State.ps1 Cleanup-AWS-Restoration-Duplicates.ps1 Finish-AWS-Capture.ps1 Finish-AWS-Capture-TaskDefs.ps1
git status
git commit -m "Phase 2: AWS restoration package captured"
git push  # if remote is configured
```
