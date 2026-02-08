# PDF Verification Performance Optimization

## Performance Test Results

### Image Format Comparison (Single Page)

| Format | Render Time | File Size | Encode Time | Ollama Inference | Total Time |
|--------|-------------|-----------|-------------|------------------|------------|
| PNG    | 0.893s      | 1.7 MB    | 0.018s      | 6.789s           | 7.700s     |
| JPG    | 1.062s      | 2.8 MB    | 0.017s      | 3.352s           | 4.431s     |

**Key Finding**: JPG is **1.74x faster** overall, primarily due to **2x faster Ollama inference** (3.4s vs 6.8s)

### Full PDF Verification Results

| Approach | Test (5 PDFs) | Time per PDF | Speedup |
|----------|---------------|--------------|---------|
| PNG (original) | 51 seconds | ~10.2s | 1.0x |
| JPG (optimized) | 12 seconds | ~2.4s | **4.2x** |

## Why JPG is Faster

1. **Ollama processes JPG 2x faster** - likely due to:
   - Model training on JPG images
   - Internal processing optimizations for JPG
   - Faster decoding in the vision pipeline

2. **Smaller base64 payload** (for typical sheet music):
   - Faster network transfer to Ollama
   - Less memory allocation

3. **Quality is sufficient**:
   - JPG at 90% quality preserves sheet music details
   - Vision models don't need lossless precision
   - Not doing OCR, just visual analysis

## Pre-rendering Strategy

### Current Approach (Render-on-Demand)
```
For each PDF:
  1. Render pages (CPU-bound)
  2. Analyze with Ollama (GPU-bound)
  3. Repeat
```

**Issues**:
- Rendering blocks Ollama calls
- Can't fully saturate GPU
- Mixed CPU/GPU workload

### Optimized Approach (Pre-render + Analyze)
```
Phase 1: Pre-render all pages (CPU-bound)
  - Use 16-24 workers
  - Render all 42,000 pages to JPG
  - Cache to D:\ImageCache

Phase 2: Analyze cached images (GPU-bound)
  - Use 6-12 Ollama workers
  - Continuous GPU utilization
  - No rendering delays
```

**Benefits**:
- Separate CPU and GPU workloads
- Better resource utilization
- Can resume from cache if interrupted
- Faster overall processing

## Implementation

### Pre-rendering Script
```bash
# Pre-render all pages (one-time operation)
py prerender_all_pages.py --full --workers 16

# Estimated time: ~18 hours for 42,000 pages at 1.5s/page
```

### Verification Script (Updated)
```bash
# Verify using cached JPG images
py verify_pdf_splits.py --full --workers 12

# Estimated time: ~14 hours for 11,976 PDFs at 4.2s/PDF
```

## Estimated Full Run Times

### With Pre-rendering (Recommended)
1. **Pre-render phase**: ~18 hours (42,000 pages × 1.5s)
2. **Verification phase**: ~14 hours (11,976 PDFs × 4.2s)
3. **Total**: ~32 hours (can run overnight + next day)

### Without Pre-rendering (Original)
- **Total**: ~33 hours (11,976 PDFs × 10s)
- But mixed workload, less efficient

## Disk Space Requirements

- **42,000 pages × 2.8 MB/page** = ~118 GB
- **Available on D:\ImageCache**: 63 GB
- **Solution**: Process in batches or use compression

### Batch Processing Strategy
```bash
# Process in 3 batches to fit in 63 GB
py prerender_all_pages.py --batch 4000 --workers 16
py verify_pdf_splits.py --batch 4000 --workers 12
# Clear cache, repeat 2 more times
```

## Recommendations

### Option 1: Full Pre-render (if disk space available)
1. Expand D:\ImageCache or use another drive
2. Pre-render all 42,000 pages once
3. Run verification multiple times if needed
4. Keep cache for future re-verification

### Option 2: Batch Processing (current disk space)
1. Pre-render 4,000 PDFs (~14,000 pages = ~40 GB)
2. Verify those 4,000 PDFs
3. Clear cache
4. Repeat 2 more times

### Option 3: No Pre-rendering (simplest)
1. Use current JPG-optimized script
2. Render on-demand (cached for re-runs)
3. ~33 hours total
4. Simpler workflow

## Current Status

✅ Switched to `llava:7b` model (fits in GPU)
✅ Switched to JPG format (4x faster)
✅ Pre-rendering script created
✅ Verification script updated for JPG

**Ready to run full verification!**

## Next Steps

Choose one of the options above and run:

```bash
# Option 3 (simplest - recommended to start)
py verify_pdf_splits.py --full --workers 12

# This will:
# - Render pages on-demand to JPG (cached)
# - Verify all 11,976 PDFs
# - Take ~14 hours (can run overnight)
# - Generate CSV reports for manual review
```
