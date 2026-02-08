"""
Update complete_provenance_viewer.html with fresh data from complete_provenance_database.json
"""
import json
import re
from pathlib import Path
from datetime import datetime

# Load the fresh provenance data
print("Loading provenance database...")
with open('data/analysis/complete_provenance_database.json', 'r', encoding='utf-8') as f:
    provenance_data = json.load(f)

print(f"  - {provenance_data['statistics']['total']} songbooks")
print(f"  - Complete: {provenance_data['statistics']['complete']}")
print(f"  - Incomplete: {provenance_data['statistics']['incomplete']}")

# Read the HTML viewer
html_file = Path('web/viewers/complete_provenance_viewer.html')
print(f"\nReading {html_file}...")
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find and replace the embeddedData
start_marker = 'const embeddedData = '
start_idx = html_content.find(start_marker)
if start_idx == -1:
    print("ERROR: Could not find embeddedData in HTML")
    exit(1)

# Find the end of the JSON object (find the matching semicolon after the object)
# The embeddedData is followed by a semicolon
brace_count = 0
in_string = False
escape_next = False
end_idx = start_idx + len(start_marker)

for i, char in enumerate(html_content[end_idx:], start=end_idx):
    if escape_next:
        escape_next = False
        continue
    if char == '\\':
        escape_next = True
        continue
    if char == '"' and not escape_next:
        in_string = not in_string
        continue
    if in_string:
        continue
    if char == '{':
        brace_count += 1
    elif char == '}':
        brace_count -= 1
        if brace_count == 0:
            end_idx = i + 1
            break

# Replace the embedded data
before = html_content[:start_idx]
after = html_content[end_idx:]
new_data_line = f'{start_marker}{json.dumps(provenance_data)}'

html_content = before + new_data_line + after

# Update the title with new count
old_title_pattern = r'<title>Complete Songbook Provenance Viewer - \d+ Books</title>'
new_title = f"<title>Complete Songbook Provenance Viewer - {provenance_data['statistics']['total']} Books</title>"
html_content = re.sub(old_title_pattern, new_title, html_content)

# Write the updated HTML
print(f"Writing updated {html_file}...")
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ Updated provenance viewer with fresh data")
print(f"  - Generated at: {provenance_data['generated_at']}")
print(f"  - Total: {provenance_data['statistics']['total']} songbooks")
print(f"  - Complete: {provenance_data['statistics']['complete']}")
print(f"  - Has TOC: {provenance_data['statistics']['has_toc']}")
print(f"  - Has manifest: {provenance_data['statistics']['has_manifest']}")
