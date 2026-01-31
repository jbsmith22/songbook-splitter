# AWS-Based PDF Verification Plan

## Overview

Use your existing AWS infrastructure with Claude 3.5 Sonnet (Bedrock) for much better accuracy and faster processing.

## Architecture

```
S3 Bucket (jsmith-output)
├── rendered_pages/           # Pre-rendered JPG images
│   ├── <artist>/<book>/<song>_page_<N>.jpg
│   └── ...
├── verification_input/       # Input manifests for Step Functions
│   └── pdf_manifest.json
└── verification_results/     # Output results
    ├── detailed_results.json
    └── flagged_pdfs.csv
```

## Step 1: Pre-render All Pages to S3

**Script**: `prerender_to_s3.py`

```python
# Render all 42,000 pages to JPG
# Upload to S3: s3://jsmith-output/rendered_pages/
# Generate manifest: list of all PDFs with their page paths
# Store in: s3://jsmith-output/verification_input/pdf_manifest.json
```

**Storage**:
- 42,000 pages × 2.8 MB = ~118 GB
- Use S:\SlowImageCache for local cache (slower but more space)
- Upload to S3 for Lambda access

**Time**: ~2-3 hours to render and upload

## Step 2: Lambda Function for Vision Analysis

**Function**: `pdf-verification-lambda`

**Input** (from Step Functions):
```json
{
  "pdf_path": "ProcessedSongs/Beatles/Abbey Road/Beatles - Come Together.pdf",
  "pages": [
    "s3://jsmith-output/rendered_pages/Beatles/Abbey Road/Beatles - Come Together_page_0.jpg",
    "s3://jsmith-output/rendered_pages/Beatles/Abbey Road/Beatles - Come Together_page_1.jpg"
  ]
}
```

**Process**:
1. Download images from S3
2. Call Bedrock (Claude 3.5 Sonnet) for each page
3. Analyze responses
4. Return result

**Output**:
```json
{
  "pdf_path": "...",
  "passed": false,
  "issues": ["Page 3 has new song starting"],
  "page_analyses": [...]
}
```

## Step 3: Step Functions Workflow

**State Machine**: `pdf-verification-workflow`

```
Start
  ↓
Read Manifest (S3)
  ↓
Map State (parallel processing)
  ├→ Lambda: Verify PDF 1
  ├→ Lambda: Verify PDF 2
  ├→ ... (up to 1000 concurrent)
  └→ Lambda: Verify PDF N
  ↓
Aggregate Results
  ↓
Write to S3
  ↓
End
```

**Concurrency**: 500-1000 concurrent executions
**Time**: ~30-60 minutes for all 11,976 PDFs

## Step 4: Results Processing

**Script**: `process_verification_results.py`

- Download results from S3
- Generate CSV with file:/// links to local cache
- Generate HTML report
- Filter to only flagged PDFs

## Cost Estimate

**Bedrock (Claude 3.5 Sonnet)**:
- Input: ~42,000 images × ~1,000 tokens = 42M tokens
- Output: ~42,000 responses × ~50 tokens = 2.1M tokens
- Cost: ~$126 input + ~$15 output = **~$141 total**

**Lambda**:
- 11,976 executions × ~10 seconds = ~33 hours compute
- Cost: **~$5**

**S3**:
- Storage: 118 GB × $0.023/GB = **~$3/month**
- Requests: Negligible

**Total**: ~$150 one-time cost

## Advantages Over Local Ollama

| Aspect | Local (llava:7b) | AWS (Claude 3.5) |
|--------|------------------|------------------|
| Accuracy | ~40% false positive | ~5-10% false positive (estimated) |
| Speed | ~7 hours | ~30-60 minutes |
| Cost | Free | ~$150 |
| Scalability | Limited by GPU | Unlimited parallel |
| Model Quality | Good | Excellent |

## Implementation Steps

### Phase 1: Pre-render (Local)
```bash
# Use S:\SlowImageCache for local storage
py prerender_to_s3.py --full --cache S:\SlowImageCache
```

### Phase 2: Deploy Lambda
```bash
# Package and deploy Lambda function
py deploy_verification_lambda.py
```

### Phase 3: Run Workflow
```bash
# Start Step Functions execution
py start_verification_workflow.py
```

### Phase 4: Download Results
```bash
# Download and process results
py download_verification_results.py
```

## Alternative: Hybrid Approach

**Use AWS for flagged PDFs only**:
1. Run local Ollama on all PDFs (free, ~7 hours)
2. Get ~7,000 flagged PDFs (60% false positive rate)
3. Re-verify those 7,000 with Claude on AWS (~$90)
4. Final result: ~350-700 truly flagged PDFs

**Cost**: ~$90 instead of $150
**Time**: ~8 hours total (7 local + 1 AWS)

## Recommendation

Given your AWS infrastructure and the accuracy issues with local models, I recommend:

**Option A**: Full AWS approach (~$150, best accuracy, fastest)
**Option B**: Hybrid approach (~$90, good accuracy, slower)
**Option C**: Continue with local Ollama (free, manual triage needed)

Which approach would you prefer?
