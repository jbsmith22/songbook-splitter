"""
Sort the auto_rename_decisions.json file alphabetically by top-level folder
"""
import json
from collections import OrderedDict

def sort_decisions_json(input_file, output_file):
    """Sort decisions by top-level folder alphabetically"""
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        decisions = json.load(f)

    print(f"Sorting {len(decisions)} folders alphabetically...")

    # Sort by folder path
    sorted_decisions = OrderedDict(sorted(decisions.items(), key=lambda x: x[0].lower()))

    print(f"Writing sorted data to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sorted_decisions, f, indent=2)

    print("Done!")
    print(f"\nSorted decisions saved to: {output_file}")

if __name__ == '__main__':
    input_file = 'data/analysis/auto_rename_decisions.json'
    output_file = 'data/analysis/auto_rename_decisions.json'

    sort_decisions_json(input_file, output_file)
