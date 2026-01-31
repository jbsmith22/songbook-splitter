# Input vs Output Analysis

## Summary
- **Input PDFs:** 559
- **Output Folders:** 569
- **Difference:** +10 output folders

## Matched
- **Exact matches:** 554 (case-insensitive)
- **Total matched:** 554/559 input PDFs have output folders

## 5 Input PDFs WITHOUT Output Folders

These are the 5 input PDFs we deleted earlier because they don't exist in S3:

1. `_Broadway Shows\Various Artists - 25th Annual Putnam County Spelling Bee.pdf`
   - **Status:** Empty folder deleted (not in S3)

2. `_Movie and TV\Various Artists - Complete TV And Film.pdf`
   - **Status:** Empty folder deleted (not in S3)

3. `Elvis Presley\Elvis Presley - The Compleat _PVG Book_.pdf`
   - **Status:** Empty folder deleted (not in S3)

4. `Eric Clapton\Eric Clapton - The Cream Of Clapton.pdf`
   - **Status:** Empty folder deleted (not in S3)

5. `Mamas and the Papas\Mamas And The Papas - Songbook _PVG_.pdf`
   - **Status:** Empty folder deleted (not in S3)

**Conclusion:** These 5 input PDFs should be processed through the pipeline to create output folders.

## 15 Output Folders WITHOUT Input PDFs

These output folders exist but don't have exact-match input PDFs. Analysis:

### 1. Downloaded from S3 (empty folders we filled)
1. **Night Ranger/Seven Wishes _jap Score_** (10 PDFs)
   - Input: `Night Ranger - Seven Wishes _Jap Score_.pdf` (case difference: jap vs Jap)
   - **Status:** Downloaded from S3, input exists with case difference

2. **_broadway Shows/Various Artists - Little Shop Of Horrors (original)** (2 PDFs)
   - Input: `Various Artists - Little Shop Of Horrors Script.pdf` (name difference)
   - **Status:** Downloaded from S3, input has different name

### 2. Bracket Style Differences (input uses _brackets_, output uses [brackets])
3. **America/America - Greatest Hits [Book]** (4 PDFs)
   - Input: `America - Greatest Hits _Book_.pdf`
   - **Status:** Same book, bracket style difference

4. **Ben Folds/Ben Folds - Rockin' The Suburbs [Book]** (1 PDF)
   - Input: `Ben Folds - Rockin The Suburbs _Book_.pdf`
   - **Status:** Same book, bracket style + apostrophe difference

5. **Kinks/Kinks - Guitar Legends [Tab]** (9 PDFs)
   - Input: `Kinks - Guitar Legends _Tab_.pdf`
   - **Status:** Same book, bracket style difference

6. **Who/Who - Quadrophenia (PVG)** (9 PDFs)
   - Input: `Who - Quadrophenia _PVG_.pdf`
   - **Status:** Same book, bracket style difference

7. **Wings/Wings - London Town (PVG Book)** (8 PDFs)
   - Input: `Wings - London Town _PVG Book_.pdf`
   - **Status:** Same book, bracket style difference

8. **_broadway Shows/Various Artists - Wicked [pvg]** (6 PDFs)
   - Input: `Various Artists - Wicked _PVG_.pdf`
   - **Status:** Same book, bracket style difference

### 3. Multiple Outputs from Same Input (book was split in S3)
9. **_broadway Shows/Various Artists - High School Musical [score]** (16 PDFs)
   - Input: `Various Artists - High School Musical _Score_.pdf`
   - **Status:** Same book, bracket style difference

10. **_broadway Shows/Various Artists - Wicked [score]** (1 PDF)
    - Input: `Various Artists - Wicked _Score_.pdf`
    - **Status:** Same book, bracket style difference (also has [pvg] version)

11. **_broadway Shows/Various Artists - You're A Good Man Charlie Brown [revival] [score]** (22 PDFs)
    - Input: `Various Artists - Youre A Good Man Charlie Brown _revival_ _score_.pdf`
    - **Status:** Same book, apostrophe + bracket style difference

### 4. Wrong Artist Folder
12. **Elo/Elton John - The Elton John Collection [Piano Solos]** (29 PDFs)
    - Input: `Elton John\Elton John - The Elton John Collection _Piano Solos_.pdf`
    - **Status:** WRONG ARTIST FOLDER! Should be in "Elton John" not "Elo"

### 5. Likely from S3 (no exact input match)
13. **Tom Waits/Anthology** (29 PDFs)
    - Input options: `Tom Waits - Anthology.pdf` OR `Tom Waits - Tom Waits Anthology.pdf`
    - **Status:** Likely matches one of these inputs

14. **Various Artists/Adult Contemporary Hits Of The Nineties** (30 PDFs)
    - Input: `Various Artists - Adult Contemporary Hits Of The Nineties.pdf` (should match)
    - **Status:** Should be exact match, investigate why it didn't match

15. **Vince Guaraldi/Peanuts Songbook** (28 PDFs)
    - Input: `Vince Guaraldi - Peanuts Songbook.pdf`
    - **Status:** Should be exact match, investigate why it didn't match

## Issues Found

### Critical Issue: Wrong Artist Folder
- **Elo/Elton John - The Elton John Collection [Piano Solos]**
  - This is an Elton John book that ended up in the ELO artist folder
  - Should be moved to: `Elton John/Elton John - The Elton John Collection [Piano Solos]`

### Matching Issues
The comparison script should have matched these but didn't:
- Tom Waits/Anthology
- Various Artists/Adult Contemporary Hits Of The Nineties
- Vince Guaraldi/Peanuts Songbook

These likely have case or spacing differences that the normalization didn't catch.

## Recommendations

1. **Process the 5 missing input PDFs** through the pipeline to create their output folders
2. **Move the Elton John folder** from Elo to Elton John artist folder
3. **Investigate the 3 matching failures** to understand why they didn't match
4. **Accept the bracket style differences** as normal (S3 uses [brackets], local input uses _brackets_)

## Final Count After Corrections

If we fix the issues:
- 559 input PDFs
- 559 output folders (after moving Elton John and accounting for bracket differences)
- Perfect 1:1 match (except for the 5 that need processing)
