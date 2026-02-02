"""
Add "Mark as Complete" button to each folder item and update filter logic
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

# 1. Find the folderMatchesFilters function and add hideCompleted check
filter_func_pattern = r'function folderMatchesFilters\(folder\) \{([^}]+)\}'
match = re.search(filter_func_pattern, html, re.DOTALL)

if match:
    func_body = match.group(1)
    # Add hideCompleted check at the beginning of the function
    new_func_body = '''
        // Check Hide Completed first
        if (currentFilters.hideCompleted && decisions[folder.local_path]?.completed) {
            return false;
        }
''' + func_body

    new_func = f'function folderMatchesFilters(folder) {{{new_func_body}}}'
    html = html.replace(match.group(0), new_func)
    print("OK Added hideCompleted logic to folderMatchesFilters")
else:
    print("WARNING: Could not find folderMatchesFilters function")

# 2. Update currentFilters to include hideCompleted
filters_init_pattern = r'let currentFilters = \{[^}]+\};'
match = re.search(filters_init_pattern, html)
if match:
    # Replace with version that includes hideCompleted
    new_filters = '''let currentFilters = {
            exactName: true,
            exactCount: true,
            hasManifest: true,
            allArtifacts: true,
            allFilesMatch: true,
            differentCount: true,
            noManifest: true,
            partialArtifacts: true,
            fuzzyName: true,
            hideCompleted: false
        };'''
    html = html.replace(match.group(0), new_filters)
    print("OK Updated currentFilters with hideCompleted")

# 3. Add completion badge to folder rendering
# Find where folder HTML is built (look for folder-badges div)
# Add after the quality tier badge
badge_insertion = '''
                    // Add completion badge if marked as completed
                    if (decisions[folder.local_path]?.completed) {
                        badgesHTML += '<span class="folder-badge badge-completed" style="background: #4ec9b0; color: #000;">COMPLETED</span>';
                    }'''

# Find the location after quality tier badge is added
tier_badge_pattern = r"(badgesHTML \+= `<span class=\"folder-badge badge-\$\{tier\}\">.*?</span>`;)"
match = re.search(tier_badge_pattern, html, re.DOTALL)
if match:
    insert_pos = html.find(match.group(0)) + len(match.group(0))
    html = html[:insert_pos] + '\n                    ' + badge_insertion + html[insert_pos:]
    print("OK Added completion badge to folder display")

# 4. Add "Mark as Complete" button in details panel
# Find where details header buttons are (after folder path)
details_button_html = '''
                <button class="btn" onclick="toggleComplete(selectedFolder.local_path)"
                    style="padding: 6px 12px; font-size: 12px; background: #4ec9b0; color: #000; font-weight: bold;">
                    <span id="complete-btn-text">Mark as Complete</span>
                </button>'''

# Find details-header and add button
details_header_pattern = r'(<div class="details-header">[\s\S]*?<div style="font-size: 14px; color: #858585;">)([\s\S]*?</div>[\s\S]*?)(</div>)'
match = re.search(details_header_pattern, html)
if match:
    # Insert button before the closing </div> of details-header
    new_header = match.group(1) + match.group(2) + details_button_html + '\n            ' + match.group(3)
    html = html.replace(match.group(0), new_header)
    print("OK Added 'Mark as Complete' button to details panel")
else:
    print("WARNING: Could not find details-header to add button")

# 5. Update the button text when folder changes
# Find showDetails function and add logic to update button text
show_details_func = html.find('function showDetails(folder')
if show_details_func > 0:
    # Find the end of the function
    func_end = html.find('\n    }', show_details_func)
    if func_end > 0:
        update_button_code = '''

        // Update complete button text
        const isCompleted = decisions[folder.local_path]?.completed;
        const btn = document.getElementById('complete-btn-text');
        if (btn) {
            btn.textContent = isCompleted ? 'Unmark' : 'Mark as Complete';
        }'''
        html = html[:func_end] + update_button_code + html[func_end:]
        print("OK Added button text update to showDetails function")

# Save updated HTML
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html)

print("\nOK Folder completion button and filtering added!")
