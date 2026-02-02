"""
Redesign filter controls to be clearer and more intuitive
"""

# Read HTML
with open('web/match-quality-viewer-enhanced.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find and replace the filter controls section
# Look for the filter-controls div
import re

# Find the old filter controls and replace with new radio button design
pattern = r'<div class="filter-controls"[^>]*>.*?</div>\s*</div>'
match = re.search(pattern, html, re.DOTALL)

if match:
    new_filter_controls = '''<div class="filter-controls" style="background: #2d2d30; padding: 15px; margin-bottom: 20px; border-radius: 4px; border-left: 3px solid #569cd6;">
            <div style="font-weight: bold; margin-bottom: 10px; color: #569cd6;">Filter Folders - Show only folders where:</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px; color: #858585; font-size: 12px;">FOLDER NAME:</div>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-name" value="any" checked style="margin-right: 8px;">
                        <span>Any (no filter)</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-name" value="exact" style="margin-right: 8px;">
                        <span>Exact name match</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-name" value="fuzzy" style="margin-right: 8px;">
                        <span>Fuzzy name (different)</span>
                    </label>
                </div>
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px; color: #858585; font-size: 12px;">FILE COUNT:</div>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-count" value="any" checked style="margin-right: 8px;">
                        <span>Any (no filter)</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-count" value="exact" style="margin-right: 8px;">
                        <span>Exact count match</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-count" value="different" style="margin-right: 8px;">
                        <span>Different count</span>
                    </label>
                </div>
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px; color: #858585; font-size: 12px;">MANIFEST:</div>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-manifest" value="any" checked style="margin-right: 8px;">
                        <span>Any (no filter)</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-manifest" value="yes" style="margin-right: 8px;">
                        <span>Has manifest</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-manifest" value="no" style="margin-right: 8px;">
                        <span>No manifest</span>
                    </label>
                </div>
                <div>
                    <div style="font-weight: bold; margin-bottom: 5px; color: #858585; font-size: 12px;">ARTIFACTS:</div>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-artifacts" value="any" checked style="margin-right: 8px;">
                        <span>Any (no filter)</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-artifacts" value="all" style="margin-right: 8px;">
                        <span>All 5 artifacts</span>
                    </label>
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 3px 0;">
                        <input type="radio" name="filter-artifacts" value="partial" style="margin-right: 8px;">
                        <span>Partial/missing</span>
                    </label>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <button class="btn" onclick="applyFilters()" style="background: #0e639c; padding: 8px 16px;">Apply Filters</button>
                <button class="btn" onclick="resetFilters()" style="background: #666; padding: 8px 16px; margin-left: 10px;">Show All</button>
                <span id="filter-result-count" style="margin-left: 20px; color: #858585;"></span>
            </div>
        </div>'''

    html = html[:match.start()] + new_filter_controls + html[match.end():]
    print("Replaced filter controls")
else:
    print("ERROR: Could not find filter controls")

# Update filter JavaScript - replace the currentFilters initialization and functions
# This is more complex, so let's do it step by step

# Write HTML back
with open('web/match-quality-viewer-enhanced.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Filter UI updated to radio buttons")
