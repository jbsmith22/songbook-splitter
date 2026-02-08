# Auto-detect Songs Feature

## Overview

The review interface now includes an **"Auto-detect Songs"** button that uses Claude to automatically identify all songs in a PDF and their page ranges.

## Setup

### 1. Start the Backend Server

In a **separate terminal window**, run:

```powershell
.\start_review_server.ps1
```

Or manually:

```powershell
py split_detection_server.py
```

This starts a local server on `http://localhost:5000` that the review page will call.

**Keep this window open** while reviewing PDFs.

### 2. Open the Review Page

Open the review page in your browser as usual:

```
file:///C:/Work/AWSMusic/verification_results/review_page.html
```

## Usage

### Auto-detect Songs

1. Mark a PDF as **"Correct"**
2. Select error type: **"🔀 Missed split"** or **"📑 Multiple songs on same page"**
3. The split tool appears
4. Click **"🤖 Auto-detect Songs (uses Claude)"**
5. Wait ~10-30 seconds (depending on PDF size)
6. Claude will populate the song titles and page ranges
7. **Review and edit** the detected songs if needed
8. Click **"💾 Save Split Instructions"**

### Manual Entry

If you prefer to enter manually or the auto-detect doesn't work:

1. Fill in song titles and page ranges manually
2. Click **"+ Add Another Song"** to add more entries
3. Click **"💾 Save Split Instructions"**

## How It Works

When you click "Auto-detect Songs":

1. The browser sends all page images to the local server
2. Server calls AWS Bedrock (Claude 3.5 Sonnet)
3. Claude analyzes all pages and identifies:
   - Song titles
   - Page ranges for each song
   - Multiple songs on the same page
4. Results are populated into the form fields
5. You can edit before saving

## Cost

- Each auto-detect call costs ~$0.05-0.15 (depending on PDF size)
- Only use when needed for missed splits
- Manual entry is free

## Troubleshooting

### "Error detecting songs: Failed to fetch"

The server isn't running. Start it with:

```powershell
.\start_review_server.ps1
```

### "API request failed"

Check the server terminal for error messages. Make sure:
- AWS credentials are configured (`aws sso login --profile default`)
- Server is running on port 5000
- No firewall blocking localhost:5000

### Auto-detect is slow

This is normal. Claude needs to analyze all pages:
- 2-3 pages: ~10 seconds
- 5-10 pages: ~20-30 seconds
- 10+ pages: ~30-60 seconds

## Example Output

For a PDF with multiple songs, Claude might detect:

```
Song 1: "Jeopardy Theme"
Pages: 1-2

Song 2: "The Luckiest"  
Pages: 3-5

Song 3: "Brick"
Pages: 6-8
```

You can then edit these if needed before saving.

## Benefits

- **Faster**: No need to manually identify songs and count pages
- **Accurate**: Claude can read song titles even in complex layouts
- **Handles edge cases**: Detects multiple songs on same page
- **Editable**: You can fix any mistakes before saving

## When to Use

Use auto-detect for:
- ✅ Missed splits (multiple songs in one PDF)
- ✅ Multiple songs on same page
- ✅ Complex PDFs with many songs
- ✅ When you're unsure of exact page ranges

Use manual entry for:
- ✅ Simple 2-song splits
- ✅ When you already know the songs
- ✅ When server isn't available
