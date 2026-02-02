"""
Add "Rename All Files" button to match-quality-viewer-enhanced.html
This button will automatically apply artist normalization to all files that need it
"""
import re

def add_rename_all_button(input_file, output_file):
    """Add the Rename All Files button and functionality"""
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add the button next to "Mark as Exact Match"
    button_pattern = r'(<button class="btn btn-success" id="mark-exact-btn" onclick="toggleMarkAsExact\(\)">\s+Mark as Exact Match\s+</button>)'

    button_replacement = r'''\1
                        <button class="btn" id="rename-all-btn" onclick="renameAllFiles()" style="background: #7a5d00;">
                            Rename All Files
                        </button>'''

    content = re.sub(button_pattern, button_replacement, content)
    print("OK - Added Rename All Files button")

    # 2. Add the renameAllFiles() function
    # Find the toggleMarkAsExact function and add the new function after it
    toggle_function_pattern = r'(function toggleMarkAsExact\(\) \{[^}]+\})'

    rename_all_function = '''

        function renameAllFiles() {
            if (!selectedFolder) return;

            const key = selectedFolder.local_path;
            let localRenames = 0;
            let s3Renames = 0;

            // Build file map to check which files need renaming
            const fc = selectedFolder.file_comparison;
            const fileMap = {};

            // Get folder artist for normalization
            const folderArtist = extractFolderArtist(selectedFolder.local_path);

            // Process all files
            const allFiles = new Set();

            // Add local-only files
            (fc.local_only_files || []).forEach(item => {
                const filename = typeof item === 'string' ? item : item.filename;
                allFiles.add(filename);
                fileMap[filename] = { local: filename, s3: null, status: 'local-only' };
            });

            // Add s3-only files
            (fc.s3_only_files || []).forEach(item => {
                const filename = typeof item === 'string' ? item : item.filename;
                allFiles.add(filename);
                fileMap[filename] = { local: null, s3: filename, status: 's3-only' };
            });

            // Add hash mismatches
            (fc.hash_mismatches || []).forEach(item => {
                const filename = item.filename;
                allFiles.add(filename);
                fileMap[filename] = { local: filename, s3: filename, status: 'hash-mismatch' };
            });

            // Process each file and check if it needs renaming
            for (const [filename, fileInfo] of Object.entries(fileMap)) {
                // Check local file
                if (fileInfo.local) {
                    const normalized = normalizeFilename(fileInfo.local, folderArtist);
                    if (normalized !== fileInfo.local) {
                        // This file needs renaming
                        if (!decisions[key]) {
                            decisions[key] = {};
                        }
                        if (!decisions[key].fileDecisions) {
                            decisions[key].fileDecisions = {};
                        }

                        decisions[key].fileDecisions[fileInfo.local] = {
                            action: 'rename-local',
                            status: 'rename',
                            filepath: fileInfo.local,
                            normalized_name: normalized,
                            local_path: selectedFolder.local_path,
                            s3_path: selectedFolder.s3_path,
                            book_id: selectedFolder.book_id,
                            timestamp: new Date().toISOString()
                        };
                        localRenames++;
                    }
                }

                // Check S3 file
                if (fileInfo.s3 && fileInfo.s3 !== fileInfo.local) {
                    const normalized = normalizeFilename(fileInfo.s3, folderArtist);
                    if (normalized !== fileInfo.s3) {
                        // This file needs renaming
                        if (!decisions[key]) {
                            decisions[key] = {};
                        }
                        if (!decisions[key].fileDecisions) {
                            decisions[key].fileDecisions = {};
                        }

                        decisions[key].fileDecisions[fileInfo.s3] = {
                            action: 'rename-s3',
                            status: 'rename',
                            filepath: fileInfo.s3,
                            normalized_name: normalized,
                            local_path: selectedFolder.local_path,
                            s3_path: selectedFolder.s3_path,
                            book_id: selectedFolder.book_id,
                            timestamp: new Date().toISOString()
                        };
                        s3Renames++;
                    }
                }
            }

            saveDecisions();

            // Show notification
            const totalRenames = localRenames + s3Renames;
            if (totalRenames > 0) {
                alert(`Queued ${totalRenames} file(s) for rename:\\n- Local: ${localRenames}\\n- S3: ${s3Renames}`);
                // Refresh the display
                buildFileComparisonTable(selectedFolder);
            } else {
                alert('No files need renaming in this folder.');
            }
        }'''

    match = re.search(toggle_function_pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + rename_all_function + content[insert_pos:]
        print("OK - Added renameAllFiles() function")
    else:
        print("WARNING - Could not find toggleMarkAsExact function")
        return False

    print(f"Writing to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("OK - Done!")
    print(f"\nUpdated HTML written to: {output_file}")
    return True

if __name__ == '__main__':
    input_file = 'web/match-quality-viewer-enhanced.html'
    output_file = 'web/match-quality-viewer-enhanced.html'

    # Backup first
    import shutil
    backup_file = 'web/match-quality-viewer-enhanced.html.backup2'
    print(f"Creating backup: {backup_file}")
    shutil.copy(input_file, backup_file)

    success = add_rename_all_button(input_file, output_file)

    if success:
        print(f"\nOriginal backed up to: {backup_file}")
    else:
        print("\nFailed to add button - restoring backup")
        shutil.copy(backup_file, input_file)
