# S3 Browser Path Flattening Fix

## Problem
When comparing and moving files between folders in the S3 browser, destination paths were being constructed incorrectly, leading to nested folder structures like:
- `Bread/Bread - Best Of Bread/Bread - Best Of Bread/Songs/`

Instead of the target structure:
- `Bread/Bread - Best Of Bread/Songs/`

## Root Cause
The JavaScript was constructing destination paths by concatenating:
```javascript
const destPath = result.folder2 + file.path;
```

Where `file.path` was a relative path that could include subfolder structure (e.g., `Bread - Best Of Bread/Songs/file.pdf`), causing duplication when appended to the folder path.

## Solution

### 1. Added Path Flattening Function
Created `buildFlattenedPath()` helper function in the HTML file that:
- Extracts just the filename from the relative path
- Constructs the target as: `<folderPath>/Songs/<filename>`
- Ensures all files land in the correct flat structure

```javascript
function buildFlattenedPath(folderPath, relativePath) {
    const pathParts = relativePath.split('/');
    const filename = pathParts[pathParts.length - 1];
    const normalizedFolder = folderPath.endsWith('/') ? folderPath : folderPath + '/';
    return normalizedFolder + 'Songs/' + filename;
}
```

### 2. Updated All Path Construction
Modified all destination path construction to use the flattening function:
- Different files (same name, different content)
- Files only in Folder 1
- Files only in Folder 2

### 3. Fixed Existing Bread Folder
Ran `fix_bread_structure.py` to move 7 files from the incorrectly nested structure to the correct location.

## Target Structure
All files should now be moved to:
```
<artist>/<artist> - <book>/Songs/<filename>.pdf
```

Example:
```
Bread/Bread - Best Of Bread/Songs/Bread - Hooked On You.pdf
```

## Files Modified
- `s3_bucket_browser_interactive.html` - Added flattening logic
- `fix_bread_structure.py` - Script to fix existing Bread folder
- `fix_html_paths.py` - Script to update HTML file

## Testing
1. Reload the S3 browser page
2. Compare two folders (e.g., `Bread/Best Of Bread/` vs `Bread/Bread - Best Of Bread/`)
3. Use Smart Select and move files
4. Verify files land in `<artist>/<artist> - <book>/Songs/` with no extra nesting

## Status
✅ Bread folder fixed
✅ HTML path construction updated
✅ Ready for testing with other artists
