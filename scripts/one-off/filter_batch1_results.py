#!/usr/bin/env python3
"""
Filter out 557 Standards book from batch1 results.
"""

import json
from pathlib import Path

results_file = Path("verification_results/batch1_results.json")
output_file = Path("verification_results/batch1_results_filtered.json")

with open(results_file, 'r') as f:
    results = json.load(f)

# Filter out 557 Standards
filtered = [r for r in results if "557 Standards" not in r['pdf_path']]

print(f"Original: {len(results)} PDFs")
print(f"Filtered: {len(filtered)} PDFs")
print(f"Removed: {len(results) - len(filtered)} PDFs from 557 Standards book")

with open(output_file, 'w') as f:
    json.dump(filtered, f, indent=2)

print(f"\n✓ Saved filtered results to: {output_file}")
print("\nNow run: py generate_review_page.py")
print("(It will use the filtered results)")
