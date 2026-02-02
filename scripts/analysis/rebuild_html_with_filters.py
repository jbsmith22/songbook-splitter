"""
Rebuild HTML viewer with:
1. New match quality data (size-based matching)
2. Proper filtering functionality
3. Pre-loaded rename decisions
"""
import json
import re

def rebuild_html_viewer():
    """Rebuild the HTML viewer with all enhancements"""

    print("=== Rebuilding HTML Viewer ===\n")

    # Load the data files
    print("Loading match_quality_data.json...")
    with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
        match_data = json.load(f)

    print("Loading auto_rename_decisions.json...")
    with open('data/analysis/auto_rename_decisions.json', 'r', encoding='utf-8') as f:
        rename_decisions = json.load(f)

    # Read the HTML file
    html_file = 'web/match-quality-viewer-enhanced.html'
    print(f"Reading {html_file}...")
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # Step 1: Replace the embedded match data
    print("\nStep 1: Embedding new match quality data...")

    # Find the line with matchDataEmbedded
    lines = html.split('\n')
    found_line = -1
    for i, line in enumerate(lines):
        if 'const matchDataEmbedded = {' in line:
            found_line = i
            break

    if found_line == -1:
        print("ERROR: Could not find matchDataEmbedded in HTML")
        return False

    # Create new embedded data (compact single line to keep file size reasonable)
    new_match_data = f"const matchDataEmbedded = {json.dumps(match_data)};"
    lines[found_line] = new_match_data
    html = '\n'.join(lines)
    print("OK - Match data embedded")

    # Step 2: Add filter controls after summary statistics
    print("\nStep 2: Adding filter controls...")

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

    # Find the summary stats section and insert after it
    summary_pattern = r'(<div class="summary-stats">.*?</div>\s*</div>)'
    match = re.search(summary_pattern, html, re.DOTALL)
    if match:
        insert_pos = match.end()
        html = html[:insert_pos] + '\n' + filter_controls_html + html[insert_pos:]
        print("OK - Filter controls added")
    else:
        print("WARNING - Could not find summary stats section")

    # Step 3: Add filtering JavaScript before initializeViewer function
    print("\nStep 3: Adding filtering JavaScript...")

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

            // Re-render
            initializeViewer();
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
        }

'''

    # Find initializeViewer function and insert filtering code before it
    init_viewer_pattern = r'(\s+function initializeViewer\(\))'
    match = re.search(init_viewer_pattern, html)
    if match:
        insert_pos = match.start()
        html = html[:insert_pos] + filter_js + html[insert_pos:]
        print("OK - Filtering JavaScript added")
    else:
        print("ERROR - Could not find initializeViewer function")
        return False

    # Step 4: Modify initializeViewer to use filtering
    print("\nStep 4: Modifying initializeViewer to use filters...")

    # Find and replace the artist grouping loop to use filtering
    old_loop = r'for \(const \[tier, folders\] of Object\.entries\(matchData\.quality_tiers\)\) \{'
    new_loop = '''for (const [tier, folders] of Object.entries(matchData.quality_tiers)) {
                const filteredFolders = folders.filter(folder => folderMatchesFilters(folder));'''

    html = re.sub(old_loop, new_loop, html)

    # Replace 'for (const folder of folders)' with 'for (const folder of filteredFolders)'
    html = html.replace(
        'for (const folder of folders) {',
        'for (const folder of filteredFolders) {'
    )
    print("OK - initializeViewer modified to use filters")

    # Step 5: Embed rename decisions
    print("\nStep 5: Embedding rename decisions...")

    load_decisions_pattern = r'function loadDecisions\(\) \{\s*const stored = localStorage\.getItem\(STORAGE_KEY\);\s*return stored \? JSON\.parse\(stored\) : \{\};\s*\}'

    match_obj = re.search(load_decisions_pattern, html)
    if not match_obj:
        print("WARNING: Could not find loadDecisions function - skipping rename decision embedding")
    else:
        decisions_json = json.dumps(rename_decisions, indent=2)

        replacement = f'''function loadDecisions() {{
            // Pre-loaded rename decisions
            const embeddedDecisions = {decisions_json};

            // Load from localStorage
            const stored = localStorage.getItem(STORAGE_KEY);
            let decisions = stored ? JSON.parse(stored) : {{}};

            // Merge embedded decisions (embedded takes precedence for file decisions)
            for (const [folderPath, folderData] of Object.entries(embeddedDecisions)) {{
                if (!decisions[folderPath]) {{
                    decisions[folderPath] = {{}};
                }}
                if (!decisions[folderPath].fileDecisions) {{
                    decisions[folderPath].fileDecisions = {{}};
                }}
                // Merge file decisions from embedded data
                Object.assign(decisions[folderPath].fileDecisions, folderData.fileDecisions);
            }}

            console.log('Loaded ' + Object.keys(embeddedDecisions).length + ' folders with pre-selected renames');
            return decisions;
        }}'''

        # Use string slicing instead of re.sub to avoid escape issues
        html = html[:match_obj.start()] + replacement + html[match_obj.end():]
        print("OK - Rename decisions embedded")

    # Write the updated HTML
    print(f"\nWriting updated HTML to {html_file}...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print("\n=== SUCCESS ===")
    print(f"HTML viewer rebuilt with:")
    print(f"  - {len(match_data.get('quality_tiers', {}).get('perfect', []))} perfect matches")
    print(f"  - Filtering functionality")
    print(f"  - {len(rename_decisions)} folders with pre-selected renames")
    print(f"\nOpen {html_file} in your browser to test!")

    return True

if __name__ == '__main__':
    import shutil

    # Backup first
    backup_file = 'web/match-quality-viewer-enhanced.html.backup5'
    print(f"Creating backup: {backup_file}\n")
    shutil.copy('web/match-quality-viewer-enhanced.html', backup_file)

    success = rebuild_html_viewer()

    if not success:
        print("\nFailed - restoring backup")
        shutil.copy(backup_file, 'web/match-quality-viewer-enhanced.html')
    else:
        print(f"\nBackup saved to: {backup_file}")
