"""
Update filter JavaScript to work with radio buttons
"""
import re

with open('web/match-quality-viewer-enhanced.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the filtering state
old_state_pattern = r'// Filtering state\s*let currentFilters = \{[^}]+\};'
new_state = '''// Filtering state
        let currentFilters = {
            name: 'any',
            count: 'any',
            manifest: 'any',
            artifacts: 'any'
        };'''

html = re.sub(old_state_pattern, new_state, html)
print("Updated filter state")

# Replace applyFilters function
old_apply_pattern = r'function applyFilters\(\) \{[^}]*getElementById[^}]*initializeViewer\(\);[^}]*\}'
new_apply = '''function applyFilters() {
            // Read radio button states
            const nameFilter = document.querySelector('input[name="filter-name"]:checked');
            const countFilter = document.querySelector('input[name="filter-count"]:checked');
            const manifestFilter = document.querySelector('input[name="filter-manifest"]:checked');
            const artifactsFilter = document.querySelector('input[name="filter-artifacts"]:checked');

            currentFilters = {
                name: nameFilter ? nameFilter.value : 'any',
                count: countFilter ? countFilter.value : 'any',
                manifest: manifestFilter ? manifestFilter.value : 'any',
                artifacts: artifactsFilter ? artifactsFilter.value : 'any'
            };

            // Re-render
            initializeViewer();
        }'''

html = re.sub(old_apply_pattern, new_apply, html, flags=re.DOTALL)
print("Updated applyFilters")

# Replace resetFilters function
old_reset_pattern = r'function resetFilters\(\) \{[^}]*getElementById[^}]*applyFilters\(\);[^}]*\}'
new_reset = '''function resetFilters() {
            // Reset all radio buttons to "any"
            document.querySelectorAll('input[type="radio"][value="any"]').forEach(radio => {
                radio.checked = true;
            });
            applyFilters();
        }'''

html = re.sub(old_reset_pattern, new_reset, html, flags=re.DOTALL)
print("Updated resetFilters")

# Replace folderMatchesFilters function - this is more complex
old_matches_pattern = r'function folderMatchesFilters\(folder\) \{.*?return.*?;[\s\n]*\}'
new_matches = '''function folderMatchesFilters(folder) {
            const exactCount = folder.local_songs === folder.s3_songs;
            const exactName = folder.exact_alpha_name;
            const hasManifest = folder.has_manifest;
            const allArtifacts = folder.artifacts_count === 5;

            // Check name filter
            if (currentFilters.name === 'exact' && !exactName) return false;
            if (currentFilters.name === 'fuzzy' && exactName) return false;

            // Check count filter
            if (currentFilters.count === 'exact' && !exactCount) return false;
            if (currentFilters.count === 'different' && exactCount) return false;

            // Check manifest filter
            if (currentFilters.manifest === 'yes' && !hasManifest) return false;
            if (currentFilters.manifest === 'no' && hasManifest) return false;

            // Check artifacts filter
            if (currentFilters.artifacts === 'all' && !allArtifacts) return false;
            if (currentFilters.artifacts === 'partial' && allArtifacts) return false;

            return true;
        }'''

html = re.sub(old_matches_pattern, new_matches, html, flags=re.DOTALL)
print("Updated folderMatchesFilters")

with open('web/match-quality-viewer-enhanced.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("\n=== Filter JavaScript Updated ===")
print("All filter functions now work with radio buttons")
