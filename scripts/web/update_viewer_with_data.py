"""
Update the HTML viewer with fresh match quality data
"""
import json
from pathlib import Path
import re

# Load the match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

# Load the decisions file
print("Loading decisions data...")
with open('reconciliation_decisions_2026-02-02_correct.json', 'r', encoding='utf-8') as f:
    decisions_data = json.load(f)

# Read the HTML file
html_file = 'web/match-quality-viewer-enhanced.html'
print(f"Reading {html_file}...")
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Find and replace the matchDataEmbedded line
# Format: const matchDataEmbedded = {...};
start_marker = 'const matchDataEmbedded = '
start_idx = html_content.find(start_marker)
if start_idx == -1:
    print("ERROR: Could not find matchDataEmbedded")
    exit(1)

# Find the end of this line (semicolon)
end_idx = html_content.find(';', start_idx)
if end_idx == -1:
    print("ERROR: Could not find end of matchDataEmbedded line")
    exit(1)

# Replace the line
before = html_content[:start_idx]
after = html_content[end_idx + 1:]
new_match_line = f'{start_marker}{json.dumps(match_data)};'

html_content = before + new_match_line + after

print(f"Writing updated {html_file}...")
with open(html_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"\n✓ Updated HTML viewer with fresh data")
print(f"  - {match_data['total_matches']} folders")
print(f"  - PERFECT: {len(match_data['quality_tiers']['perfect'])}")
print(f"  - EXCELLENT: {len(match_data['quality_tiers']['excellent'])}")
print(f"  - GOOD: {len(match_data['quality_tiers']['good'])}")
print(f"  - FAIR: {len(match_data['quality_tiers']['fair'])}")
print(f"  - WEAK: {len(match_data['quality_tiers']['weak'])}")
print(f"  - POOR: {len(match_data['quality_tiers']['poor'])}")
print(f"  - {len(decisions_data['decisions'])} decisions embedded")
