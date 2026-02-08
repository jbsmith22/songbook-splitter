#!/usr/bin/env python3
"""Create embedded JavaScript data file from lineage JSON."""
import json
from pathlib import Path

# Read the lineage data
with open('data/analysis/complete_lineage_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Write as JavaScript constant
output = Path('web/complete_lineage_data_embedded.js')
with open(output, 'w', encoding='utf-8') as f:
    f.write('const LINEAGE_DATA = ')
    json.dump(data, f, indent=2)
    f.write(';\n')

print(f'Created: {output}')
print(f'  Size: {output.stat().st_size / 1024:.1f} KB')
