"""
Fix the S3 browser HTML to use flattened destination paths.
Target structure: <artist>/<artist> - <book>/Songs/<filename>
"""

def main():
    with open('s3_bucket_browser_interactive.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add the helper function right after displayCompareResults starts
    old_func_start = '''        function displayCompareResults(result) {
            const content = document.getElementById('compareContent');
            
            // Determine which folder has the preferred naming format (Artist - Book)'''
    
    new_func_start = '''        function displayCompareResults(result) {
            const content = document.getElementById('compareContent');
            
            // Helper function to build flattened destination path
            // Target: <artist>/<artist> - <book>/Songs/<filename>
            function buildFlattenedPath(folderPath, relativePath) {
                // Extract just the filename from the relative path
                const pathParts = relativePath.split('/');
                const filename = pathParts[pathParts.length - 1];
                
                // Build target: folderPath + Songs/ + filename
                // Ensure folderPath ends with /
                const normalizedFolder = folderPath.endsWith('/') ? folderPath : folderPath + '/';
                return normalizedFolder + 'Songs/' + filename;
            }
            
            // Determine which folder has the preferred naming format (Artist - Book)'''
    
    # Replace all occurrences
    content = content.replace(old_func_start, new_func_start)
    
    # Now fix the path construction for "different" files
    old_different = '''                    const sourcePath1 = result.folder1 + file.path;
                    const sourcePath2 = result.folder2 + file.path;
                    const destPath1 = result.folder1 + file.path;
                    const destPath2 = result.folder2 + file.path;'''
    
    new_different = '''                    const sourcePath1 = result.folder1 + file.path;
                    const sourcePath2 = result.folder2 + file.path;
                    const destPath1 = buildFlattenedPath(result.folder1, file.path);
                    const destPath2 = buildFlattenedPath(result.folder2, file.path);'''
    
    content = content.replace(old_different, new_different)
    
    # Fix the path construction for "only in folder 1"
    old_only1 = '''                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder1 + file.path;
                    const destPath = result.folder2 + file.path;'''
    
    new_only1 = '''                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder1 + file.path;
                    const destPath = buildFlattenedPath(result.folder2, file.path);'''
    
    content = content.replace(old_only1, new_only1)
    
    # Fix the path construction for "only in folder 2"
    old_only2 = '''                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder2 + file.path;
                    const destPath = result.folder1 + file.path;'''
    
    new_only2 = '''                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder2 + file.path;
                    const destPath = buildFlattenedPath(result.folder1, file.path);'''
    
    content = content.replace(old_only2, new_only2)
    
    # Write back
    with open('s3_bucket_browser_interactive.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed HTML file to use flattened destination paths")
    print("   Target structure: <artist>/<artist> - <book>/Songs/<filename>")

if __name__ == '__main__':
    main()
