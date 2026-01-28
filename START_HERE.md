# 🚀 START HERE - ALWAYS READ THIS FIRST

## Critical Information

**Project**: Sheet Music Book Splitter - AWS Serverless Pipeline
**Status**: PRODUCTION OPERATIONAL - 96.3% Complete (541/562 books processed)
**Last Updated**: 2026-01-28

## ⚠️ CRITICAL: Python Command

**ALWAYS use `py` not `python` or `python.exe`**
- ✅ Correct: `py script.py`
- ❌ Wrong: `python script.py`
- ❌ Wrong: `python.exe script.py`

This system uses `py.exe` launcher, not `python.exe` directly.

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

## 🎯 Current State (As of 2026-01-28)

### ✅ PRODUCTION OPERATIONAL - 96.3% COMPLETE

**Processing Statistics**:
- Total Source Books: 562
- Successfully Processed: 541 (96.3%)
- Remaining to Process: 21 (3.7%)
- Test Pass Rate: 99.6% (244/245 tests)

### What's Working
1. **DEPLOYED**: Full AWS infrastructure operational
2. **TESTED**: End-to-end pipeline validated with real books
3. **PROCESSED**: 541 books successfully split into individual songs
4. **VERIFIED**: Inventory reconciliation completed

### Remaining Work
1. Process final 15-20 books (2-3 hours)
2. Final verification and documentation
3. Git commit and project completion

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

- **PRODUCTION READY**: Pipeline successfully extracts all 9 songs with correct page boundaries
- **GROUND TRUTH VERIFIED**: All songs found at expected PDF indices
- **TOC CORRECTED**: 52nd Street is at TOC page 68, Until The Night is at TOC page 60
- **VISION IMPROVEMENTS**: Prompts filter out title pages and lyrics, require both title AND music
- **SONG VERIFIER FIX**: Now trusts page mapper's vision detection, requires BOTH staff lines AND title match
- **ALWAYS ASK USER** when there's a conflict between what they tell you and what you observe
- **ASSUME USER IS CORRECT** - they have ground truth information
- **PYTHON COMMAND**: Use `py` not `python` - this system has `py.exe` not `python.exe`
- **PDF INDEXING**: 0-based. page_000.png = PDF index 0 = 1st page
- **PAGE RANGE LOGIC**: Song contains all pages from its start index to (next song start index - 1)

## 🚨 Remember

1. **ALWAYS** read this file first when context switches
2. **ALWAYS** check `PROJECT_STATUS_DENSE.md` for complete technical state
3. **ALWAYS** verify what the user told you vs what you discovered
4. **NEVER** assume TOC page numbers are PDF indices
5. **NEVER** limit searches to arbitrary page ranges
