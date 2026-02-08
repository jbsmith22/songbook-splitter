# Concurrency Update - January 26, 2026

## Why Increase Concurrency?

You're absolutely correct that:
1. **Cost is proportional to total work, not concurrency** - Processing 566 books costs the same whether we do 3 at a time or 20 at a time
2. **Fargate charges per vCPU-second and GB-second** - Running 20 tasks for 5 minutes costs the same as running 3 tasks for 33 minutes
3. **Faster completion is better** - No reason to artificially limit concurrency

## Changes Made

Updated default `MaxConcurrent` from 3 to 20 in:
- `process-all-books.ps1`
- `process-and-download-all.ps1`

## Current Status

- **Currently running script**: Still using MaxConcurrent=3 (started before the change)
- **Books completed**: 296 out of 566
- **Books remaining**: 265
- **Current running**: 3 executions

## Estimated Completion Time

With 3 concurrent:
- Average time per book: ~5-10 minutes
- 265 books / 3 concurrent = ~88 batches
- Total time: 88 * 7 minutes = ~10 hours

With 20 concurrent (for future runs):
- 265 books / 20 concurrent = ~14 batches  
- Total time: 14 * 7 minutes = ~1.6 hours

## Recommendation for Current Run

The current batch script is running fine with 3 concurrent and has already processed 296 books successfully. Since:
1. It's working correctly with the fixed code
2. Stopping and restarting might cause issues
3. It will complete overnight anyway

**Recommendation**: Let it continue. The next time you run the script, it will use MaxConcurrent=20 by default.

## For Future Runs

To process with higher concurrency:
```powershell
.\process-and-download-all.ps1 -MaxConcurrent 20
```

Or even higher if desired:
```powershell
.\process-and-download-all.ps1 -MaxConcurrent 50
```

## AWS Limits to Consider

- **Step Functions**: 1,000 concurrent executions per account (we're nowhere near this)
- **Fargate**: Default limit is 1,000 concurrent tasks per region (we're fine)
- **Bedrock**: Rate limits on Claude API calls (this is the real bottleneck)

The Bedrock rate limit is probably the main constraint. With 20 concurrent executions, we'd be making ~60-100 Bedrock API calls per minute, which should be well within limits.
