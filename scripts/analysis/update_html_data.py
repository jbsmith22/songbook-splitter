"""
Properly update the HTML viewer with new match quality data
"""
import json
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.backup_helper import create_backup, cleanup_old_backups

# Load new data
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    new_data = json.load(f)

# Create backup and clean up old ones (keep last 10)
html_file = 'web/match-quality-viewer-enhanced.html'
create_backup(html_file)
cleanup_old_backups(html_file, keep_count=10)

# Read HTML file
with open(html_file, 'r', encoding='utf-8') as f:
    html = f.read()

# Find the line with matchDataEmbedded and replace it
# Split into lines, find the line, and replace it
lines = html.split('\n')
updated_lines = []
found = False

# Create new data string (minified, on one line to match original format)
new_data_str = json.dumps(new_data, separators=(',', ': '))
new_line = f'const matchDataEmbedded = {new_data_str};'

for line in lines:
    if line.strip().startswith('const matchDataEmbedded = '):
        updated_lines.append(new_line)
        found = True
        print(f"Found and replaced matchDataEmbedded (old size: {len(line)} chars, new size: {len(new_line)} chars)")
    else:
        updated_lines.append(line)

new_html = '\n'.join(updated_lines)

# Verify the replacement worked
if found:
    # Save updated HTML
    with open('web/match-quality-viewer-enhanced.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print("OK HTML viewer updated successfully!")
    print(f"  Total matches: {new_data['total_matches']}")
    print(f"  PERFECT: {len(new_data['quality_tiers']['perfect'])}")
    print(f"  EXCELLENT: {len(new_data['quality_tiers']['excellent'])}")
    print(f"  POOR: {len(new_data['quality_tiers']['poor'])}")
else:
    print("ERROR: Could not find matchDataEmbedded in HTML")
    print("HTML unchanged")
