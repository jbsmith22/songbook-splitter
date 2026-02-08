# Sync Original Structure to Match This Organization

This document explains how to reorganize the original `C:\Work\AWSMusic` structure to exactly match the organization in `D:\Work\songbook-splitter`.

## Overview

The synchronization will:
1. **Move working directories** from `data/` to root
2. **Move build artifacts** to `build/` directory
3. **Move verification results** to `web/verification/`
4. **Create all subdirectories** to match the hierarchical structure
5. **Preserve all files** - nothing is deleted, only reorganized

## What Will Change

### Moves from data/ to root:
- `data/ProcessedSongs` → `ProcessedSongs`
- `data/SheetMusic` → `SheetMusic`
- `data/SheetMusicIndividualSheets` → `SheetMusicIndividualSheets`
- `data/output` → `output`
- `data/temp_anthology_output` → `temp_anthology_output`
- `data/temp_anthology_pages` → `temp_anthology_pages`
- `data/toc_cache` → `toc_cache`
- `data/verification_batches` → `verification_batches`

### Moves to build/:
- `lambda-deployment.zip` → `build/lambda-deployment.zip`
- `lambda-package` → `build/lambda-package`

### Moves to web/verification/:
- `data/verification_results` → `web/verification/verification_results`

### New subdirectories created:
All 36+ subdirectories will be created to match the hierarchical structure:
- `data/` → 10 subdirectories
- `docs/` → 12 subdirectories
- `scripts/` → 7 subdirectories (with sub-subdirectories)
- `logs/` → 4 subdirectories
- `web/` → 3 subdirectories
- `tests/fixtures/`
- `build/`

## Instructions

### Option 1: Python Script (Recommended)

1. **Copy the script** to the original location:
   ```bash
   copy sync_to_my_structure.py C:\Work\AWSMusic\
   ```

2. **Update the BASE_DIR** in the script if needed:
   - Open `sync_to_my_structure.py`
   - Change line 9 if your directory is different:
     ```python
     BASE_DIR = Path(r"C:\Work\AWSMusic")  # Update this path
     ```

3. **Run the script**:
   ```bash
   cd C:\Work\AWSMusic
   py sync_to_my_structure.py
   ```

4. **Review the output** and press Enter to confirm

### Option 2: PowerShell Script

1. **Copy the script** to the original location:
   ```powershell
   Copy-Item sync_to_my_structure.ps1 C:\Work\AWSMusic\
   ```

2. **Update the BASE_DIR** in the script if needed:
   - Open `sync_to_my_structure.ps1`
   - Change line 4 if your directory is different:
     ```powershell
     $BASE_DIR = "C:\Work\AWSMusic"  # Update this path
     ```

3. **Run the script**:
   ```powershell
   cd C:\Work\AWSMusic
   .\sync_to_my_structure.ps1
   ```

4. **Review the output** and press Enter to confirm

## After Running

### 1. Verify the Changes

Compare the two directories using a folder comparison tool (like Beyond Compare) to ensure everything matches.

### 2. Check Git Status

```bash
cd C:\Work\AWSMusic
git status
```

You'll see:
- Many files marked as "renamed" (git tracks the moves)
- New directories created
- No files deleted or lost

### 3. Commit the Changes

If everything looks good:

```bash
git add -A
git commit -m "Reorganize structure to match hierarchical organization

- Move working directories from data/ to root
- Move build artifacts to build/ directory
- Move verification results to web/verification/
- Create comprehensive subdirectory structure
- 36+ subdirectories for fine-grained organization"
```

### 4. Push to GitHub

```bash
git push
```

## Safety Notes

- ✅ **No files are deleted** - only moved/reorganized
- ✅ **Git tracks renames** - history is preserved
- ✅ **Can be undone** with `git reset --hard HEAD` before committing
- ✅ **Script checks** if directories exist before moving
- ✅ **Creates directories** automatically as needed

## Rollback

If you want to undo the changes before committing:

```bash
git reset --hard HEAD
git clean -fd
```

This will restore the original structure.

## Verification

After syncing, both directories should have:
- **7 essential files in root**
- **Same main directories**: app/, build/, data/, docs/, ecs/, infra/, lambda/, logs/, scripts/, tests/, web/
- **Same subdirectory structure** within each main directory
- **All files preserved** - just in better organized locations

## Questions?

If you encounter any issues:
1. Check the script output for error messages
2. Verify the BASE_DIR path is correct
3. Ensure you have write permissions
4. Make sure no files are open in other programs

The scripts are designed to be safe and reversible. All changes are tracked by git, so you can always review or undo them before pushing.
