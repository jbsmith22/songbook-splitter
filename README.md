# SheetMusic Book Splitter

**Status**: 🚀 **DEPLOYED TO AWS** | Pipeline operational, testing in progress

An AWS-based serverless pipeline that automatically splits sheet music compilation books into individual song PDFs using OCR, AI parsing, and intelligent page mapping.

## Quick Start

```bash
# Deploy infrastructure
.\deploy.ps1

# Build and push Docker image
.\deploy-docker.ps1

# Deploy Lambda functions
.\deploy-lambda.ps1

# Test locally
python local_runner.py --pdf "path/to/book.pdf" --artist "Artist Name" --book-name "Book Name"

# Monitor AWS execution
.\monitor-execution.ps1
```

## Current Status (January 25, 2026)

### ✅ Completed
- Full 6-stage processing pipeline implemented
- All AWS infrastructure deployed (CloudFormation)
- 6 ECS task definitions registered
- Docker image built and pushed to ECR
- Step Functions state machine with 10 states
- Lambda functions for orchestration
- DynamoDB ledger for state tracking
- TOC Discovery tested and working (98% confidence)
- Real TOC extraction validated (Billy Joel - 52nd Street)

### 🔧 In Progress
- End-to-end pipeline testing
- Bug fix: Added `S3Utils.read_bytes()` method
- Validating all 6 stages execute successfully

### 📋 Next Steps
1. Complete end-to-end test execution
2. Validate PDF splitting creates individual files
3. Process remaining 499 books
4. Add quality gates and error handling
5. Implement manual review workflow

---

## Architecture

```
S3 Input → Step Functions Pipeline → S3 Output
           ├─ Lambda (orchestration)
           ├─ ECS Fargate (processing)
           ├─ Textract (OCR)
           ├─ Bedrock (AI fallback)
           └─ DynamoDB (state)
```

### Processing Stages

1. **TOC Discovery** (ECS) - Find table of contents pages using Textract OCR
2. **TOC Parsing** (ECS) - Extract song titles and page numbers
3. **Page Mapping** (ECS) - Map TOC pages to actual PDF pages
4. **Song Verification** (ECS) - Verify songs start at expected pages
5. **PDF Splitting** (ECS) - Split into individual song PDFs
6. **Manifest Generation** (ECS) - Create processing manifest

---

## AWS Infrastructure

### Deployed Resources
- **S3 Buckets**: jsmith-input, jsmith-output, jsmith-artifacts
- **DynamoDB**: jsmith-processing-ledger
- **ECS Cluster**: jsmith-sheetmusic-splitter-cluster
- **ECS Tasks**: 6 task definitions (toc-discovery, toc-parser, page-mapper, song-verifier, pdf-splitter, manifest-generator)
- **Lambda**: 6 functions (ingest, check-processed, record-start/success/failure, manual-review)
- **Step Functions**: jsmith-sheetmusic-splitter-pipeline
- **ECR**: Docker image repository
- **CloudWatch**: Logs and alarms
- **IAM**: Roles for Lambda, ECS, Step Functions

### Configuration
- **Region**: us-east-1
- **Account**: 227027150061
- **VPC**: vpc-4c5f5735
- **Subnet**: subnet-0f6ba7ae50933273e
- **Docker Image**: 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest

---

## Project Structure

```
├── app/                          # Core application code
│   ├── models.py                 # Data models
│   ├── services/                 # Processing services
│   │   ├── toc_discovery.py      # ✅ WORKING
│   │   ├── toc_parser.py         # 🔧 TESTING
│   │   ├── page_mapper.py        # 🔧 TESTING
│   │   ├── song_verifier.py      # 🔧 TESTING
│   │   ├── pdf_splitter.py       # 🔧 TESTING
│   │   ├── manifest_generator.py # 🔧 TESTING
│   │   ├── bedrock_parser.py     # Bedrock fallback
│   │   └── quality_gates.py      # Quality enforcement
│   └── utils/                    # Utilities
│       ├── s3_utils.py           # S3 operations (read_bytes added)
│       ├── dynamodb_ledger.py    # DynamoDB operations
│       ├── sanitization.py       # Filename sanitization
│       ├── artist_resolution.py  # Artist name resolution
│       └── error_handling.py     # Error handling
├── lambda/                       # Lambda functions
│   ├── ingest_service.py         # PDF discovery
│   └── state_machine_helpers.py  # State management
├── ecs/                          # ECS task entry points
│   └── task_entrypoints.py       # All 6 task types
├── infra/                        # Infrastructure
│   ├── cloudformation_template.yaml
│   └── step_functions_complete.json
├── tests/                        # Tests (244/245 passing)
├── Dockerfile                    # ECS container
├── requirements.txt              # Dependencies
├── local_runner.py               # Local testing
├── deploy.ps1                    # Deploy CloudFormation
├── deploy-docker.ps1             # Build/push Docker
├── deploy-lambda.ps1             # Deploy Lambdas
└── monitor-execution.ps1         # Real-time monitoring
```

---

## Deployment

### Prerequisites
- AWS CLI configured
- Docker Desktop running
- Python 3.12
- PowerShell

### Deploy Everything

```powershell
# 1. Deploy infrastructure (one-time, ~15 minutes)
.\deploy.ps1

# 2. Build and push Docker image
.\deploy-docker.ps1

# 3. Deploy Lambda functions
.\deploy-lambda.ps1

# 4. Trigger execution
.\monitor-execution.ps1
```

### Update Code Only

```powershell
# Rebuild Docker image
.\deploy-docker.ps1

# Redeploy Lambdas
.\deploy-lambda.ps1
```

---

## Testing

### Local Testing
```bash
python local_runner.py \
  --pdf "SheetMusic/Billy Joel/books/Billy Joel - 52nd Street.pdf" \
  --artist "Billy Joel" \
  --book-name "52nd Street" \
  --output-dir "./test_output"
```

### AWS Testing
```powershell
# Start execution and monitor in real-time
.\monitor-execution.ps1

# Check specific execution
.\monitor-execution.ps1 -ExecutionArn "arn:aws:states:..."

# View logs
aws logs tail /aws/ecs/jsmith-sheetmusic-splitter --since 1h --format short

# Check DynamoDB
aws dynamodb get-item --table-name jsmith-processing-ledger --key '{"book_id":{"S":"book-id"}}'

# List S3 artifacts
aws s3 ls s3://jsmith-output/artifacts/book-id/ --recursive
```

---

## Monitoring

### CloudWatch Logs
- `/aws/ecs/jsmith-sheetmusic-splitter` - ECS task logs
- `/aws/lambda/jsmith-sheetmusic-splitter-*` - Lambda logs

### DynamoDB Queries
```bash
# Get all processing records
aws dynamodb scan --table-name jsmith-processing-ledger

# Get failed books
aws dynamodb query --table-name jsmith-processing-ledger \
  --index-name status-index \
  --key-condition-expression "status = :status" \
  --expression-attribute-values '{":status":{"S":"failed"}}'
```

### Step Functions Console
https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines

---

## Cost Analysis

### Per Book (~20 pages scanned, 9 songs)
- **Textract**: $0.030 (20 pages × $0.0015/page)
- **ECS Fargate**: $0.0135 (6 tasks × 1.5 min × $0.04048/hour)
- **Lambda**: $0.000005 (10 invocations)
- **Step Functions**: $0.000250 (10 transitions)
- **DynamoDB**: $0.000010 (8 writes)
- **S3**: $0.001 (storage + transfers)

**Total**: ~$0.045 per book

### For 500 Books
**Total**: ~$22.50 (well under $1,000 budget)

---

## Validated Results

### Test Execution: Billy Joel - 52nd Street
- **TOC Pages Found**: 2 (pages 1, 14)
- **Confidence**: 98.3% (page 1), 95.2% (page 14)
- **Songs Extracted**: 9 songs
  - Big Shot (page 10)
  - 52nd Street (page 68)
  - Half A Mile Away (page 52)
  - Honesty (page 19)
  - My Life (page 25)
  - Rosalinda's Eyes (page 46)
  - Stiletto (page 40)
  - Until The Night (page 60)
  - Zanzibar (page 33)

---

## Troubleshooting

### Common Issues

**ECS Task Fails with "No module named..."**
- Rebuild Docker image: `.\deploy-docker.ps1`
- Check CloudWatch logs for specific error

**Step Functions Fails with IAM Error**
- Check IAM roles have correct permissions
- Verify task definitions use correct role ARNs

**No TOC Found**
- Check if PDF has a table of contents
- Increase MAX_PAGES environment variable

**S3 Access Denied**
- Verify bucket names in environment variables
- Check IAM role policies

### Debug Commands
```powershell
# Get execution history
aws stepfunctions get-execution-history --execution-arn "arn:..." --query 'events[?type==`TaskFailed`]'

# Get ECS task logs
aws logs get-log-events --log-group-name "/aws/ecs/jsmith-sheetmusic-splitter" --log-stream-name "toc-discovery/toc-discovery/<task-id>"

# Check Docker image
aws ecr describe-images --repository-name jsmith-sheetmusic-splitter --region us-east-1
```

---

## Technical Details

### Dependencies
- **boto3**: AWS SDK
- **PyMuPDF**: PDF manipulation
- **Pillow**: Image processing
- **numpy**: Numerical operations
- **pytest**: Testing framework
- **hypothesis**: Property-based testing

### Python Version
- Python 3.12

### Docker Base Image
- python:3.12-slim

### System Dependencies
- poppler-utils (PDF rendering)
- qpdf (PDF manipulation)
- libgl1, libglib2.0-0 (image processing)

---

## Known Issues

1. **TOC Parsing**: Currently being tested with real AWS execution
2. **Page Mapping**: Needs validation with multiple books
3. **Quality Gates**: Not yet enforced
4. **Manual Review**: Workflow not implemented

---

## Future Enhancements

- [ ] Parallel processing of multiple books
- [ ] Web UI for monitoring and manual review
- [ ] Support for non-standard TOC formats
- [ ] Automatic artist name resolution from metadata
- [ ] Cost optimization (Spot instances, caching)
- [ ] Support for other document types (chord charts, lead sheets)

---

## License

MIT License

## Author

Built with AWS serverless technologies

## Support

For issues: Check CloudWatch logs and DynamoDB ledger for detailed error information
