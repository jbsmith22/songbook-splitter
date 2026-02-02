"""
Add filtering controls and detailed metadata display to the HTML viewer
"""
import re

def add_filtering_features(html_file):
    """Add filtering and metadata expansion features"""
    print(f"Reading {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Add filter controls after the summary statistics
    filter_controls_html = '''
        <div class="filter-controls" style="background: #2d2d30; padding: 15px; margin-bottom: 20px; border-radius: 4px; border-left: 3px solid #569cd6;">
            <div style="font-weight: bold; margin-bottom: 10px; color: #569cd6;">Filter by Match Criteria:</div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-exact-name" checked style="margin-right: 8px;">
                    <span>Exact Folder Name</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-exact-count" checked style="margin-right: 8px;">
                    <span>Exact File Count</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-has-manifest" checked style="margin-right: 8px;">
                    <span>Has Manifest</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-all-artifacts" checked style="margin-right: 8px;">
                    <span>All Artifacts (5/5)</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-files-match" checked style="margin-right: 8px;">
                    <span>All Files Match</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-fuzzy-name" checked style="margin-right: 8px;">
                    <span>Fuzzy Name Match</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-different-count" checked style="margin-right: 8px;">
                    <span>Different File Count</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-no-manifest" checked style="margin-right: 8px;">
                    <span>No Manifest</span>
                </label>
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="filter-partial-artifacts" checked style="margin-right: 8px;">
                    <span>Partial/No Artifacts</span>
                </label>
            </div>
            <div style="margin-top: 10px;">
                <button class="btn" onclick="applyFilters()" style="background: #0e639c; padding: 8px 16px;">Apply Filters</button>
                <button class="btn" onclick="resetFilters()" style="background: #666; padding: 8px 16px; margin-left: 10px;">Reset</button>
                <span id="filter-result-count" style="margin-left: 20px; color: #858585;"></span>
            </div>
        </div>
'''

    # Find where to insert (after the summary stats div)
    summary_pattern = r'(<div class="summary-stats">.*?</div>\s*</div>)'
    match = re.search(summary_pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + '\n' + filter_controls_html + content[insert_pos:]
        print("OK - Added filter controls")
    else:
        print("WARNING - Could not find summary stats section")

    # 2. Add filtering JavaScript functions
    filter_js = '''
        // Filtering state
        let currentFilters = {
            exactName: true,
            exactCount: true,
            hasManifest: true,
            allArtifacts: true,
            filesMatch: true,
            fuzzyName: true,
            differentCount: true,
            noManifest: true,
            partialArtifacts: true
        };

        function applyFilters() {
            // Read checkbox states
            currentFilters = {
                exactName: document.getElementById('filter-exact-name').checked,
                exactCount: document.getElementById('filter-exact-count').checked,
                hasManifest: document.getElementById('filter-has-manifest').checked,
                allArtifacts: document.getElementById('filter-all-artifacts').checked,
                filesMatch: document.getElementById('filter-files-match').checked,
                fuzzyName: document.getElementById('filter-fuzzy-name').checked,
                differentCount: document.getElementById('filter-different-count').checked,
                noManifest: document.getElementById('filter-no-manifest').checked,
                partialArtifacts: document.getElementById('filter-partial-artifacts').checked
            };

            // Re-render folder tree with filters
            buildFolderTree();
        }

        function resetFilters() {
            // Check all boxes
            document.getElementById('filter-exact-name').checked = true;
            document.getElementById('filter-exact-count').checked = true;
            document.getElementById('filter-has-manifest').checked = true;
            document.getElementById('filter-all-artifacts').checked = true;
            document.getElementById('filter-files-match').checked = true;
            document.getElementById('filter-fuzzy-name').checked = true;
            document.getElementById('filter-different-count').checked = true;
            document.getElementById('filter-no-manifest').checked = true;
            document.getElementById('filter-partial-artifacts').checked = true;

            applyFilters();
        }

        function folderMatchesFilters(folder) {
            const exactCount = folder.local_songs === folder.s3_songs;
            const exactName = folder.exact_alpha_name;
            const hasManifest = folder.has_manifest;
            const allArtifacts = folder.artifacts_count === 5;
            const allFilesMatch = folder.all_files_match;

            // Check if folder matches any of the enabled filter criteria
            let matches = false;

            // Exact name match combinations
            if (exactName && currentFilters.exactName) {
                if (exactCount && currentFilters.exactCount) matches = true;
                if (hasManifest && currentFilters.hasManifest) matches = true;
                if (allArtifacts && currentFilters.allArtifacts) matches = true;
                if (allFilesMatch && currentFilters.filesMatch) matches = true;
            }

            // Fuzzy name match combinations
            if (!exactName && currentFilters.fuzzyName) {
                if (exactCount && currentFilters.exactCount) matches = true;
                if (hasManifest && currentFilters.hasManifest) matches = true;
                if (allArtifacts && currentFilters.allArtifacts) matches = true;
            }

            // Different count combinations
            if (!exactCount && currentFilters.differentCount) {
                if (hasManifest && currentFilters.hasManifest) matches = true;
                if (allArtifacts && currentFilters.allArtifacts) matches = true;
            }

            // No manifest combinations
            if (!hasManifest && currentFilters.noManifest) {
                matches = true;
            }

            // Partial/no artifacts combinations
            if (allArtifacts < 5 && currentFilters.partialArtifacts) {
                matches = true;
            }

            return matches;
        }'''

    # Find where to insert filtering JS (before buildFolderTree function)
    build_folder_tree_pattern = r'(function buildFolderTree\(\))'
    match = re.search(build_folder_tree_pattern, content)
    if match:
        insert_pos = match.start()
        content = content[:insert_pos] + filter_js + '\n\n        ' + content[insert_pos:]
        print("OK - Added filtering JavaScript")
    else:
        print("WARNING - Could not find buildFolderTree function")

    # 3. Modify buildFolderTree to use filters
    # Find the line that iterates through matchData.quality_tiers
    old_build_pattern = r"for \(const \[tier, folders\] of Object\.entries\(matchData\.quality_tiers\)\) \{"
    new_build = '''for (const [tier, folders] of Object.entries(matchData.quality_tiers)) {
                const filteredFolders = folders.filter(folder => folderMatchesFilters(folder));
                if (filteredFolders.length === 0) continue; // Skip empty tiers'''

    # Replace and adjust the loop to use filteredFolders
    content = re.sub(
        r"(for \(const \[tier, folders\] of Object\.entries\(matchData\.quality_tiers\)\) \{)",
        new_build,
        content
    )

    # Replace 'folders.forEach' with 'filteredFolders.forEach'
    content = content.replace(
        'folders.forEach(folder => {',
        'filteredFolders.forEach(folder => {'
    )
    print("OK - Modified buildFolderTree to use filters")

    # 4. Update artifact display to show all 5 artifacts
    # This will be done by modifying the buildCriteriaGrid function
    # For now, just ensure the artifacts_list is displayed

    print(f"Writing updated HTML...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Done!")
    return True

if __name__ == '__main__':
    html_file = 'web/match-quality-viewer-enhanced.html'

    # Backup first
    import shutil
    backup_file = 'web/match-quality-viewer-enhanced.html.backup4'
    print(f"Creating backup: {backup_file}")
    shutil.copy(html_file, backup_file)

    add_filtering_features(html_file)
    print(f"\nBackup saved to: {backup_file}")
