# Reconciliation Guide - 248 Folders Remaining

## Current Status

After archiving 292 PERFECT folders, you have **248 folders** remaining that need reconciliation between local (ProcessedSongs) and S3 (jsmith-output).

### Quality Tier Breakdown

| Tier | Count | % | What It Means |
|------|-------|---|---------------|
| PERFECT | 8 | 3.2% | Exact match - consider archiving these too |
| EXCELLENT | 11 | 4.4% | Name and count match, some file differences |
| GOOD | 4 | 1.6% | Name matches, count is close |
| WEAK | 103 | 41.5% | Name similar, count differs significantly |
| POOR | 122 | 49.2% | Significant mismatches |

## File Decision Summary

Total file decisions across all 248 folders: **8,036 files**

| Action | Count | % | What It Means |
|--------|-------|---|---------------|
| No action (match) | 5,754 | 71.6% | Files already match perfectly |
| Copy S3 → local | 890 | 11.1% | File only in S3 or S3 version is larger |
| Copy local → S3 | 509 | 6.3% | File only local or local version is larger |
| S3 larger (overwrite local) | 797 | 9.9% | Both exist, S3 has larger file |
| Local larger (overwrite S3) | 86 | 1.1% | Both exist, local has larger file |

## Manual Decisions Preserved

Your previous reconciliation work has been preserved and merged:

- **82 rename decisions** - File name corrections you made
- **17 delete decisions** - Duplicates you marked for removal
- **285 aligned decisions** - Your choices that match current analysis
- **60 conflicts** - Places where your previous decision differs from current recommendation (flagged for review)

## Reconciliation Workflow

### 1. Open the HTML Viewer

Open `web/match-quality-viewer-enhanced.html` in your browser. This viewer now contains:
- All 248 folders with current file state
- Your previous manual decisions
- Recommended actions for each file
- Conflicts flagged for review

### 2. Work Through Each Tier

**Recommended order:**

1. **PERFECT (8 folders)** - Quick wins, consider archiving
   - Verify they truly are perfect
   - Archive them with the others

2. **EXCELLENT (11 folders)** - Easy fixes
   - Most files match, just a few differences
   - Usually just need to sync size mismatches
   - Should take 5-10 minutes each

3. **GOOD (4 folders)** - Minor issues
   - Name matches, count is close
   - May have a few extra/missing files
   - Check for duplicates or renamed files

4. **WEAK (103 folders)** - Moderate work
   - Significant file count differences
   - May need careful review of what files belong
   - Could have missing sections or duplicates

5. **POOR (122 folders)** - Requires investigation
   - Major mismatches
   - May need to check source PDFs
   - Could be completely different books or processing errors

### 3. For Each Folder

1. **Review the match quality details:**
   - Local file count vs S3 file count
   - Matching files vs mismatched files
   - File size differences

2. **Check file decisions:**
   - Files marked with `conflict_with_previous` need your attention
   - Files marked with `hint_source: previous_decision` use your manual choices
   - Other files use automatic recommendations

3. **Make adjustments if needed:**
   - Override automatic recommendations
   - Add delete decisions for duplicates
   - Add rename decisions for incorrect file names

4. **Apply decisions:**
   - The viewer can export your decisions as JSON
   - Execute the decisions to sync files

## Recommended Actions by Tier

### PERFECT Folders (8)
- **Action:** Archive these with the other 292
- **Why:** They're already perfect, get them out of the way
- **Script:** `scripts/analysis/archive_perfect_folders.py` (update to use new list)

### EXCELLENT Folders (11)
- **Action:** Quick sync of size mismatches
- **Why:** Most files match, just need to copy larger versions
- **Effort:** Low - 10-20 minutes total

### GOOD Folders (4)
- **Action:** Review and sync
- **Why:** Small count differences, probably just a few files to fix
- **Effort:** Low - 30 minutes total

### WEAK Folders (103)
- **Action:** Systematic review
- **Why:** Significant differences, need to understand what's wrong
- **Effort:** Medium - Could take several hours
- **Strategy:**
  - Batch similar issues together
  - Look for patterns (artist name issues, missing sections, etc.)

### POOR Folders (122)
- **Action:** Deep investigation
- **Why:** Major problems, may need to re-process
- **Effort:** High - Could take many hours
- **Strategy:**
  - Start with a sample (5-10 folders)
  - Identify common issues
  - Consider re-processing from source if problems are systemic

## Files Generated

1. **reconciliation_decisions_2026-02-02_fresh_generated.json**
   - Fresh analysis of current state
   - Automatic recommendations based on file sizes

2. **reconciliation_decisions_2026-02-02_merged.json**
   - Fresh analysis + your previous manual decisions
   - This is what's loaded in the HTML viewer
   - Use this as your working file

3. **web/match-quality-viewer-enhanced.html**
   - Updated with 248 folders
   - Embedded with merged decisions
   - Ready to use for reconciliation

## Next Steps

1. **Open the viewer:** `web/match-quality-viewer-enhanced.html`
2. **Start with PERFECT folders:** Verify and archive the 8 perfect ones
3. **Work through EXCELLENT:** Quick wins, should be easy
4. **Tackle GOOD and WEAK systematically**
5. **Save POOR for last or consider re-processing**

## Important Notes

- The viewer saves decisions to browser localStorage
- Export your decisions regularly (use the Export button)
- The HTML file already has your 82 renames and 17 deletes preserved
- Review the 60 conflicts carefully - these are where your previous manual decision differs from the current automatic recommendation

## Questions?

- **Why 71.6% already match?** Most files are fine, you're just fixing the problematic ones
- **Should I trust the automatic recommendations?** Generally yes, but review conflicts
- **What if I'm not sure?** Mark for manual review and investigate the source PDF
- **Can I undo decisions?** Yes, the viewer allows editing before applying

Good luck with the reconciliation! Start with the easy tiers and work your way up.
