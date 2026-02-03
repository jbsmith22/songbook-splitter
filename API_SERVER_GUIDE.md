# Pipeline API Server - Quick Start Guide

## Overview

The Pipeline API Server bridges the provenance viewer and the AWS processing pipeline, allowing you to:
- Check book processing status from DynamoDB
- Verify S3 artifacts exist
- Trigger Step Functions reprocessing
- Manage manual split points
- All directly from the provenance viewer

## Setup

### 1. Install Dependencies

```bash
pip install flask flask-cors boto3
```

### 2. AWS Configuration

Make sure your AWS credentials are configured:
```bash
aws configure
```

Or set environment variables:
```bash
set AWS_ACCESS_KEY_ID=your_key
set AWS_SECRET_ACCESS_KEY=your_secret
set AWS_DEFAULT_REGION=us-east-1
```

### 3. Start the API Server

```bash
cd d:\Work\songbook-splitter
py scripts\pipeline_api_server.py
```

The server will start on http://localhost:5000

You should see:
```
================================================================================
Pipeline API Server
================================================================================
Starting server on http://localhost:5000

Endpoints:
  GET  /api/health
  GET  /api/status/<book_id>
  POST /api/reprocess
  GET  /api/execution/<execution_arn>
  GET  /api/check_artifacts/<book_id>
  GET/POST /api/manual_split/<book_id>

Open the provenance viewer to use action buttons
================================================================================
```

## Usage

### 1. Open the Provenance Viewer

Open [web/viewers/complete_provenance_viewer.html](web/viewers/complete_provenance_viewer.html) in your browser.

You should see a green banner at the top saying **"API Server: Connected"**.

If you see **"Not Connected"**, make sure the API server is running.

### 2. Action Buttons

Each row in the table has action buttons:

#### **Details**
- Shows full book information (same as before)
- View source PDF, DynamoDB, local files, TOC, manifest, etc.

#### **Status** (Green)
- Checks current processing status from DynamoDB
- Shows: processing status, songs extracted, duration
- Quick way to verify a book has been processed

#### **Artifacts** (Green)
- Checks which pipeline artifacts exist in S3
- Shows: toc_discovery.json, toc_parse.json, page_mapping.json, verified_songs.json, output_files.json, manifest.json
- Useful for debugging incomplete processing

#### **Reprocess** (Orange)
- Triggers Step Functions to reprocess the book
- Automatically detects manual split points in `data/manual_splits/{book_id}.json`
- Shows confirmation dialog before starting
- Returns execution ARN for tracking

#### **Edit Splits** (Purple)
- Opens the manual split point editor in a new tab
- Pre-loads the book ID and source PDF path
- Use this when TOC detection failed or split points are wrong

## Workflow Examples

### Example 1: Check Status of Incomplete Book

1. Filter viewer by "Status: Incomplete"
2. Find a book (e.g., "ACDC - Anthology")
3. Click **Status** button
4. See: "Status: completed, Songs: 3, Duration: 45s"
5. Note: TOC says 16 songs, but only 3 extracted

### Example 2: Verify Pipeline Artifacts

1. Click **Artifacts** button on the incomplete book
2. See which artifacts exist:
   - toc_discovery.json: exists
   - toc_parse.json: exists
   - page_mapping.json: missing
   - verified_songs.json: missing
3. Diagnosis: Pipeline failed during page mapping step

### Example 3: Reprocess with Manual Splits

1. Click **Edit Splits** button
2. Manual editor opens in new tab
3. Load source PDF
4. Enter book ID and load TOC
5. Adjust split points visually
6. Export JSON to `data/manual_splits/{book_id}.json`
7. Close editor, return to viewer
8. Click **Reprocess** button
9. See: "Reprocessing started! Using manual split points"
10. Wait for processing to complete (check DynamoDB or CloudWatch)
11. Run: `py scripts/analysis/finalize_provenance_with_song_matching.py`
12. Refresh viewer - book should now show 16/16 songs

### Example 4: Batch Reprocess Multiple Books

For reprocessing many books at once:

1. Use the viewer to identify incomplete books
2. Note their book IDs
3. Create a file `books_to_reprocess.txt` with one book ID per line
4. Run the batch script:
   ```bash
   py scripts\reprocessing\reprocess_book.py --from-file books_to_reprocess.txt
   ```

Note: The batch script currently shows a TODO message. To make it work with the API server, you would need to modify it to call the API endpoints instead of trying to trigger the pipeline directly.

## API Endpoints

### GET /api/health
Check if API server is running.

**Response:**
```json
{"status": "ok", "service": "pipeline-api"}
```

### GET /api/status/<book_id>
Get processing status from DynamoDB ledger.

**Response:**
```json
{
  "status": "found",
  "book_id": "abc123",
  "processing_status": "completed",
  "songs_extracted": 12,
  "processing_duration": 45.2
}
```

### GET /api/check_artifacts/<book_id>
Check which S3 artifacts exist.

**Response:**
```json
{
  "status": "success",
  "book_id": "abc123",
  "artifacts": {
    "toc_discovery.json": "exists",
    "toc_parse.json": "exists",
    "page_mapping.json": "missing",
    "verified_songs.json": "missing",
    "output_files.json": "missing",
    "manifest.json": "missing"
  }
}
```

### POST /api/reprocess
Trigger Step Functions reprocessing.

**Request:**
```json
{
  "book_id": "abc123",
  "source_pdf": "Artist/Artist - Album.pdf",
  "force": true
}
```

**Response:**
```json
{
  "status": "started",
  "execution_arn": "arn:aws:states:us-east-1:...:execution:...",
  "start_date": "2026-02-03T12:00:00",
  "use_manual_splits": true
}
```

### GET /api/manual_split/<book_id>
Load existing manual split points.

**Response:**
```json
{
  "book_id": "abc123",
  "total_pages": 100,
  "songs": [
    {
      "title": "Song Title",
      "start_page": 10,
      "end_page": 15,
      "page_count": 6,
      "source": "manual"
    }
  ]
}
```

### POST /api/manual_split/<book_id>
Save manual split points.

**Request:**
```json
{
  "book_id": "abc123",
  "total_pages": 100,
  "songs": [...]
}
```

**Response:**
```json
{
  "status": "saved",
  "path": "data/manual_splits/abc123.json"
}
```

## Troubleshooting

### "API Server: Not Connected"

**Problem:** Viewer shows red banner saying not connected.

**Solutions:**
1. Make sure API server is running: `py scripts/pipeline_api_server.py`
2. Check firewall isn't blocking localhost:5000
3. Try accessing http://localhost:5000/api/health directly in browser
4. Check browser console for CORS errors

### "Error checking status: Failed to fetch"

**Problem:** Clicking buttons shows fetch errors.

**Solutions:**
1. API server crashed - check the terminal
2. Restart API server
3. Check AWS credentials are valid: `aws sts get-caller-identity`

### "Book not found in processing ledger"

**Problem:** Status button says book not in DynamoDB.

**Explanation:** The book has never been processed through the pipeline. Either:
- It was processed before DynamoDB tracking was added
- Local files were created manually
- The book ID mapping is wrong

**Solution:** Use the Reprocess button to process it through the pipeline.

### Manual split points not being used

**Problem:** Reprocessed but still has wrong splits.

**Solutions:**
1. Verify JSON file exists: `data/manual_splits/{book_id}.json`
2. Check JSON format matches expected structure
3. Check reprocessing response says "use_manual_splits": true
4. View CloudWatch logs for the ECS task to see if splits were loaded

### Reprocessing not starting

**Problem:** Clicking Reprocess shows error.

**Solutions:**
1. Check STATE_MACHINE_ARN is correct in `scripts/pipeline_api_server.py`
2. Verify AWS credentials have stepfunctions:StartExecution permission
3. Check Step Functions state machine exists: `aws stepfunctions describe-state-machine --state-machine-arn "arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline"`

## Configuration

The API server configuration is at the top of [scripts/pipeline_api_server.py](scripts/pipeline_api_server.py):

```python
# Configuration
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'
```

Update these if your AWS resources have different names.

## Next Steps

1. **Test the integration**:
   - Start API server
   - Open viewer
   - Click buttons on a test book
   - Verify responses make sense

2. **Process incomplete books**:
   - Filter by Status: Incomplete
   - Review issues
   - Use Edit Splits for problem cases
   - Reprocess books
   - Rebuild provenance: `py scripts/analysis/finalize_provenance_with_song_matching.py`

3. **Monitor progress**:
   - Check DynamoDB table: `jsmith-processing-ledger`
   - Watch CloudWatch Logs for ECS tasks
   - View Step Functions executions in AWS Console
   - Refresh provenance viewer after processing completes

## Related Documentation

- [REPROCESSING_GUIDE.md](REPROCESSING_GUIDE.md) - Detailed guide for manual editor and reprocessing workflows
- [RECONCILIATION_PROJECT_OVERVIEW.md](RECONCILIATION_PROJECT_OVERVIEW.md) - Complete project overview
