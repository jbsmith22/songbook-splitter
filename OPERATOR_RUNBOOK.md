# SheetMusic Book Splitter - Operator Runbook

**Version**: 1.0  
**Last Updated**: 2026-01-28  
**Status**: Production Operational

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Daily Operations](#daily-operations)
3. [Processing New Books](#processing-new-books)
4. [Monitoring and Alerts](#monitoring-and-alerts)
5. [Troubleshooting](#troubleshooting)
6. [Maintenance Tasks](#maintenance-tasks)
7. [Emergency Procedures](#emergency-procedures)
8. [Cost Management](#cost-management)

---

## System Overview

### Architecture
The SheetMusic Book Splitter is an AWS serverless pipeline that:
1. Discovers PDF songbooks in S3
2. Extracts Table of Contents using OCR
3. Maps page numbers to PDF indices
4. Verifies song start pages
5. Splits books into individual song PDFs
6. Generates audit manifests

### Key Components
- **Step Functions**: Orchestrates the 6-stage pipeline
- **ECS Fargate**: Runs compute-intensive processing tasks
- **Lambda**: Handles orchestration and state management
- **S3**: Stores input PDFs and output songs
- **DynamoDB**: Tracks processing state
- **CloudWatch**: Logs, metrics, and alarms

### AWS Resources
- **Account**: 227027150061
- **Region**: us-east-1
- **Profile**: default (requires SSO login)
- **State Machine**: `jsmith-sheetmusic-splitter-pipeline`
- **Input Bucket**: `jsmith-input`
- **Output Bucket**: `jsmith-output`
- **DynamoDB Table**: `jsmith-processing-ledger`

---

## Daily Operations

### Morning Checklist

1. **Check CloudWatch Alarms**
   ```powershell
   aws cloudwatch describe-alarms --state-value ALARM --profile default
   ```
   - Should return no alarms in ALARM state
   - If alarms present, see [Troubleshooting](#troubleshooting)

2. **Review Recent Executions**
   ```powershell
   aws stepfunctions list-executions `
     --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
     --max-results 20 `
     --profile default
   ```
   - Check for any FAILED executions
   - Review SUCCEEDED executions for processing time

3. **Check DynamoDB Ledger**
   ```powershell
   aws dynamodb scan --table-name jsmith-processing-ledger `
     --filter-expression "#status = :failed" `
     --expression-attribute-names '{"#status":"status"}' `
     --expression-attribute-values '{":failed":{"S":"failed"}}' `
     --profile default
   ```
   - Review any failed books
   - Determine if retry is needed

4. **Review CloudWatch Logs**
   ```powershell
   aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 24h --profile default | Select-String "ERROR"
   ```
   - Look for any ERROR level logs
   - Investigate patterns or recurring issues

### Weekly Checklist

1. **Cost Review**
   - Check AWS Cost Explorer for unexpected charges
   - Verify costs align with processing volume
   - Target: ~$0.07 per book processed

2. **Storage Cleanup**
   - Review S3 bucket sizes
   - Clean up old artifacts if needed
   - Verify lifecycle policies are working

3. **Performance Review**
   - Check average processing time per book
   - Identify any performance degradation
   - Review ECS task metrics

4. **Backup Verification**
   - Verify DynamoDB backups are running
   - Check S3 versioning is enabled
   - Test restore procedure if needed

---

## Processing New Books

### Upload Books to S3

1. **Prepare Source PDFs**
   - Organize in folder structure: `SheetMusic/<Artist>/books/<BookName>.pdf`
   - Verify PDF files are not corrupted
   - Check file sizes (large files may need special handling)

2. **Upload to S3**
   ```powershell
   aws s3 cp "SheetMusic/Artist Name/books/Book Name.pdf" `
     "s3://jsmith-input/SheetMusic/Artist Name/books/Book Name.pdf" `
     --profile default
   ```

3. **Trigger Processing**
   ```powershell
   # Create execution input
   $input = @{
       bucket = "jsmith-input"
       key = "SheetMusic/Artist Name/books/Book Name.pdf"
       artist = "Artist Name"
       book_name = "Book Name"
       book_id = (Get-FileHash "SheetMusic/Artist Name/books/Book Name.pdf" -Algorithm SHA256).Hash.Substring(0,16)
   } | ConvertTo-Json

   # Start execution
   aws stepfunctions start-execution `
     --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
     --input $input `
     --profile default
   ```

### Batch Processing

For processing multiple books:

1. **Create Batch Script**
   ```powershell
   # process-batch.ps1
   $books = Import-Csv books-to-process.csv
   
   foreach ($book in $books) {
       # Upload to S3
       aws s3 cp $book.SourcePath "s3://jsmith-input/$($book.S3Key)" --profile default
       
       # Start execution
       $input = @{
           bucket = "jsmith-input"
           key = $book.S3Key
           artist = $book.Artist
           book_name = $book.BookName
           book_id = $book.BookId
       } | ConvertTo-Json
       
       aws stepfunctions start-execution `
         --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" `
         --input $input `
         --profile default
       
       # Wait between books to avoid rate limiting
       Start-Sleep -Seconds 30
   }
   ```

2. **Monitor Progress**
   ```powershell
   .\monitor-all-executions.ps1
   ```

3. **Download Results**
   ```powershell
   .\download-with-s3-search.ps1
   ```

### Rate Limiting Guidelines

- **Maximum Concurrent Executions**: 10
- **Delay Between Starts**: 30 seconds
- **Batch Size**: 5-10 books per batch
- **Wait Between Batches**: 60 seconds

---

## Monitoring and Alerts

### CloudWatch Alarms

The system has 7 configured alarms:

1. **Cost Threshold Alarm**
   - Triggers when daily costs exceed $50
   - Action: Review processing volume and costs

2. **Error Rate Alarm**
   - Triggers when error rate exceeds 10%
   - Action: Check logs for recurring errors

3. **Lambda Error Alarm**
   - Triggers on Lambda function failures
   - Action: Check Lambda logs and permissions

4. **ECS Task Failure Alarm**
   - Triggers on ECS task failures
   - Action: Check ECS logs and task definitions

5. **Processing Failure Alarm**
   - Triggers when books fail processing
   - Action: Review failed books in DynamoDB

6. **Manual Review Alarm**
   - Triggers when books require manual review
   - Action: Review quality gate failures

7. **State Machine Failure Alarm**
   - Triggers on Step Functions execution failures
   - Action: Check execution history

### Key Metrics to Monitor

**Processing Metrics**:
- Books processed per day
- Average processing time per book
- Success rate (target: >95%)
- Songs extracted per book

**Cost Metrics**:
- Daily AWS costs
- Cost per book processed
- Textract API usage
- Bedrock API usage

**Performance Metrics**:
- ECS task duration
- Lambda invocation duration
- S3 transfer times
- DynamoDB read/write latency

### Accessing Metrics

**CloudWatch Console**:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:
```

**CLI Commands**:
```powershell
# Get processing metrics
aws cloudwatch get-metric-statistics `
  --namespace SheetMusicSplitter `
  --metric-name BooksProcessed `
  --start-time (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
  --period 86400 `
  --statistics Sum `
  --profile default

# Get error metrics
aws cloudwatch get-metric-statistics `
  --namespace SheetMusicSplitter `
  --metric-name ProcessingErrors `
  --start-time (Get-Date).AddDays(-1).ToString("yyyy-MM-ddTHH:mm:ss") `
  --end-time (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss") `
  --period 3600 `
  --statistics Sum `
  --profile default
```

---

## Troubleshooting

### Common Issues

#### 1. Execution Fails with "TOC Not Found"

**Symptoms**:
- Step Functions execution fails at TOC Discovery stage
- Logs show "No TOC pages found"

**Diagnosis**:
```powershell
# Check TOC discovery artifacts
aws s3 ls "s3://jsmith-output/artifacts/<book_id>/" --profile default

# View logs
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 1h --filter-pattern "book_id=<book_id>" --profile default
```

**Solutions**:
1. Verify PDF has a table of contents
2. Increase MAX_PAGES environment variable
3. Check if TOC is in unusual format
4. Consider manual TOC entry

#### 2. Rate Limiting Errors

**Symptoms**:
- Textract or Bedrock throttling errors
- Multiple executions failing simultaneously

**Diagnosis**:
```powershell
# Check for throttling errors
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 1h --filter-pattern "ThrottlingException" --profile default
```

**Solutions**:
1. Reduce concurrent executions
2. Increase delay between batch starts
3. Request service quota increase if needed
4. Process books in smaller batches

#### 3. Song Verification Failures

**Symptoms**:
- Books marked for manual review
- Verification success rate <95%

**Diagnosis**:
```powershell
# Check verification results
aws s3 cp "s3://jsmith-output/artifacts/<book_id>/verification_results.json" - --profile default
```

**Solutions**:
1. Review page mapping offset
2. Check for unusual page layouts
3. Verify song titles match TOC
4. Adjust verification thresholds if needed

#### 4. S3 Access Denied

**Symptoms**:
- Execution fails with S3 access errors
- Logs show "Access Denied"

**Diagnosis**:
```powershell
# Check IAM role permissions
aws iam get-role-policy --role-name <ECS-Task-Role> --policy-name <PolicyName> --profile default
```

**Solutions**:
1. Verify IAM role has S3 permissions
2. Check bucket policies
3. Verify bucket names in environment variables
4. Check if SSO session expired

#### 5. DynamoDB Write Failures

**Symptoms**:
- Execution completes but status not recorded
- Logs show DynamoDB errors

**Diagnosis**:
```powershell
# Check DynamoDB table
aws dynamodb describe-table --table-name jsmith-processing-ledger --profile default
```

**Solutions**:
1. Verify table exists and is active
2. Check IAM permissions for DynamoDB
3. Verify table name in environment variables
4. Check for provisioned throughput issues

### Log Analysis

**View Recent Errors**:
```powershell
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 1h --filter-pattern "ERROR" --profile default
```

**Search for Specific Book**:
```powershell
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 24h --filter-pattern "book_id=<book_id>" --profile default
```

**View Lambda Logs**:
```powershell
aws logs tail "/aws/lambda/jsmith-sheetmusic-splitter-ingest-service" --since 1h --profile default
```

### Execution History

**Get Execution Details**:
```powershell
aws stepfunctions describe-execution --execution-arn "<execution-arn>" --profile default
```

**Get Execution History**:
```powershell
aws stepfunctions get-execution-history --execution-arn "<execution-arn>" --max-results 100 --profile default
```

**Find Failed Steps**:
```powershell
aws stepfunctions get-execution-history --execution-arn "<execution-arn>" --profile default | ConvertFrom-Json | Select-Object -ExpandProperty events | Where-Object { $_.type -match "Failed" }
```

---

## Maintenance Tasks

### Monthly Maintenance

1. **Update Dependencies**
   ```powershell
   # Update Python packages
   py -m pip list --outdated
   py -m pip install --upgrade <package>
   
   # Rebuild Docker image
   .\deploy-docker.ps1
   ```

2. **Review and Clean S3 Artifacts**
   ```powershell
   # List old artifacts
   aws s3 ls "s3://jsmith-output/artifacts/" --recursive --profile default | Where-Object { $_.LastWriteTime -lt (Get-Date).AddMonths(-3) }
   
   # Delete old artifacts (if needed)
   aws s3 rm "s3://jsmith-output/artifacts/<old-book-id>/" --recursive --profile default
   ```

3. **DynamoDB Cleanup**
   ```powershell
   # Query old records
   aws dynamodb scan --table-name jsmith-processing-ledger `
     --filter-expression "processing_timestamp < :cutoff" `
     --expression-attribute-values '{":cutoff":{"N":"<timestamp>"}}' `
     --profile default
   
   # Delete if needed (be careful!)
   ```

4. **Cost Optimization Review**
   - Review CloudWatch logs retention (reduce if needed)
   - Check S3 storage classes (move to Glacier if appropriate)
   - Review ECS task sizes (right-size CPU/memory)

### Quarterly Maintenance

1. **Security Review**
   - Review IAM roles and policies
   - Check for unused permissions
   - Rotate access keys if applicable
   - Review CloudTrail logs

2. **Performance Optimization**
   - Analyze processing times
   - Identify bottlenecks
   - Consider parallel processing improvements
   - Review ECS task configurations

3. **Disaster Recovery Test**
   - Test DynamoDB restore
   - Verify S3 versioning works
   - Test CloudFormation stack recreation
   - Document recovery procedures

### Annual Maintenance

1. **Full System Audit**
   - Review all AWS resources
   - Check for unused resources
   - Verify backup strategies
   - Update documentation

2. **Cost Analysis**
   - Review annual costs
   - Compare to budget
   - Identify optimization opportunities
   - Plan for next year

---

## Emergency Procedures

### System Down

1. **Check AWS Service Health**
   ```
   https://status.aws.amazon.com/
   ```

2. **Verify CloudFormation Stack**
   ```powershell
   aws cloudformation describe-stacks --stack-name jsmith-sheetmusic-splitter --profile default
   ```

3. **Check Step Functions State Machine**
   ```powershell
   aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" --profile default
   ```

4. **Restart Services if Needed**
   ```powershell
   # Update Step Functions (if needed)
   aws stepfunctions update-state-machine --state-machine-arn "<arn>" --definition file://infra/step_functions_complete.json --profile default
   
   # Redeploy Lambda functions
   .\deploy-lambda.ps1
   ```

### Data Loss

1. **Check S3 Versioning**
   ```powershell
   aws s3api list-object-versions --bucket jsmith-output --prefix "SheetMusicOut/" --profile default
   ```

2. **Restore from Version**
   ```powershell
   aws s3api get-object --bucket jsmith-output --key "<key>" --version-id "<version-id>" "<output-file>" --profile default
   ```

3. **Restore DynamoDB**
   ```powershell
   # List backups
   aws dynamodb list-backups --table-name jsmith-processing-ledger --profile default
   
   # Restore from backup
   aws dynamodb restore-table-from-backup --target-table-name jsmith-processing-ledger-restored --backup-arn "<backup-arn>" --profile default
   ```

### Cost Overrun

1. **Stop All Executions**
   ```powershell
   # List running executions
   aws stepfunctions list-executions --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" --status-filter RUNNING --profile default
   
   # Stop each execution
   aws stepfunctions stop-execution --execution-arn "<execution-arn>" --profile default
   ```

2. **Review Costs**
   ```powershell
   # Check current month costs
   aws ce get-cost-and-usage --time-period Start=(Get-Date -Format "yyyy-MM-01"),End=(Get-Date -Format "yyyy-MM-dd") --granularity DAILY --metrics BlendedCost --profile default
   ```

3. **Identify Cost Drivers**
   - Check Textract usage
   - Check Bedrock usage
   - Check ECS task hours
   - Check S3 storage and transfers

4. **Implement Cost Controls**
   - Reduce concurrent executions
   - Increase delays between batches
   - Review and optimize task sizes
   - Consider processing schedule

---

## Cost Management

### Cost Breakdown

**Per Book Processing**:
- Textract: ~$0.030 (20 pages × $0.0015/page)
- Bedrock: ~$0.020 (fallback for ~25% of books)
- ECS Fargate: ~$0.015 (6 tasks × 1.5 min)
- Other: ~$0.005
- **Total**: ~$0.07 per book

**Monthly Idle Costs**:
- S3 Storage: ~$0.50
- CloudWatch Logs: ~$0.50
- ECR: ~$0.10
- **Total**: ~$1.10/month

### Cost Optimization Tips

1. **Reduce Textract Usage**
   - Limit MAX_PAGES for TOC discovery
   - Cache Textract responses
   - Use deterministic parsing when possible

2. **Minimize Bedrock Usage**
   - Improve deterministic parser
   - Reduce fallback rate
   - Limit token usage

3. **Optimize ECS Tasks**
   - Right-size CPU and memory
   - Reduce task duration
   - Use Spot instances if appropriate

4. **S3 Cost Reduction**
   - Use lifecycle policies
   - Move old artifacts to Glacier
   - Enable S3 Intelligent-Tiering

### Budget Alerts

Current budget: $1,000 for 500 books

**Alert Thresholds**:
- 50% ($500): Warning
- 75% ($750): Review and optimize
- 90% ($900): Stop processing

**Set Budget Alert**:
```powershell
aws budgets create-budget --account-id 227027150061 `
  --budget file://budget-config.json `
  --notifications-with-subscribers file://budget-notifications.json `
  --profile default
```

---

## Contact Information

### AWS Support
- **Account**: 227027150061
- **Support Plan**: (Specify your support plan)
- **Support Portal**: https://console.aws.amazon.com/support/

### Project Team
- **Project Owner**: (Your name/email)
- **Technical Lead**: (Your name/email)
- **Operations**: (Your name/email)

### Escalation Path
1. Check this runbook
2. Review CloudWatch logs
3. Check AWS Service Health
4. Contact AWS Support if needed

---

## Appendix

### Useful Commands Reference

```powershell
# AWS SSO Login
aws sso login --profile default

# List Executions
aws stepfunctions list-executions --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline" --profile default

# View Logs
aws logs tail "/aws/ecs/jsmith-sheetmusic-splitter" --since 1h --profile default

# Check DynamoDB
aws dynamodb scan --table-name jsmith-processing-ledger --profile default

# List S3 Output
aws s3 ls s3://jsmith-output/SheetMusicOut/ --recursive --profile default

# Get Execution Details
aws stepfunctions describe-execution --execution-arn "<arn>" --profile default

# Stop Execution
aws stepfunctions stop-execution --execution-arn "<arn>" --profile default

# Check CloudWatch Alarms
aws cloudwatch describe-alarms --state-value ALARM --profile default

# Get Cost Data
aws ce get-cost-and-usage --time-period Start=2026-01-01,End=2026-01-31 --granularity MONTHLY --metrics BlendedCost --profile default
```

### Environment Variables

**ECS Tasks**:
- `TASK_TYPE`: Type of processing task
- `BOOK_ID`: Unique book identifier
- `SOURCE_PDF_URI`: S3 URI of source PDF
- `OUTPUT_BUCKET`: S3 output bucket name
- `MAX_PAGES`: Maximum pages to scan for TOC
- `VERIFICATION_THRESHOLD`: Song verification threshold

**Lambda Functions**:
- `STATE_MACHINE_ARN`: Step Functions ARN
- `DYNAMODB_TABLE`: DynamoDB table name
- `INPUT_BUCKET`: S3 input bucket name
- `OUTPUT_BUCKET`: S3 output bucket name

---

**End of Operator Runbook**

*Last Updated: 2026-01-28*
