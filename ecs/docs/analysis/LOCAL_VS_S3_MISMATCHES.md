# Local vs S3 Mismatches

## Summary
- **Local folders:** 559
- **Matched to S3:** 547 (97.9%)
- **NO MATCH in S3:** 12 folders

## 12 Local Folders WITHOUT S3 Match

These local folders don't have corresponding folders in S3:

1. **Elton John/Elton John - Songs From The West Coast** (3 PDFs)
2. **Elton John/Elton John - The Big Picture** (3 PDFs)
3. **Fray/Fray - How To Save A Life _Book_** (3 PDFs)
4. **Meatloaf/MeatLoaf - Bat Out Of Hell** (3 PDFs)
5. **Various Artists/Various Artists - 50s And 60s** (81 PDFs)
6. **Various Artists/Various Artists - Biggest Pop Hits 1996-1997** (36 PDFs)
7. **_broadway Shows/Various Artists - Legally Blonde - score** (1 PDF)
8. **_broadway Shows/Various Artists - Little Shop Of Horrors Script** (2 PDFs)
9. **_broadway Shows/Various Artists - Little Shop Of Horrors _Broadway_** (2 PDFs)
10. **_broadway Shows/Various Artists - Little Shop Of Horrors _original_** (2 PDFs)
11. **_movie And Tv/Disney Collection _Songs Out Of order_** (42 PDFs)
12. **_movie And Tv/Various Artists - 100 Of The Best Movie Songs Ever** (101 PDFs)

**Total PDFs in unmatched folders:** 279 PDFs

## Analysis

### Little Shop Of Horrors (3 folders, 6 PDFs total)
- `Little Shop Of Horrors Script` (2 PDFs)
- `Little Shop Of Horrors _Broadway_` (2 PDFs)
- `Little Shop Of Horrors _original_` (2 PDFs)

**Note:** We also have `Little Shop Of Horrors (original)` (2 PDFs) which DOES match S3.

**Issue:** Multiple versions of the same show. Need to determine which are duplicates.

### Elton John (2 folders, 6 PDFs)
- `Songs From The West Coast` (3 PDFs)
- `The Big Picture` (3 PDFs)

**Action:** These need to be uploaded to S3 or verified if they exist under different names.

### Large Collections (2 folders, 182 PDFs)
- `Various Artists - 50s And 60s` (81 PDFs)
- `Various Artists - 100 Of The Best Movie Songs Ever` (101 PDFs)

**Action:** These are significant collections that should be in S3. Need to verify.

### Other Missing (5 folders, 85 PDFs)
- `Fray - How To Save A Life _Book_` (3 PDFs)
- `MeatLoaf - Bat Out Of Hell` (3 PDFs)
- `Various Artists - Biggest Pop Hits 1996-1997` (36 PDFs)
- `Legally Blonde - score` (1 PDF)
- `Disney Collection _Songs Out Of order_` (42 PDFs)

## Recommendations

1. **Little Shop Of Horrors:** Compare the 4 versions (Script, Broadway, original x2) to see if they're duplicates
2. **Large collections:** Verify if these exist in S3 under different names
3. **Elton John:** Check if these albums exist in S3 under different names
4. **Others:** Determine if these should be uploaded to S3 or if they're duplicates of existing S3 folders

## Next Steps

Would you like me to:
1. Check if any of these 12 exist in S3 under different names (fuzzy matching)?
2. Compare the Little Shop Of Horrors versions to identify duplicates?
3. Create a list of folders to upload to S3?
