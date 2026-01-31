# SheetMusic Book Splitter - AWS Deployment Plan

## Deployment Summary

**AWS Account**: 227027150061  
**Region**: us-east-1  
**VPC**: vpc-4c5f5735  
**Subnet**: subnet-0f6ba7ae50933273e  
**Stack Name**: jsmith-sheetmusic-splitter  

---

## What We're Deploying

### Infrastructure Components

1. **S3 Buckets** (3 total)
   - `jsmith-input` - For uploading songbook PDFs
   - `jsmith-output` - For split song PDFs and manifests
   - `jsmith-sheetmusic-splitter-artifacts` - For intermediate processing artifacts
   - All buckets have versioning enabled
   - Lifecycle policies for cleanup

2. **DynamoDB Table**
   - `jsmith-processing-ledger` - Tracks processing state
   - Pay-per-request billing
   - Global secondary index on status
   - TTL enabled for automatic cleanup

3. **ECR Repository**
   - `jsmith-sheetmusic-splitter` - For Docker container images

4. **ECS Cluster**
   - Fargate-based (serverless containers)
   - Task definitions for: TOC Discovery, TOC Parser, Page Mapper, Song Verifier, PDF Splitter

5. **Lambda Functions** (6 total)
   - Ingest Service - Discovers PDFs and starts processing
   - Check Processed - Idempotency check
   - Record Start - Records processing start
   - Record Success - Records successful completion
   - Record Failure - Records failures
   - Record Manual Review - Records quality gate failures

6. **Step Functions State Machine**
   - Orchestrates the entire pipeline
   - Includes retry logic and error handling
   - Quality gates at multiple checkpoints

7. **CloudWatch Resources**
   - Log groups for all services
   - Custom metrics for monitoring
   - 7 CloudWatch Alarms:
     - Cost threshold ($50/day)
     - Error rate (>10%)
     - Processing failures
     - Manual review required
     - State machine failures
     - Lambda errors
     - ECS task failures

8. **SNS Topic**
   - For alarm notifications
   - You can subscribe your email to receive alerts

9. **IAM Roles** (3 total)
   - ECS Task Execution Role
   - ECS Task Role
   - Lambda Execution Role
   - Step Functions Execution Role

10. **EventBridge Rule**
    - Scheduled daily execution (can be disabled)

---

## Cost Estimate

### One-Time Costs
- **ECR Storage**: ~$0.10/month for Docker image (~1GB)
- **Setup**: $0 (no charges for creating resources)

### Per-Book Processing Costs (estimated for 50-song, 500-page book)
- **Textract**: $0.15 (20 pages @ $0.0075/page)
- **Bedrock** (if used): $0.05 (5000 tokens @ $0.01/1K tokens)
- **ECS Fargate**: $0.10 (5 minutes @ $0.04/vCPU-hour, 0.5GB RAM)
- **Lambda**: $0.01 (minimal execution time)
- **Step Functions**: $0.01 (state transitions)
- **S3**: $0.01 (storage + requests)
- **DynamoDB**: $0.01 (reads + writes)
- **CloudWatch**: $0.01 (logs + metrics)

**Total per book**: ~$0.35

### Monthly Baseline Costs (if idle)
- **S3 Storage**: $0.023/GB/month
  - Input bucket: ~$2/month (assuming 100GB of PDFs)
  - Output bucket: ~$5/month (assuming 200GB of split songs)
  - Artifacts: ~$1/month (assuming 50GB)
- **DynamoDB**: $0 (pay-per-request, no charges when idle)
- **CloudWatch Logs**: ~$0.50/month (minimal retention)
- **ECR**: ~$0.10/month (image storage)

**Monthly baseline (idle)**: ~$8.60/month

### Processing 500 Books
- **Processing costs**: 500 × $0.35 = $175
- **Storage increase**: ~100GB output = ~$2.30/month ongoing
- **Total one-time**: ~$175
- **Ongoing monthly**: ~$10.90/month

### Alarm Threshold
- Cost alarm set at $50/day to prevent runaway costs

---

## Deployment Steps

### Phase 1: Create ECR Repository and Build Container
1. Create ECR repository
2. Build Docker image
3. Push image to ECR

### Phase 2: Deploy CloudFormation Stack
1. Package Lambda code
2. Deploy CloudFormation template
3. Wait for stack creation (~10-15 minutes)

### Phase 3: Verification
1. Verify all resources created
2. Check CloudWatch logs
3. Subscribe to SNS topic for alerts

### Phase 4: Test with Sample PDF
1. Upload a test PDF to input bucket
2. Trigger Ingest Service Lambda
3. Monitor Step Functions execution
4. Verify output in output bucket

---

## Cleanup/Destruction Process

To completely remove everything we create:

### Option 1: Delete CloudFormation Stack (Recommended)
```bash
aws cloudformation delete-stack --stack-name jsmith-sheetmusic-splitter --region us-east-1
```

This will delete:
- All Lambda functions
- Step Functions state machine
- ECS cluster and task definitions
- IAM roles
- CloudWatch log groups
- CloudWatch alarms
- SNS topic
- EventBridge rule

### Option 2: Manual Cleanup (if stack deletion fails)
1. Empty and delete S3 buckets (must be done manually)
2. Delete DynamoDB table
3. Delete ECR repository
4. Delete CloudFormation stack

### Important Notes on Cleanup
- **S3 buckets must be emptied before deletion** (CloudFormation won't delete non-empty buckets)
- **DynamoDB table** - CloudFormation will delete it (data will be lost)
- **ECR repository** - Must be deleted separately
- **CloudWatch logs** - Will be deleted with stack
- **No charges after cleanup** (except any remaining S3 storage)

---

## Security Considerations

1. **S3 Buckets**: All have public access blocked
2. **IAM Roles**: Follow least-privilege principle
3. **VPC**: ECS tasks run in your existing VPC
4. **Encryption**: S3 uses default encryption
5. **Secrets**: No secrets or credentials stored in code

---

## Monitoring and Alerts

### CloudWatch Alarms Will Alert On:
- Daily costs exceeding $50
- Error rate above 10%
- Any processing failures
- Books requiring manual review
- Step Functions execution failures
- Lambda function errors
- ECS task failures

### To Receive Alerts:
After deployment, subscribe to the SNS topic:
```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:227027150061:jsmith-sheetmusic-splitter-alarms \
  --protocol email \
  --notification-endpoint your-email@example.com
```

---

## Post-Deployment Usage

### Upload PDFs for Processing
```bash
aws s3 cp "path/to/book.pdf" s3://jsmith-input/SheetMusic/ArtistName/books/
```

### Trigger Processing Manually
```bash
aws lambda invoke \
  --function-name jsmith-sheetmusic-splitter-ingest-service \
  --region us-east-1 \
  response.json
```

### Check Processing Status
```bash
aws dynamodb scan \
  --table-name jsmith-processing-ledger \
  --region us-east-1
```

### View Step Functions Executions
```bash
aws stepfunctions list-executions \
  --state-machine-arn <state-machine-arn> \
  --region us-east-1
```

---

## Risk Assessment

### Low Risk
- All resources are in your dedicated AWS account
- CloudFormation provides rollback on failure
- No production data at risk
- Easy to delete everything

### Medium Risk
- Costs could accumulate if processing many books
- Cost alarm provides protection ($50/day threshold)

### Mitigation
- Start with 1-2 test PDFs
- Monitor costs in AWS Cost Explorer
- Set up billing alerts
- Can disable EventBridge rule to prevent automatic processing

---

## Timeline

- **Deployment**: 15-20 minutes
- **First test**: 5 minutes
- **Full cleanup**: 5 minutes

---

## Next Steps

1. Review this plan
2. Confirm you want to proceed
3. I'll generate the deployment commands
4. You execute them one by one
5. We verify everything works
6. Test with a sample PDF

---

## Questions to Confirm

1. ✅ Deploy to account 227027150061?
2. ✅ Use region us-east-1?
3. ✅ Use VPC vpc-4c5f5735?
4. ✅ Use subnet subnet-0f6ba7ae50933273e?
5. ✅ Use "jsmith" prefix for all resources?
6. ✅ Understand costs (~$0.35/book, ~$10/month baseline)?
7. ✅ Understand cleanup process?
8. ✅ Ready to proceed?

**If everything looks good, confirm and I'll generate the deployment commands!**
