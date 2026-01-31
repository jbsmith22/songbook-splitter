# S3-to-Local Match Review Summary

**Date:** January 30, 2026  
**Status:** Ready for Manual Review

## Overview

We've matched 563 local books to S3 folders by comparing file contents. The matching algorithm found excellent matches for most books, but some need manual confirmation.

## Match Quality Breakdown

| Quality | Count | Description | Action Needed |
|---------|-------|-------------|---------------|
| **PERFECT** | 430 | 100% file match | ✅ Confirmed - No review needed |
| **EXCELLENT** | 7 | 95-99% match | ⚠️ Review - Likely correct |
| **GOOD** | 31 | 80-95% match | ⚠️ Review - May be correct |
| **PARTIAL** | 59 | 50-80% match | ❌ Review - Likely wrong |
| **POOR** | 28 | <50% match | ❌ Review - Definitely wrong |
| **NO MATCH** | 8 | No S3 folder found | ❌ Find correct folder |
| **TOTAL** | **563** | | |

**Needs Review:** 133 books (24%)  
**Confirmed:** 430 books (76%)

## Files Generated

### 1. `matches_confirmed.csv` (430 books)
Perfect matches that are confirmed correct. No review needed.

### 2. `matches_need_review.csv` (133 books)
Books that need manual review and confirmation. Contains:
- All EXCELLENT, GOOD, PARTIAL, POOR, and NO MATCH books
- Columns: local_artist, local_book, s3_artist, s3_book, match_quality, status, notes

**Instructions:**
1. Review each row
2. Verify the S3 match is correct
3. Update `status` to `CONFIRMED` when verified
4. Update `s3_artist` and `s3_book` if you find a better match
5. Add notes if needed

### 3. `missing_books_candidates.csv` (95 books)
Books with PARTIAL, POOR, or NO MATCH quality, with suggested S3 candidates.

**Instructions:**
1. Review the top 3 candidates for each book
2. Select the correct match in `selected_match` column
3. Format: `Artist/Book Name`
4. Add notes if needed

## Common Issues Found

### 1. Artist Prefix Variations
**Issue:** Some S3 folders have artist prefix, some don't
```
Local:  Beatles/Beatles - Abbey Road
S3:     Beatles/Abbey Road  (missing artist prefix)
```

### 2. Bracket Style Differences
**Issue:** Underscores vs brackets in book names
```
Local:  Adele/Adele - 19 _PVG Book_
S3:     Adele/19 [pvg Book]
```

### 3. Multiple S3 Versions
**Issue:** Same book processed multiple times with different names
```
Local:  Beatles/Beatles - Complete Scores (210 songs)
S3 v1:  Beatles/Complete Scores (210 songs)
S3 v2:  Beatles/Beatles - Complete Scores (167 songs)
S3 v3:  Beatles/Beatles - Complete Scores (2) (160 songs)
```

### 4. Song Count Mismatches
**Issue:** Local has different song count than S3
- Could be due to local splitting/merging
- Could be incomplete S3 processing
- Need to verify which is correct

## Review Process

### Step 1: Review EXCELLENT Matches (7 books)
These are 95-99% matches. Very likely correct but have 1-2 song differences.

**Example:**
```
Local:  Bob Dylan/Bob Dylan - Songbook (47 songs)
S3:     Bob Dylan/Songbook (47 songs)
Match:  95.7% (45 matches, 2 local only, 2 S3 only)
```

**Action:** Verify these are the same book, just with minor differences.

### Step 2: Review GOOD Matches (31 books)
These are 80-95% matches. Likely correct but need verification.

**Common cases:**
- Beatles books matching to "Complete Scores" (which contains many books)
- Billy Joel Complete Vol 1/2 with some song differences
- Bob Dylan anthologies with slight variations

**Action:** Confirm these are the correct S3 folders.

### Step 3: Review PARTIAL Matches (59 books)
These are 50-80% matches. May be wrong.

**Action:** Check `missing_books_candidates.csv` for better options.

### Step 4: Review POOR Matches (28 books)
These are <50% matches. Definitely wrong.

**Action:** Check `missing_books_candidates.csv` for correct folder.

### Step 5: Find NO MATCH Books (8 books)
These have no S3 folder found.

**Action:** 
1. Check `missing_books_candidates.csv` for suggestions
2. Manually search S3 structure
3. May need to reprocess these books

## Example Reviews

### EXCELLENT Match - Likely Correct
```
Local:  _broadway Shows/Various Artists - The Ultimate BROADWAY fakebook (407 songs)
S3:     _broadway Shows/Various Artists - The Ultimate Broadway Fakebook (407 songs)
Match:  99.5% (405/407 matches)
Diff:   2 songs only in local, 2 songs only in S3

Decision: CONFIRMED - Same book, minor differences in song extraction
```

### GOOD Match - Needs Verification
```
Local:  Billy Joel/Billy Joel - Complete Vol 1 (47 songs)
S3:     Billy Joel/Complete Vol 1 (47 songs)
Match:  85.1% (40/47 matches)
Diff:   7 songs only in local, 7 songs only in S3

Decision: Need to check - Are these the same 47 songs or different versions?
```

### PARTIAL Match - Likely Wrong
```
Local:  Beatles/Beatles - Abbey Road (19 songs)
S3:     Beatles/Beatles - Complete Scores (167 songs)
Match:  63.2% (12/19 matches)

Candidates:
1. Beatles/Beatles - Abbey Road (7 songs) - Score: 0.81
2. Beatles/Abbey Road (17 songs) - Score: 0.62

Decision: Use candidate #2 (Beatles/Abbey Road) - closer song count
```

## Next Steps

1. **Review `matches_need_review.csv`**
   - Open in Excel or text editor
   - Go through each row
   - Mark status as `CONFIRMED` when verified
   - Update S3 artist/book if needed

2. **Review `missing_books_candidates.csv`**
   - Check suggested candidates
   - Select correct match in `selected_match` column
   - Add notes if needed

3. **Run merge script** (after reviews complete)
   ```powershell
   py merge_confirmed_matches.py
   ```
   This will combine all confirmed matches into final list.

4. **Proceed with cleanup**
   Once all matches are confirmed, we can:
   - Rename S3 folders to match local
   - Delete duplicate folders
   - Fix path duplication bug

## Questions to Answer During Review

For each book, ask:

1. **Is this the same book?**
   - Check artist and book name
   - Verify it's not a different edition/version

2. **Is the song count reasonable?**
   - If local has 47 songs and S3 has 47, likely same
   - If local has 47 and S3 has 167, probably wrong match

3. **Are the song names similar?**
   - Check the sample song names
   - Do they look like they're from the same book?

4. **Is there a better candidate?**
   - Check `missing_books_candidates.csv`
   - Are any of the suggested candidates better?

## Tips

- **Trust PERFECT matches** - These are 100% confirmed
- **Be cautious with Beatles** - Many duplicate folders in S3
- **Check song counts** - Big differences usually mean wrong match
- **Use candidates file** - It has better suggestions for poor matches
- **Add notes** - Document your decisions for future reference

## Timeline

**Estimated review time:** 2-3 hours for 133 books
- EXCELLENT (7): ~5 minutes
- GOOD (31): ~30 minutes
- PARTIAL (59): ~1 hour
- POOR (28): ~45 minutes
- NO MATCH (8): ~15 minutes

**After review:** Ready to execute cleanup script
