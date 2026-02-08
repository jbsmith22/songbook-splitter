"""
Regenerate unmapped songbooks only CSV from complete mapping
"""
import csv

print('Regenerating unmapped songbooks CSV...')

# Read complete mapping
rows = []
with open('data/analysis/complete_songbook_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Filter to unmapped only
unmapped = []
for row in rows:
    if row['status'] in ['NO_MAPPING', 'LOCAL_ONLY']:
        unmapped.append(row)

print(f'Found {len(unmapped)} unmapped entries')

# Save unmapped CSV
with open('data/analysis/unmapped_songbooks_only.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unmapped)

print(f'Saved to: data/analysis/unmapped_songbooks_only.csv')

# Print breakdown
no_mapping = sum(1 for r in unmapped if r['status'] == 'NO_MAPPING')
local_only = sum(1 for r in unmapped if r['status'] == 'LOCAL_ONLY')

print(f'\nBreakdown:')
print(f'  Source PDFs without mapping: {no_mapping}')
print(f'  Local folders without source: {local_only}')
