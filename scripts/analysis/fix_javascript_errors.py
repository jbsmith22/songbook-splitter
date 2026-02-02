"""
Fix JavaScript errors in the HTML viewer
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.backup_helper import create_backup, cleanup_old_backups

html_file = 'web/match-quality-viewer-enhanced.html'

# Create backup
create_backup(html_file)
cleanup_old_backups(html_file, keep_count=10)

# Read HTML
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Fix duplicate 'decisions' declaration
# Find all 'let decisions' declarations and remove duplicates
decisions_pattern = r'let decisions = \{\};'
matches = list(re.finditer(decisions_pattern, html))
if len(matches) > 1:
    print(f"Found {len(matches)} 'let decisions' declarations, removing duplicates...")
    # Keep only the first one, remove the rest
    for match in matches[1:]:
        html = html[:match.start()] + '// decisions already declared above' + html[match.end():]
    print("OK Removed duplicate decisions declarations")
else:
    print(f"Found {len(matches)} 'let decisions' declaration(s)")

# 2. Add applyFilters function if missing
if 'function applyFilters()' not in html:
    print("Adding applyFilters function...")
    apply_filters_func = '''
        function applyFilters() {
            // Read all filter checkboxes
            const filters = {
                exactName: document.getElementById('filter-exact-name').checked,
                exactCount: document.getElementById('filter-exact-count').checked,
                hasManifest: document.getElementById('filter-has-manifest').checked,
                allArtifacts: document.getElementById('filter-all-artifacts').checked,
                allFilesMatch: document.getElementById('filter-all-files-match').checked,
                differentCount: document.getElementById('filter-different-count').checked,
                noManifest: document.getElementById('filter-no-manifest').checked,
                partialArtifacts: document.getElementById('filter-partial-artifacts').checked,
                fuzzyName: document.getElementById('filter-fuzzy-name').checked,
                hideCompleted: document.getElementById('filter-hide-completed')?.checked || false
            };

            currentFilters = filters;
            initializeViewer();
        }

        function resetFilters() {
            // Reset all checkboxes to checked except hideCompleted
            document.getElementById('filter-exact-name').checked = true;
            document.getElementById('filter-exact-count').checked = true;
            document.getElementById('filter-has-manifest').checked = true;
            document.getElementById('filter-all-artifacts').checked = true;
            document.getElementById('filter-all-files-match').checked = true;
            document.getElementById('filter-different-count').checked = true;
            document.getElementById('filter-no-manifest').checked = true;
            document.getElementById('filter-partial-artifacts').checked = true;
            document.getElementById('filter-fuzzy-name').checked = true;
            const hideCompletedCheckbox = document.getElementById('filter-hide-completed');
            if (hideCompletedCheckbox) {
                hideCompletedCheckbox.checked = false;
            }
            applyFilters();
        }
'''

    # Insert before the completion tracking code
    completion_tracking_pos = html.find('// Completion tracking with localStorage')
    if completion_tracking_pos > 0:
        html = html[:completion_tracking_pos] + apply_filters_func + '\n\n        ' + html[completion_tracking_pos:]
        print("OK Added applyFilters and resetFilters functions")
    else:
        print("WARNING: Could not find insertion point for applyFilters function")
else:
    print("applyFilters function already exists")

# 3. Make sure initializeViewer exists
if 'function initializeViewer()' not in html:
    print("WARNING: initializeViewer function not found - this will cause errors!")

# Save updated HTML
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html)

print("\nOK JavaScript errors fixed!")
print("Refresh your browser to see the fixes.")
