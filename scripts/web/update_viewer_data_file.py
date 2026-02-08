"""
Update the viewer by creating a separate data.js file instead of embedding
"""
import json
from pathlib import Path

# Load the match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

# Load the decisions file
print("Loading decisions data...")
with open('reconciliation_decisions_2026-02-02_correct.json', 'r', encoding='utf-8') as f:
    decisions_data = json.load(f)

# Create a data.js file that the HTML can load
data_js_content = f"""// Auto-generated match quality and decisions data
const matchDataEmbedded = {json.dumps(match_data)};
const decisionsDataEmbedded = {json.dumps(decisions_data)};

console.log('Data loaded from external file');
console.log('Match data folders:', matchDataEmbedded.total_matches);
console.log('Decisions:', Object.keys(decisionsDataEmbedded.decisions || {{}}).length);
"""

output_file = 'web/match-quality-data.js'
print(f"Writing {output_file}...")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(data_js_content)

print(f"\nDone! Created {output_file}")
print(f"  - {match_data['total_matches']} folders")
print(f"  - PERFECT: {len(match_data['quality_tiers']['perfect'])}")
print(f"  - EXCELLENT: {len(match_data['quality_tiers']['excellent'])}")
print(f"  - GOOD: {len(match_data['quality_tiers']['good'])}")
print(f"  - FAIR: {len(match_data['quality_tiers']['fair'])}")
print(f"  - WEAK: {len(match_data['quality_tiers']['weak'])}")
print(f"  - POOR: {len(match_data['quality_tiers']['poor'])}")
print(f"  - {len(decisions_data['decisions'])} decisions")
print(f"\nNow update the HTML to load this file with:")
print(f'  <script src="match-quality-data.js"></script>')
