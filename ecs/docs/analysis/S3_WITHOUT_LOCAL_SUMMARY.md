# S3 Folders Without Local Matches

## Summary
- **Total S3 folders:** 913
- **Local folders:** 559
- **S3 folders WITHOUT local match:** 617 (67.6%)
- **S3 folders WITH local match:** 296 (32.4%)

## Analysis

This means **most of S3 is NOT downloaded locally**. The 617 unmatched S3 folders represent duplicate versions, alternate editions, or books that were never downloaded.

## Top 20 Largest S3 Folders Not in Local

1. **Various Artists - 557 Standards (sheet music - piano)(2)** - 345 PDFs
2. **Beatles - Fake songbook (guitar)** - 250 PDFs
3. **Beatles - Complete scores (2)** - 210 PDFs
4. **Beatles - Complete scores** - 210 PDFs
5. **Beatles - All songs 1962-1974** - 199 PDFs
6. **Beatles - Anthology** - 199 PDFs
7. **Beatles - Songbook** - 194 PDFs
8. **Various Artists - 557 Standards** - 174 PDFs
9. **Beatles - Complete scores (2)** - 160 PDFs
10. **Beatles - Fake songbook (guitar)** - 121 PDFs
11. **Burl Ives - Song book** - 107 PDFs
12. **Various Artists - The best children's songs ever** - 103 PDFs
13. **Various Artists - Ultimate 100 pop hits of the 90s** - 102 PDFs
14. **Various Artists - 100 songs for kids** - 99 PDFs
15. **Various Artists - Golden era of rock and roll** - 99 PDFs
16. **Beatles - Essential songs** - 96 PDFs
17. **Various Artists - Ultimate pop sheet music collection 2000** - 84 PDFs
18. **Various Artists - Classic rock - 73 songs** - 73 PDFs
19. **Various Artists - Great big book of children's songs** - 73 PDFs
20. **Billy Joel - My lives** - 72 PDFs

**Total PDFs in top 20:** ~2,800 PDFs

## Key Observations

### 1. Beatles Duplicates
Multiple versions of Beatles books exist in S3:
- Complete Scores (3 versions: 210, 210, 160 PDFs)
- Fake Songbook (2 versions: 250, 121 PDFs)
- Anthology (199 PDFs)
- Songbook (194 PDFs)
- All Songs 1962-1974 (199 PDFs)

**Local has:** Beatles - Complete Scores _2_ (210 PDFs), Beatles - Fake Songbook _Guitar_ (178 PDFs)

### 2. Large Collections Not Downloaded
- 557 Standards (345 PDFs) - NOT in local
- Burl Ives Song Book (107 PDFs) - NOT in local
- Various Artists collections (100+ PDFs each) - NOT in local

### 3. Duplicate Versions
Many artists have multiple versions in S3 with different PDF counts:
- John Denver - Anthology [pvg] (53) vs Anthology (53)
- Bob Dylan - Anthology (45) vs Anthology 1 (45) vs Anthology 2 (50)
- Journey - Complete (68) vs Complete Songbook (68)

## Recommendations

1. **Identify true duplicates in S3** - Many folders are the same book with different naming
2. **Determine which S3 versions to keep** - Should match local naming conventions
3. **Download missing large collections** - If you want them locally
4. **Clean up S3** - Remove duplicate versions to match the 559 local folders

## Question

Do you want to:
1. **Download the 617 S3 folders to local** (massive download)?
2. **Delete the 617 S3 folders** to match local (clean up S3)?
3. **Identify which are true duplicates** vs unique books?
