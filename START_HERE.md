# 🚀 START HERE - ALWAYS READ THIS FIRST

## Critical Information

**Project**: Sheet Music Book Splitter - AWS Serverless Pipeline
**Status**: ACTIVE DEVELOPMENT - Page Mapping Algorithm Fixed, Awaiting Test
**Last Updated**: 2026-01-25

## 📍 Where to Find Everything

### Most Important Files (Read These First)
1. **THIS FILE** - `START_HERE.md` - You're reading it now
2. **Dense Status** - `PROJECT_STATUS_DENSE.md` - Complete technical state
3. **Context File** - `PROJECT_CONTEXT.md` - High-level overview
4. **Current Issues** - `CURRENT_ISSUES.md` - Active problems and fixes

### Key Technical Files
- **Algorithm Fix**: `ALGORITHM_FIX_APPLIED.md` - Latest page mapping fix
- **Deployment**: `DEPLOYMENT_SUMMARY.md` - What was just deployed
- **Test Data**: `test-billy-joel.pdf` - Billy Joel 52nd Street (9 songs)

## 🎯 Current State (As of 2026-01-25)

### What Just Happened
1. **FIXED**: Page mapping algorithm - was only searching 20 pages, now searches entire PDF
2. **DEPLOYED**: New Docker image to ECR with fix
3. **READY**: Pipeline ready for new test execution

### What's Next
1. Run new pipeline execution
2. Verify all songs are found at correct indices
3. Download and verify extracted PDFs contain correct songs
4. Fix S3 path duplication bug (separate issue)

## 🔧 Quick Commands

### Run Pipeline Test
```powershell
aws stepfunctions start-execution `
  --state-machine-arn "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine" `
  --input (Get-Content test-execution-input.json -Raw)
```

### Check Execution Status
```powershell
aws stepfunctions describe-execution `
  --execution-arn "arn:aws:states:us-east-1:730335490735:execution:SheetMusicSplitterStateMachine:<execution-id>"
```

### Download Results
```powershell
aws s3 cp s3://jsmith-output/s3://jsmith-output/SheetMusicOut/Billy_Joel/books/52nd_Street/ test_output_aws_new/ --recursive
```

## 🏗️ Architecture

**6-Stage AWS Step Functions Pipeline**:
1. TOC Discovery (ECS) - Find table of contents pages
2. TOC Parser (ECS) - Extract song titles and page numbers using Bedrock vision
3. Page Mapper (ECS) - **JUST FIXED** - Find actual PDF indices for each song
4. Song Verifier (ECS) - Verify song start pages
5. PDF Splitter (ECS) - Extract individual song PDFs
6. Manifest Generator (ECS) - Create processing manifest

## 📊 Test Data

**Source PDF**: `test-billy-joel.pdf` (Billy Joel - 52nd Street)
- Total Pages: 59
- Songs: 9 (Big Shot, Honesty, My Life, Zanzibar, Stiletto, Rosalinda's Eyes, Half A Mile Away, 52nd Street, Until the Night)

**Known Facts**:
- Big Shot starts at PDF index 3 (TOC says page 10, offset = -7)
- TOC page numbers are printed page numbers, not PDF indices
- Algorithm must use vision to find each song's actual location

## 🐛 Known Issues

1. **S3 Path Duplication** - Keys have bucket name duplicated: `s3://jsmith-output/SheetMusicOut/...`
2. **Vision API Image Size** - Some pages exceed 5MB limit at 150 DPI (reduced to 72 DPI in page mapper)

## 📁 Repository Structure

```
AWSMusic/
├── START_HERE.md                    ← YOU ARE HERE
├── PROJECT_STATUS_DENSE.md          ← Complete technical state
├── PROJECT_CONTEXT.md               ← High-level overview
├── CURRENT_ISSUES.md                ← Active problems
├── app/                             ← Python application code
│   ├── services/                    ← Core services
│   │   ├── page_mapper.py          ← JUST FIXED
│   │   ├── pdf_splitter.py
│   │   ├── toc_discovery.py
│   │   ├── toc_parser.py
│   │   └── song_verifier.py
│   └── utils/                       ← Utility modules
├── ecs/                             ← ECS task entry points
├── lambda/                          ← Lambda functions
├── infra/                           ← CloudFormation & Step Functions
├── tests/                           ← Test suite
└── .kiro/specs/                     ← Feature specifications
```

## 🔑 AWS Resources

- **State Machine**: `SheetMusicSplitterStateMachine`
- **ECR Repository**: `227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter`
- **Input Bucket**: `jsmith-input`
- **Output Bucket**: `jsmith-output`
- **Region**: `us-east-1`

## 💡 Important Context

- User told me: "the first song starts on pdf index 3 NOT 8"
- User told me: "You should do a png conversion of EVERY page of EVERY pdf as a first step"
- The algorithm now searches the entire PDF for each song (no 20-page limit)
- Vision verification is critical for image-based PDFs with no text layer

## 🚨 Remember

1. **ALWAYS** read this file first when context switches
2. **ALWAYS** check `PROJECT_STATUS_DENSE.md` for complete technical state
3. **ALWAYS** verify what the user told you vs what you discovered
4. **NEVER** assume TOC page numbers are PDF indices
5. **NEVER** limit searches to arbitrary page ranges
