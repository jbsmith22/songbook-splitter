# Test Executions Status

## Deployment Summary
- **Docker Image**: `sha256:251717e5a015eebdb48665bfdae88f364bf323b84b9ff41370fbf4495955a2c5`
- **Task Definition**: `jsmith-page-mapper:3`
- **State Machine**: Updated with new task definition
- **Deployment Time**: 2026-01-26 01:32 EST

## Changes Deployed
1. ✅ TOC artist names used preferentially over vision-extracted names
2. ✅ New directory structure: `<Artist>/<BookName>/Songs/<Artist> - <Song>.pdf`
3. ✅ Title Case formatting for all names
4. ✅ Space-dash-space filename format
5. ✅ "Unknown Artist" for missing artists

## Test Executions

### Test 1: Various Artists - Classic Rock (73 songs)
- **Status**: ✅ SUCCEEDED (Skipped - Already Processed)
- **Execution ARN**: `arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:ef03a7a5-1421-49ba-9960-5866111cc714`
- **Start Time**: 2026-01-26 01:32:28 EST
- **Result**: Deduplication detected previous processing, skipped execution
- **Note**: This book was processed in the previous run, so the new formatting was not applied

### Test 2: Various Artists - Great Bands Of The 70s
- **Status**: 🟡 RUNNING
- **Execution ARN**: `arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:de25c80d-09d8-4706-94be-132ba5069faa`
- **Start Time**: 2026-01-26 01:35:23 EST
- **Book ID**: `various-artists-great-bands-70s`
- **Source**: `s3://jsmith-input/SheetMusic/Various Artists/books/Various Artists - Great Bands Of The 70s [PVG Book].pdf`
- **Expected Output**: Files with new directory structure and Title Case formatting
- **Monitor Script**: `monitor-great-bands-70s.ps1`

## Expected Results for Test 2

### Directory Structure
```
Various Artists/
└── Great Bands Of The 70s/
    └── Songs/
        ├── <Artist> - <Song Title>.pdf
        ├── <Artist> - <Song Title>.pdf
        └── ...
```

### Example Filenames (Expected)
- `Heart - Barracuda.pdf`
- `The Eagles - Hotel California.pdf`
- `Fleetwood Mac - Dreams.pdf`
- `Boston - More Than A Feeling.pdf`

### What's Different from Previous Runs
1. **Artist Names**: Should show performer names (e.g., "Heart") not composer names (e.g., "Billy Steinberg And Tom Kelly")
2. **Capitalization**: Title Case (e.g., "Hotel California" not "HOTEL CALIFORNIA")
3. **Directory**: No nested artist folders, no "books" folder, no "SheetMusicOut" prefix
4. **Filename Format**: Space-dash-space separator (e.g., "Heart - Barracuda.pdf")

## Monitoring

### Check Execution Status
```powershell
# Run the monitoring script
.\monitor-great-bands-70s.ps1

# Or check manually
aws stepfunctions describe-execution --execution-arn "arn:aws:states:us-east-1:227027150061:execution:jsmith-sheetmusic-splitter-pipeline:de25c80d-09d8-4706-94be-132ba5069faa" --region us-east-1
```

### Download Results (After Completion)
```powershell
# Create output directory
mkdir great_bands_70s_output

# Download all songs
aws s3 sync "s3://jsmith-output/Various Artists/Great Bands Of The 70s/Songs/" ./great_bands_70s_output/songs/ --region us-east-1

# List files to verify formatting
ls ./great_bands_70s_output/songs/
```

### View CloudWatch Logs
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:log-groups/log-group/$252Faws$252Fecs$252Fjsmith-sheetmusic-splitter
```

## Notes

### Challenging TOC
The "Great Bands Of The 70s" book has a particularly challenging table of contents, which makes it a good test case for:
- Complex TOC parsing
- Artist name extraction from TOC
- Fallback vision scanning with TOC artist lookup
- Handling various formatting styles

### Deduplication
The system includes deduplication to avoid reprocessing books. To reprocess a book with new code:
1. Delete the processing record from DynamoDB, or
2. Use a different book_id, or
3. Process a book that hasn't been processed before (like Test 2)
