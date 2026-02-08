"""
Update HTML viewer with fresh merged decisions and match quality data
"""
import json
import re
from datetime import datetime

print("Loading merged decisions...")
with open('reconciliation_decisions_2026-02-02_merged.json', 'r') as f:
    decisions_data = json.load(f)

print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

print("Reading HTML template...")
with open('web/match-quality-viewer-enhanced.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# Prepare JSON strings with proper escaping
match_data_json = json.dumps(match_data)
decisions_json = json.dumps(decisions_data.get("decisions", {}))

# Find the matchDataEmbedded section
match_start = html_content.find('const matchDataEmbedded = ')
if match_start == -1:
    raise ValueError("Could not find matchDataEmbedded in HTML")

# Find the end of matchDataEmbedded (next semicolon at start of line)
match_end = html_content.find('\n        ', match_start + 1)
if match_end == -1:
    raise ValueError("Could not find end of matchDataEmbedded")

# Replace matchDataEmbedded
html_content = (
    html_content[:match_start] +
    f'const matchDataEmbedded = {match_data_json};\n' +
    html_content[match_end:]
)

# Find and replace embeddedDecisions
decisions_start = html_content.find('const embeddedDecisions = {};')
if decisions_start != -1:
    html_content = (
        html_content[:decisions_start] +
        f'const embeddedDecisions = {decisions_json};' +
        html_content[decisions_start + len('const embeddedDecisions = {};'):]
    )

# Add timestamp comment
timestamp = datetime.now().isoformat()
comment_pos = html_content.find('<!-- Match Quality Viewer -->')
if comment_pos != -1:
    html_content = (
        html_content[:comment_pos] +
        f'<!-- Match Quality Viewer - Updated {timestamp} with 248 folders -->' +
        html_content[comment_pos + len('<!-- Match Quality Viewer -->'):]
    )

# Save updated HTML
output_file = 'web/match-quality-viewer-enhanced.html'
backup_file = f'web/match-quality-viewer-enhanced.backup.{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

# Create backup
print(f"Creating backup: {backup_file}")
with open(backup_file, 'w', encoding='utf-8') as f:
    with open('web/match-quality-viewer-enhanced.html', 'r', encoding='utf-8') as original:
        f.write(original.read())

# Write updated HTML
print(f"Writing updated HTML: {output_file}")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n{'='*70}")
print("HTML VIEWER UPDATED")
print(f"{'='*70}")
print(f"Match data: {len(match_data.get('all_folders', []))} folders")
print(f"Decisions: {len(decisions_data.get('decisions', {}))} folders")
print()
print("Quality tiers:")
for tier, folders in match_data.get('quality_tiers', {}).items():
    print(f"  {tier.upper():12} {len(folders):3} folders")
print()
print(f"Backup saved to: {backup_file}")
print(f"Updated file: {output_file}")
print()
print("Open the HTML file in your browser to start reconciling!")
print("The viewer now has:")
print("  - Current match quality data (248 folders)")
print("  - Fresh analysis with previous manual decisions preserved")
print("  - 60 conflicts flagged for review")

print("\nUpdate complete!")
