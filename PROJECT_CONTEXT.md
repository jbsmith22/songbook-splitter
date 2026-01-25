# SheetMusic Book Splitter - Dense Context File for AI Sessions

**PURPOSE**: This file provides maximum information density for AI agents starting new sessions. Read this FIRST.

---

## CRITICAL STATUS (Jan 25, 2026)

**DEPLOYMENT**: ✅ COMPLETE - All AWS infrastructure operational
**TESTING**: 🔧 IN PROGRESS - TOC Discovery validated, full pipeline needs end-to-end test
**NEXT ACTION**: Run complete pipeline test with `.\monitor-execution.ps1`

---

## SYSTEM OVERVIEW

**What**: AWS serverless pipeline that splits sheet music compilation PDFs into individual song PDFs
**Input**: S3 bucket with PDFs at `SheetMusic/<Artist>/books/*.pdf`
**Output**: Individual song PDFs at `SheetMusicOut/<Artist>/books/<BookName>/<Artist>-<Song>.pdf`
**Scale**: 500 books, ~$22.50 total cost (well under $1,000 budget)

---

## ARCHITECTURE (6-STAGE PIPELINE)

```
S3 Input → Step Functions → 6 ECS Tasks → S3 Output
           ├─ Lambda (orchestration)
           ├─ Textract (OCR)
           ├─ Bedrock (AI fallback)
           └─ DynamoDB (state tracking)
```

**Stages**:
1. **TOC Discovery** (ECS) - Render pages, Textract OCR, score TOC likelihood → ✅ WORKING (98% confidence)
2. **TOC Parsing** (ECS) - Extract song titles + page numbers (deterministic + Bedrock fallback) → 🔧 TESTING
3. **Page Mapping** (ECS) - Calculate offset between printed pages and PDF indices → 🔧 TESTING
4. **Song Verification** (ECS) - Verify song starts (staff lines + title match) → 🔧 TESTING
5. **PDF Splitting** (ECS) - Extract page ranges, create individual PDFs → 🔧 TESTING
6. **Manifest Generation** (ECS) - Create audit manifest with metadata → 🔧 TESTING

---

## AWS RESOURCES (us-east-1, Account: 227027150061)

**S3**: jsmith-input, jsmith-output, jsmith-artifacts
**DynamoDB**: jsmith-processing-ledger (book_id PK, processing_timestamp SK)
**ECS Cluster**: jsmith-sheetmusic-splitter-cluster
**ECS Tasks**: 6 definitions (toc-discovery:2, toc-parser:2, page-mapper:2, song-verifier:2, pdf-splitter:2, manifest-generator:2)
**Lambda**: 6 functions (ingest, check-processed, record-start, record-success, record-failure, manual-review)
**Step Functions**: jsmith-sheetmusic-splitter-pipeline (10 states)
**ECR**: 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest
**VPC**: vpc-4c5f5735, Subnet: subnet-0f6ba7ae50933273e

---

## VALIDATED RESULTS

**Test**: Billy Joel - 52nd Street
**TOC Pages**: 2 (pages 1, 14) with 98.3% and 95.2% confidence
**Songs Extracted**: 9 songs (Big Shot, 52nd Street, Half A Mile Away, Honesty, My Life, Rosalinda's Eyes, Stiletto, Until The Night, Zanzibar)
**Status**: TOC Discovery stage fully validated with real PDF

---

## KEY FILES

**Entry Points**:
- `ecs/task_entrypoints.py` - All 6 ECS task entry points
- `lambda/ingest_service.py` - PDF discovery Lambda
- `lambda/state_machine_helpers.py` - State management Lambdas
- `app/main.py` - ECS task dispatcher

**Core Services** (`app/services/`):
- `toc_discovery.py` - Render pages, Textract, scoring (✅ WORKING)
- `toc_parser.py` - Deterministic + Bedrock parsing
- `page_mapper.py` - Offset calculation
- `song_verifier.py` - Staff line detection + title matching
- `pdf_splitter.py` - PyMuPDF page extraction
- `manifest_generator.py` - Audit manifest creation
- `bedrock_parser.py` - Claude fallback for TOC parsing
- `quality_gates.py` - Quality enforcement (≥10 entries, ≥95% verification, ≥90% output)

**Utilities** (`app/utils/`):
- `s3_utils.py` - S3 operations (read_bytes, write_bytes, list_files)
- `dynamodb_ledger.py` - State tracking (check_processed, record_start, record_complete)
- `sanitization.py` - Filename sanitization (Windows + S3 safe)
- `artist_resolution.py` - Artist name normalization + Various Artists handling
- `error_handling.py` - Retry logic, error context capture
- `cloudwatch_utils.py` - Metrics + structured logging

**Infrastructure**:
- `infra/cloudformation_template.yaml` - All AWS resources
- `infra/step_functions_complete.json` - 10-state workflow
- `Dockerfile` - Python 3.12 + PyMuPDF + dependencies
- `requirements.txt` - boto3, PyMuPDF, Pillow, numpy, pytest, hypothesis

**Deployment Scripts**:
- `deploy.ps1` - Deploy CloudFormation stack (~15 min)
- `deploy-docker.ps1` - Build + push Docker image to ECR
- `deploy-lambda.ps1` - Package + deploy Lambda functions
- `monitor-execution.ps1` - Real-time Step Functions monitoring (polls every 3s)

**Testing**:
- `local_runner.py` - Local testing with mock AWS services
- `tests/unit/` - 244/245 tests passing
- `test-execution-input.json` - Test input (book_id: "complete-success")

---

## CRITICAL BUG FIXES (COMPLETED)

1. **Docker Dependencies**: Added Pillow, numpy to requirements.txt
2. **Lambda DynamoDB**: Convert floats to Decimal for DynamoDB writes
3. **S3Utils Missing Method**: Added `read_bytes()` method to `app/utils/s3_utils.py`
4. **IAM Permissions**: Step Functions role needed PassRole permission
5. **Task Entry Points**: All 6 tasks load data from S3 artifacts

**Latest Docker Image**: sha256:020fab651873c87b483af1973bab8c14fb5a8ec7c4552e91d281a988c5675234 (has all fixes)

---

## DATA FLOW

1. **Ingest**: Lambda scans S3, checks DynamoDB ledger, starts Step Functions execution
2. **TOC Discovery**: ECS renders pages → Textract OCR → score TOC likelihood → save to S3 (`toc_discovery.json`)
3. **TOC Parsing**: ECS loads discovery results → deterministic parse (or Bedrock fallback) → save to S3 (`toc_parse.json`)
4. **Page Mapping**: ECS loads TOC parse → sample entries → calculate offset → save to S3 (`page_mapping.json`)
5. **Song Verification**: ECS loads page mapping → verify staff lines + titles → adjust if needed → save to S3 (`verified_songs.json`)
6. **PDF Splitting**: ECS loads verified songs → extract page ranges → create individual PDFs → save to S3 output bucket → save list to S3 (`output_files.json`)
7. **Manifest**: ECS aggregates all artifacts → create manifest.json → save to S3 → update DynamoDB ledger

**S3 Artifact Paths**:
- `s3://jsmith-artifacts/<book_id>/toc_discovery.json`
- `s3://jsmith-artifacts/<book_id>/toc_parse.json`
- `s3://jsmith-artifacts/<book_id>/page_mapping.json`
- `s3://jsmith-artifacts/<book_id>/verified_songs.json`
- `s3://jsmith-artifacts/<book_id>/output_files.json`
- `s3://jsmith-artifacts/<book_id>/manifest.json`

---

## SPEC LOCATION

**Spec Directory**: `.kiro/specs/sheetmusic-book-splitter/`
- `requirements.md` - 15 requirements with acceptance criteria
- `design.md` - Architecture, components, 33 correctness properties
- `tasks.md` - 31 tasks (7 completed, 24 remaining)

**Key Requirements**:
- R1: S3 input/output management
- R2: TOC discovery and extraction
- R3: TOC parsing with Bedrock fallback
- R4: Page number mapping (offset calculation)
- R5: Song start verification (staff lines + title match)
- R6: PDF splitting with vector preservation
- R7: Manifest and auditability
- R8: Cost control ($1,000 budget)
- R9: Orchestration and state management (idempotency)
- R10: Quality gates (≥10 entries, ≥95% verification, ≥90% output)

**Correctness Properties**: 33 properties for property-based testing with Hypothesis
- Property 1: S3 pattern matching
- Property 2: Output path format compliance
- Property 3: Artist override resolution
- Property 4: Vector content preservation
- Property 5: TOC page scoring accuracy
- ... (see design.md for all 33)

---

## TESTING STRATEGY

**Unit Tests**: Specific examples, edge cases, AWS integration (244/245 passing)
**Property Tests**: Hypothesis with 100 iterations per property (optional tasks marked with `*`)
**Integration Tests**: End-to-end with LocalStack or mocked AWS
**Local Mode**: `local_runner.py` with mock Textract/Bedrock/DynamoDB

---

## COMMANDS

**Deploy**:
```powershell
.\deploy.ps1                    # CloudFormation (~15 min)
.\deploy-docker.ps1             # Build + push Docker
.\deploy-lambda.ps1             # Deploy Lambdas
```

**Test**:
```powershell
.\monitor-execution.ps1         # Real-time monitoring (polls every 3s)
python local_runner.py --pdf "path/to/book.pdf" --artist "Artist" --book-name "Book"
```

**Debug**:
```powershell
aws logs tail /aws/ecs/jsmith-sheetmusic-splitter --since 1h --format short
aws stepfunctions get-execution-history --execution-arn "arn:..."
aws dynamodb get-item --table-name jsmith-processing-ledger --key '{"book_id":{"S":"book-id"}}'
aws s3 ls s3://jsmith-output/artifacts/book-id/ --recursive
```

---

## COST BREAKDOWN (Per Book)

- Textract: $0.030 (20 pages × $0.0015/page)
- ECS Fargate: $0.0135 (6 tasks × 1.5 min × $0.04048/hour)
- Lambda: $0.000005 (10 invocations)
- Step Functions: $0.000250 (10 transitions)
- DynamoDB: $0.000010 (8 writes)
- S3: $0.001 (storage + transfers)

**Total**: ~$0.045/book × 500 books = ~$22.50 (well under $1,000 budget)

---

## KNOWN ISSUES

1. **Full Pipeline**: Not yet tested end-to-end (TOC Discovery validated only)
2. **Quality Gates**: Not yet enforced in Step Functions
3. **Manual Review**: Workflow not implemented
4. **Parallel Processing**: Not yet configured

---

## NEXT IMMEDIATE ACTIONS

1. ✅ Create this context file
2. ⏳ Run `.\monitor-execution.ps1` to test complete pipeline
3. ⏳ Validate all 6 stages execute successfully
4. ⏳ Check S3 artifacts created for all stages
5. ⏳ Verify individual song PDFs created
6. ⏳ Commit to GitHub

---

## TROUBLESHOOTING

**ECS Task Fails**: Check CloudWatch logs `/aws/ecs/jsmith-sheetmusic-splitter`
**IAM Error**: Verify roles have correct permissions (PassRole for Step Functions)
**No TOC Found**: Increase MAX_PAGES env var or check PDF has TOC
**S3 Access Denied**: Verify bucket names in env vars, check IAM policies
**Module Not Found**: Rebuild Docker image with `.\deploy-docker.ps1`

---

## DEPENDENCIES

**Python**: 3.12
**Key Libraries**: boto3 (AWS SDK), PyMuPDF (PDF manipulation), Pillow (image processing), numpy (numerical ops), pytest (testing), hypothesis (property-based testing)
**System**: poppler-utils (PDF rendering), qpdf (PDF manipulation), libgl1, libglib2.0-0 (image processing)

---

## CONFIGURATION

**Environment Variables** (set in ECS task definitions):
- `INPUT_BUCKET=jsmith-input`
- `OUTPUT_BUCKET=jsmith-output`
- `ARTIFACTS_BUCKET=jsmith-artifacts`
- `LEDGER_TABLE=jsmith-processing-ledger`
- `MAX_PAGES=20` (TOC discovery)
- `MIN_TOC_ENTRIES=10` (quality gate)
- `VERIFICATION_THRESHOLD=0.95` (quality gate)
- `OUTPUT_THRESHOLD=0.90` (quality gate)

---

## MONITORING

**CloudWatch Logs**:
- `/aws/ecs/jsmith-sheetmusic-splitter` - ECS tasks
- `/aws/lambda/jsmith-sheetmusic-splitter-*` - Lambdas

**DynamoDB Ledger Schema**:
- PK: `book_id` (String) - hash of S3 URI
- SK: `processing_timestamp` (Number) - Unix timestamp
- Attributes: status ("processing"|"success"|"failed"|"manual_review"), source_pdf_uri, artist, book_name, step_function_execution_arn, error_message, manifest_uri, songs_extracted, processing_duration_seconds, cost_usd

**Step Functions Console**: https://console.aws.amazon.com/states/home?region=us-east-1#/statemachines

---

## DESIGN PATTERNS

**Graceful Degradation**: Deterministic parsing → Bedrock fallback → fail
**Retry Logic**: Exponential backoff (30s, 60s, 120s) for transient AWS errors
**Error Context**: Capture stack trace, execution ARN, stage, timestamp
**Quality Gates**: Validate at 3 checkpoints (post-TOC, post-verification, post-splitting)
**Idempotency**: Check DynamoDB ledger before processing
**Auditability**: Save all intermediate artifacts to S3

---

## FILE STRUCTURE

```
├── .kiro/specs/sheetmusic-book-splitter/  # Spec files
├── app/                                    # Core application
│   ├── main.py                             # ECS dispatcher
│   ├── models.py                           # Data models
│   ├── services/                           # 6 processing services
│   └── utils/                              # Utilities
├── lambda/                                 # Lambda functions
├── ecs/                                    # ECS entry points
├── infra/                                  # Infrastructure
├── tests/                                  # Tests (244/245 passing)
├── Dockerfile                              # ECS container
├── requirements.txt                        # Dependencies
├── deploy*.ps1                             # Deployment scripts
├── monitor-execution.ps1                   # Real-time monitoring
└── local_runner.py                         # Local testing
```

---

## CONTEXT TRANSFER NOTES

**Previous Session Summary**:
- Deployed complete AWS infrastructure
- Fixed Docker dependencies (Pillow, numpy)
- Fixed Lambda DynamoDB float→Decimal conversion
- Added missing `S3Utils.read_bytes()` method
- Registered all 6 ECS task definitions (version :2)
- Updated Step Functions to use task definition :2
- Created real-time monitoring script
- Validated TOC Discovery with Billy Joel PDF (9 songs, 98% confidence)
- Updated README.md with current status
- Ready for end-to-end pipeline test

**User Queries**:
1. "what is the complete readout of the current state of the project?"
2. "can we run this with a test file?"
3. "do it" (expand pipeline to full 6 stages)
4. "2 hours isn't enough. Look back 5 hours"
5. "I don't like a 7 minute sleep in there. Can't we do this realtime?"
6. "what are we monitoring right now?"
7. "what are we doing right now?"

---

**END OF CONTEXT FILE**
