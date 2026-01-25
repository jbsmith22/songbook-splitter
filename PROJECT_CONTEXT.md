# Project Context - Sheet Music Book Splitter

**Last Updated**: 2026-01-25 15:45 EST
**Status**: Algorithm Fixed, Docker Deployed, Ready for Test

---

## 🎯 Project Overview

Automated AWS serverless pipeline that splits sheet music book PDFs into individual song files using AI vision for table of contents parsing and song detection.

**Key Innovation**: Uses AWS Bedrock (Claude Sonnet) vision AI to parse image-based PDFs that have no text layer.

---

## 📊 Current Status

### Just Completed (2026-01-25)
- **Fixed page mapping algorithm** - Was only searching 20 pages, now searches entire PDF
- **Deployed new Docker image** to ECR
- **Ready for test execution** to verify fix

### What's Working
- ✅ TOC Discovery - Finds table of contents pages
- ✅ TOC Parser - Extracts song titles and page numbers using Bedrock vision
- ✅ Page Mapper - **JUST FIXED** - Now searches entire PDF for each song
- ✅ Song Verifier - Verifies song start pages
- ✅ PDF Splitter - Extracts individual song PDFs
- ✅ Manifest Generator - Creates processing manifest
- ✅ Full 6-stage pipeline deployed to AWS

### What Needs Testing
- 🔄 Verify page mapper finds all songs at correct indices
- 🔄 Verify extracted PDFs contain correct songs
- 🔄 End-to-end pipeline with fixed algorithm

### Known Issues
- 🐛 S3 path duplication (keys have bucket name duplicated) - Low priority

---

## 🏗️ Architecture

**6-Stage AWS Step Functions Pipeline**:

1. **TOC Discovery** (ECS Fargate)
   - Scans first 20 pages for table of contents
   - Uses text patterns and heuristics
   - Output: List of TOC page indices

2. **TOC Parser** (ECS Fargate)
   - Renders TOC pages as images
   - Uses Bedrock Claude Sonnet vision to extract song titles and page numbers
   - Output: List of TOCEntry objects

3. **Page Mapper** (ECS Fargate) ← **JUST FIXED**
   - Uses vision to find where each song actually starts in PDF
   - Searches entire PDF for each song (no arbitrary limits)
   - Output: Mapping of song titles to actual PDF indices

4. **Song Verifier** (ECS Fargate)
   - Verifies each song's start page using vision
   - Calculates page ranges (start/end for each song)
   - Output: Verified page ranges

5. **PDF Splitter** (ECS Fargate)
   - Extracts page ranges into individual PDFs
   - Preserves vector graphics and fonts
   - Output: Individual song PDF files in S3

6. **Manifest Generator** (ECS Fargate)
   - Creates processing manifest with metadata
   - Includes all intermediate results
   - Output: JSON manifest

---

## 🧪 Test Data

**Source**: `test-billy-joel.pdf` (Billy Joel - 52nd Street)
- **Total Pages**: 59
- **Songs**: 9
- **Format**: Image-based PDF (no text layer)

**TOC Entries**:
- Big Shot (page 10) → Actually at PDF index 3
- Honesty (page 19)
- My Life (page 25)
- Zanzibar (page 33)
- Stiletto (page 40)
- Rosalinda's Eyes (page 46)
- Half A Mile Away (page 52)
- 52nd Street (page 60)
- Until the Night (page 68)

**Key Insight**: TOC page numbers are printed page numbers from the book, NOT PDF indices. Offset = -7 for this book.

---

## 🔧 Technical Stack

**AWS Services**:
- Step Functions - Pipeline orchestration
- ECS Fargate - Containerized task execution
- ECR - Docker image registry
- S3 - Input/output storage
- Bedrock - AI vision (Claude Sonnet)
- CloudWatch - Logging and monitoring

**Languages & Frameworks**:
- Python 3.12
- PyMuPDF (fitz) - PDF manipulation
- Boto3 - AWS SDK
- Pillow - Image processing

**Infrastructure as Code**:
- CloudFormation templates
- Step Functions state machine JSON
- ECS task definitions

---

## 📁 Repository Structure

```
AWSMusic/
├── START_HERE.md                    ← Read this first!
├── PROJECT_STATUS_DENSE.md          ← Complete technical state
├── PROJECT_CONTEXT.md               ← This file
├── CURRENT_ISSUES.md                ← Active problems
├── app/
│   ├── services/                    ← Core business logic
│   │   ├── page_mapper.py          ← JUST FIXED
│   │   ├── pdf_splitter.py
│   │   ├── toc_discovery.py
│   │   ├── toc_parser.py
│   │   ├── song_verifier.py
│   │   └── bedrock_parser.py
│   ├── utils/                       ← Utilities
│   └── models.py                    ← Data models
├── ecs/
│   └── task_entrypoints.py          ← ECS task entry points
├── lambda/
│   └── ingest_service.py            ← Lambda functions
├── infra/
│   ├── cloudformation_template.yaml
│   └── step_functions_complete.json
├── tests/
│   └── unit/                        ← Unit tests
└── .kiro/specs/                     ← Feature specifications
```

---

## 🚀 Quick Start

### Run Pipeline Test
```powershell
aws stepfunctions start-execution `
  --state-machine-arn "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine" `
  --input (Get-Content test-execution-input.json -Raw)
```

### Monitor Execution
```powershell
# Get execution ARN from start-execution output, then:
aws stepfunctions describe-execution --execution-arn "<execution-arn>"
```

### Check Logs
```powershell
aws logs tail /ecs/sheetmusic-splitter-page-mapper --follow
```

### Download Results
```powershell
aws s3 ls s3://jsmith-output/ --recursive | Select-String "Billy"
aws s3 cp s3://jsmith-output/<path> ./test_output_aws_new/ --recursive
```

---

## 🎓 Key Learnings

### Page Mapping Algorithm
**Wrong Approach** (what we had):
- Find first song
- Use TOC page differences as song lengths
- Apply lengths sequentially

**Correct Approach** (what we have now):
- Find each song individually using vision
- Search entire PDF for each song (no 20-page limit)
- No assumptions about offset consistency

### Vision API Best Practices
- Reduce DPI to 72 to stay under 5MB limit
- Batch render all pages upfront for efficiency
- Start searches from expected positions to minimize API calls
- Always verify with vision for image-based PDFs

### AWS ECS Gotchas
- ECS may cache Docker images - need to force pull new image
- Task definitions need to be updated to use new image
- CloudWatch logs are essential for debugging

---

## 📈 Success Metrics

**Pipeline Success**:
- All songs found at correct PDF indices
- All extracted PDFs contain correct song titles
- No songs skipped or duplicated
- Processing time < 10 minutes per book

**Quality Gates**:
- TOC confidence > 0.8
- Page mapping confidence > 0.8
- Song verification success rate > 90%

---

## 🔗 Related Documentation

- `START_HERE.md` - Bootstrap file (always read first)
- `PROJECT_STATUS_DENSE.md` - Complete technical state
- `CURRENT_ISSUES.md` - Active problems and solutions
- `ALGORITHM_FIX_APPLIED.md` - Latest algorithm fix
- `DEPLOYMENT_SUMMARY.md` - Deployment details

---

## 👥 Team Context

**User Expertise**: Understands the domain deeply, provided critical corrections
**User Corrections**:
- "the first song starts on pdf index 3 NOT 8"
- "You should do a png conversion of EVERY page of EVERY pdf as a first step"
- "The TOC CAME FROM THIS EDITION" (page numbers are printed pages)
- "that is not the right question. The right question is why did you not find it the first time?"

**Development Approach**: Iterative, test-driven, user feedback is ground truth

---

## 🎯 Next Milestones

1. **Immediate**: Verify page mapping fix works correctly
2. **Short-term**: Fix S3 path duplication bug
3. **Medium-term**: Optimize vision API usage (reduce calls)
4. **Long-term**: Support multiple book formats and publishers
