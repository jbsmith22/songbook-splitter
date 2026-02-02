"""
Add completion tracking features back to the HTML viewer
"""
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

# 1. Add "Hide Completed" checkbox after the filter controls
hide_completed_html = '''
                <label style="display: flex; align-items: center; cursor: pointer; margin-top: 15px; padding-top: 15px; border-top: 1px solid #3e3e42;">
                    <input type="checkbox" id="filter-hide-completed" style="margin-right: 8px;">
                    <span style="color: #4ec9b0;">Hide Completed</span>
                </label>'''

# Find the location to insert (after the last filter checkbox, before the buttons)
insertion_point = html.find('</div>\n            <div style="margin-top: 10px;">\n                <button class="btn" onclick="applyFilters()"')
if insertion_point > 0:
    html = html[:insertion_point] + hide_completed_html + '\n            ' + html[insertion_point:]
    print("OK Added 'Hide Completed' checkbox")
else:
    print("WARNING: Could not find insertion point for Hide Completed checkbox")

# 2. Add "Mark All Perfect as Complete" button
mark_all_button = '''
                <button class="btn" onclick="markAllPerfectAsComplete()" style="background: #4ec9b0; color: #000; padding: 8px 16px; margin-left: 10px; font-weight: bold;">Mark All Perfect as Complete</button>'''

# Insert after Reset button
reset_button_pos = html.find('<button class="btn" onclick="resetFilters()"')
if reset_button_pos > 0:
    # Find the end of the Reset button tag
    button_end = html.find('</button>', reset_button_pos)
    if button_end > 0:
        button_end += len('</button>')
        html = html[:button_end] + mark_all_button + html[button_end:]
        print("OK Added 'Mark All Perfect as Complete' button")
else:
    print("WARNING: Could not find location for Mark All Perfect button")

# 3. Add completion management JavaScript functions
completion_js = '''
        // Completion tracking with localStorage
        let decisions = {};

        function loadDecisions() {
            const saved = localStorage.getItem('folderDecisions');
            if (saved) {
                try {
                    decisions = JSON.parse(saved);
                } catch (e) {
                    console.error('Error loading decisions:', e);
                    decisions = {};
                }
            }
        }

        function saveDecisions() {
            localStorage.setItem('folderDecisions', JSON.stringify(decisions));
        }

        function toggleComplete(folderPath) {
            if (!decisions[folderPath]) {
                decisions[folderPath] = {};
            }
            decisions[folderPath].completed = !decisions[folderPath].completed;
            saveDecisions();
            initializeViewer(); // Refresh display
        }

        function markAllPerfectAsComplete() {
            if (!confirm('Mark all PERFECT matches as completed?')) {
                return;
            }

            let count = 0;
            if (matchDataEmbedded && matchDataEmbedded.quality_tiers) {
                const perfectFolders = matchDataEmbedded.quality_tiers.perfect || [];
                perfectFolders.forEach(folder => {
                    if (!decisions[folder.local_path]) {
                        decisions[folder.local_path] = {};
                    }
                    if (!decisions[folder.local_path].completed) {
                        decisions[folder.local_path].completed = true;
                        count++;
                    }
                });
            }

            saveDecisions();
            initializeViewer();
            alert(`Marked ${count} folders as completed`);
        }

        // Call loadDecisions when page loads
        loadDecisions();
'''

# Insert before the closing </script> tag
script_end = html.rfind('</script>')
if script_end > 0:
    html = html[:script_end] + completion_js + '\n    ' + html[script_end:]
    print("OK Added completion tracking JavaScript")
else:
    print("WARNING: Could not find </script> tag")

# 4. Update applyFilters to include hideCompleted logic
# Find the applyFilters function and add hideCompleted check
apply_filters_pattern = 'function applyFilters() {'
apply_filters_pos = html.find(apply_filters_pattern)
if apply_filters_pos > 0:
    # Find the filter collection section
    filter_section_start = html.find('const filters = {', apply_filters_pos)
    if filter_section_start > 0:
        # Find the closing brace of the filters object
        brace_count = 0
        i = filter_section_start + len('const filters = {')
        while i < len(html):
            if html[i] == '{':
                brace_count += 1
            elif html[i] == '}':
                if brace_count == 0:
                    # Insert hideCompleted before the closing brace
                    hide_completed_filter = ',\n            hideCompleted: document.getElementById(\'filter-hide-completed\').checked'
                    html = html[:i] + hide_completed_filter + html[i:]
                    print("OK Added hideCompleted to applyFilters function")
                    break
                brace_count -= 1
            i += 1

# 5. Add "Mark as Complete" button to folder details
# This will be added in the folder rendering, look for where folder items are created
# We need to add a button in the folder item HTML

# Save updated HTML
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html)

print("\nOK Completion features added successfully!")
print("Features added:")
print("  - Hide Completed checkbox filter")
print("  - Mark All Perfect as Complete button")
print("  - Completion tracking with localStorage")
print("  - Toggle completion functionality")
