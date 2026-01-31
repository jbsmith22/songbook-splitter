# Project Status - Dense Technical Reference

**Last Updated**: 2026-01-25 15:30 EST
**Status**: Algorithm Fixed, Docker Deployed, Ready for Test

---

## Current Sprint: Page Mapping Algorithm Fix

### Completed (2026-01-25)
- ✅ Identified root cause: `max_search=20` parameter limiting search range
- ✅ Fixed `build_page_mapping()` to search entire PDF (`max_search=total_pages`)
- ✅ Rebuilt Docker image with fix
- ✅ Pushed to ECR: `227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest`
- ✅ Digest: `sha256:cf3aeeaf873dc09c4b9282a8bc787f2f2e66ca42451e9830bba2e536a683032f`

### In Progress
- ⏳ Awaiting new pipeline test execution
- ⏳ Need to verify all songs found at correct indices
- ⏳ Need to verify extracted PDFs contain correct songs

### Blocked/Pending
- 🔴 S3 path duplication bug (separate issue, not blocking)

---

## Technical State

### Page Mapping Algorithm (FIXED)

**Problem**: Algorithm only searched 20 pages forward from starting position, missing songs outside that range.

**Root Cause**: 
```python
# app/services/page_mapper.py line ~107
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages)
# _find_song_forward() has default max_search=20
```

**Fix Applied**:
```python
actual_pdf_index = self._find_song_forward(doc, entry.song_title, search_start, total_pages, max_search=total_pages)
```

**How It Works Now**:
1. First song: Search from index 0 through entire PDF
2. Subsequent songs: Start from expected position (based on TOC page diff), search up to total_pages forward
3. No arbitrary limits - will find songs anywhere in PDF

**Expected Behavior**:
- Big Shot (TOC page 10) → Find at PDF index 3 (offset -7)
- Honesty (TOC page 19) → Find at PDF index 12 (offset -7)
- My Life (TOC page 25) → Find at PDF index 18 (offset -7)
- etc.

### Test Data: Billy Joel - 52nd Street

**File**: `test-billy-joel.pdf`
**Total Pages**: 59
**Songs**: 9

**TOC Entries** (from Bedrock vision parsing):
```
Big Shot          - page 10
Honesty           - page 19
My Life           - page 25
Zanzibar          - page 33
Stiletto          - page 40
Rosalinda's Eyes  - page 46
Half A Mile Away  - page 52
52nd Street       - page 60
Until the Night   - page 68 (may be cut off)
```

**Known Facts** (from user):
- Big Shot actually starts at PDF index 3
- Offset = 3 - 10 = -7
- TOC page numbers are printed page numbers from the book
- Must use vision verification to find actual locations

### Previous Test Results

**Execution**: `2292b70a-ce66-4e48-b509-ac0540f61b99` (2026-01-25)
**Result**: 7 PDFs created, but WRONG content
- Big Shot PDF: ✅ Correct (first song found correctly)
- All others: ❌ Wrong (sequential calculation was incorrect)

**Why It Failed**:
- Algorithm found Big Shot at index 8 (should be 3)
- Used TOC page differences as song lengths
- Applied lengths sequentially instead of using simple offset

### AWS Infrastructure

**State Machine**: `SheetMusicSplitterStateMachine`
- ARN: `arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine`
- Definition: `infra/step_functions_complete.json`

**ECS Tasks** (all registered):
1. `sheetmusic-splitter-toc-discovery`
2. `sheetmusic-splitter-toc-parser`
3. `sheetmusic-splitter-page-mapper` ← JUST UPDATED
4. `sheetmusic-splitter-song-verifier`
5. `sheetmusic-splitter-pdf-splitter`
6. `sheetmusic-splitter-manifest-generator`

**ECR Image**:
- Repository: `jsmith-sheetmusic-splitter`
- Latest: `sha256:cf3aeeaf873dc09c4b9282a8bc787f2f2e66ca42451e9830bba2e536a683032f`
- Account: `227027150061`
- Region: `us-east-1`

**S3 Buckets**:
- Input: `jsmith-input`
- Output: `jsmith-output`

**Bedrock Model**: `anthropic.claude-3-sonnet-20240229-v1:0`

### Code Structure

**Core Services** (`app/services/`):
- `toc_discovery.py` - Find TOC pages using text patterns
- `bedrock_parser.py` - Parse TOC using Bedrock vision
- `page_mapper.py` - **FIXED** - Map TOC pages to PDF indices
- `song_verifier.py` - Verify song start pages
- `pdf_splitter.py` - Extract individual song PDFs
- `manifest_generator.py` - Generate processing manifest

**Utilities** (`app/utils/`):
- `s3_utils.py` - S3 operations with local mode support
- `sanitization.py` - Filename sanitization
- `artist_resolution.py` - Artist name normalization
- `dynamodb_ledger.py` - Processing ledger
- `error_handling.py` - Error handling utilities

**ECS Entry Points** (`ecs/task_entrypoints.py`):
- Single file with all 6 task entry points
- Each reads from S3, executes service, writes results

### Known Issues

#### 1. S3 Path Duplication (Low Priority)
**Symptom**: S3 keys have bucket name duplicated
- Actual: `s3://jsmith-output/SheetMusicOut/Billy Joel/...`
- Expected: `SheetMusicOut/Billy Joel/...`

**Location**: Likely in `s3_utils.py` `write_bytes()` method
**Impact**: Files are created but with wrong key structure
**Status**: Not blocking, needs investigation

#### 2. Vision API Image Size Limits
**Symptom**: Some pages exceed 5MB at 150 DPI
**Solution**: Reduced to 72 DPI in page mapper
**Status**: Resolved

### Testing Strategy

**Unit Tests**: `tests/unit/`
- Test individual service methods
- Mock S3 and Bedrock calls
- Run with: `pytest tests/unit/`

**Integration Tests**: Manual pipeline execution
- Use `test-execution-input.json`
- Monitor via Step Functions console
- Verify outputs in S3

**Verification Scripts** (created for debugging):
- `verify_extracted_pdfs.py` - Check extracted PDFs with vision
- `identify_extracted_pdfs.py` - Identify what's actually in PDFs
- `analyze_toc_and_pages.py` - Check source PDF pages
- `debug_page_mapping.py` - Debug page mapping logic
- `check_page_3.py` - Render specific page

### Git Status

**Branch**: main (assumed)
**Uncommitted Changes**:
- `app/services/page_mapper.py` - Algorithm fix
- Multiple analysis/debug files created
- Status documentation files

**Need to Commit**:
- Algorithm fix
- Updated documentation
- Clean up temporary debug files

### Next Actions

1. **Immediate**:
   - Run new pipeline test
   - Monitor CloudWatch logs for "Found first song" messages
   - Verify all songs found

2. **Verification**:
   - Download extracted PDFs
   - Use vision verification on first pages
   - Confirm correct song titles

3. **If Successful**:
   - Clean up debug/analysis files
   - Update main documentation
   - Commit and push to GitHub

4. **If Failed**:
   - Check CloudWatch logs for errors
   - Verify Docker image is being used (check task definition)
   - May need to force ECS to pull new image

### User Instructions/Corrections

**Critical User Feedback**:
1. "the first song starts on pdf index 3 NOT 8" - Algorithm was finding wrong index
2. "You should do a png conversion of EVERY page of EVERY pdf as a first step" - Need systematic scanning
3. "The TOC CAME FROM THIS EDITION" - TOC page numbers are printed pages, not offsets
4. "that is not the right question. The right question is why did you not find it the first time?" - Algorithm had 20-page search limit

**User's Correct Algorithm**:
1. Find first song's actual PDF index using vision
2. Calculate offset: actual_index - toc_page
3. Apply that offset to ALL TOC entries
4. Don't use TOC page differences as song lengths

### Performance Considerations

**Vision API Calls**:
- Cost: ~$0.003 per image (Claude Sonnet)
- 60-page PDF × 9 songs = up to 540 calls worst case
- Optimization: Start search from expected position to reduce calls

**ECS Task Duration**:
- TOC Discovery: ~30 seconds
- TOC Parser: ~60 seconds (vision calls)
- Page Mapper: ~120 seconds (vision calls for each song)
- Song Verifier: ~60 seconds
- PDF Splitter: ~30 seconds
- Manifest Generator: ~10 seconds
- **Total**: ~5-6 minutes per book

### Environment

**Local Development**:
- OS: Windows
- Shell: PowerShell
- Python: 3.12
- Docker: Desktop

**AWS Account**: 227027150061 (dev/test)
**AWS Region**: us-east-1

### Dependencies

**Python Packages** (requirements.txt):
- boto3 - AWS SDK
- PyMuPDF (fitz) - PDF manipulation
- Pillow - Image processing
- pytest - Testing
- hypothesis - Property-based testing

**AWS Services**:
- Step Functions - Orchestration
- ECS Fargate - Task execution
- ECR - Container registry
- S3 - Storage
- Bedrock - AI/ML (Claude Sonnet)
- CloudWatch - Logging

---

## Quick Reference Commands

### Deploy Docker Image
```powershell
docker build -t sheetmusic-splitter:latest .
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 227027150061.dkr.ecr.us-east-1.amazonaws.com
docker tag sheetmusic-splitter:latest 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest
docker push 227027150061.dkr.ecr.us-east-1.amazonaws.com/jsmith-sheetmusic-splitter:latest
```

### Run Pipeline
```powershell
aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-east-1:730335490735:stateMachine:SheetMusicSplitterStateMachine" --input (Get-Content test-execution-input.json -Raw)
```

### Check Logs
```powershell
aws logs tail /ecs/sheetmusic-splitter-page-mapper --follow
```

### Download Results
```powershell
aws s3 cp s3://jsmith-output/s3://jsmith-output/SheetMusicOut/Billy_Joel/books/52nd_Street/ test_output_aws_new/ --recursive
```

---

## File Locations

**Status Files**:
- `START_HERE.md` - Bootstrap file (read first)
- `PROJECT_STATUS_DENSE.md` - This file
- `PROJECT_CONTEXT.md` - High-level overview
- `CURRENT_ISSUES.md` - Active problems

**Algorithm Documentation**:
- `ALGORITHM_FIX_APPLIED.md` - Latest fix details
- `DEPLOYMENT_SUMMARY.md` - Deployment info
- `CORRECT_ALGORITHM.md` - Correct approach explanation
- `FIX_SUMMARY.md` - User's instructions
- `PAGE_MAPPING_ANALYSIS.md` - Problem analysis

**Specs**:
- `.kiro/specs/sheetmusic-book-splitter/requirements.md`
- `.kiro/specs/sheetmusic-book-splitter/design.md`
- `.kiro/specs/sheetmusic-book-splitter/tasks.md`
