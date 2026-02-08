"""
Create properly formatted file for HTML viewer import
"""
import json

print("Loading merged decisions...")
with open('reconciliation_decisions_2026-02-02_merged.json', 'r') as f:
    merged_data = json.load(f)

# Extract just the decisions in the format the viewer expects
decisions = merged_data.get('decisions', {})

# The viewer expects the format: {"decisions": {...}}
output_data = {
    "timestamp": "2026-02-02",
    "version": "1.0",
    "decisions": decisions
}

output_file = 'reconciliation_decisions_2026-02-02_for_import.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

print(f"Created import file: {output_file}")
print(f"Folders: {len(decisions)}")
print(f"Total file decisions: {sum(len(f.get('fileDecisions', {})) for f in decisions.values())}")
print("\nYou can now import this file in the HTML viewer.")
