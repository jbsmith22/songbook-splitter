"""
Match LOCAL_ONLY folders to NO_MAPPING source PDFs by exact name matching
"""
import csv
import re

def normalize_for_matching(text):
    """Normalize for case-insensitive matching"""
    return text.lower().replace(' ', '').replace('_', '').replace('-', '')

print('Matching LOCAL_ONLY folders to NO_MAPPING source PDFs...\n')

# Read provenance mapping
rows = []
with open('data/analysis/provenance_verified_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Get LOCAL_ONLY and NO_MAPPING entries
local_only = {r['local_folder']: r for r in rows if r['status'] == 'LOCAL_ONLY'}
no_mapping = {r['source_pdf']: r for r in rows if r['status'] == 'NO_MAPPING'}

print(f'LOCAL_ONLY folders: {len(local_only)}')
print(f'NO_MAPPING source PDFs: {len(no_mapping)}')

# Match by normalized name
matches = []
for local_folder, local_row in local_only.items():
    local_normalized = normalize_for_matching(local_folder)

    for source_pdf, source_row in no_mapping.items():
        # Remove .pdf extension and normalize
        source_normalized = normalize_for_matching(source_pdf.replace('.pdf', ''))

        if local_normalized == source_normalized:
            matches.append({
                'source_pdf': source_pdf,
                'local_folder': local_folder,
                'source_row': source_row,
                'local_row': local_row
            })
            print(f'MATCH: {source_pdf}')
            print(f'    -> {local_folder}')
            break

print(f'\nFound {len(matches)} matches')

# Update rows with matches
matched_sources = {m['source_pdf'] for m in matches}
matched_locals = {m['local_folder'] for m in matches}

updated_rows = []
for row in rows:
    if row['status'] == 'NO_MAPPING' and row['source_pdf'] in matched_sources:
        # Find the match
        match = next(m for m in matches if m['source_pdf'] == row['source_pdf'])
        row['local_folder'] = match['local_folder']
        row['s3_folder'] = match['local_row']['s3_folder']
        row['book_id'] = match['local_row']['book_id']
        row['status'] = 'MATCHED_MANUAL'
    elif row['status'] == 'LOCAL_ONLY' and row['local_folder'] in matched_locals:
        # Skip - this will be replaced by the source PDF row above
        continue

    updated_rows.append(row)

# Save updated mapping
with open('data/analysis/provenance_verified_mapping_updated.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(updated_rows)

# Regenerate unmapped CSV
unmapped = [r for r in updated_rows if r['status'] in ['NO_MAPPING', 'LOCAL_ONLY']]
with open('data/analysis/provenance_unmapped_only.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unmapped)

print(f'\n{"="*80}')
print('MATCHING SUMMARY')
print(f'{"="*80}')
print(f'Matches found: {len(matches)}')
print(f'Updated mapping saved to: provenance_verified_mapping.csv')
print(f'\nUpdated status:')
print(f'  VERIFIED: {sum(1 for r in updated_rows if r["status"] == "VERIFIED")}')
print(f'  MATCHED_MANUAL: {sum(1 for r in updated_rows if r["status"] == "MATCHED_MANUAL")}')
print(f'  NO_MAPPING: {sum(1 for r in updated_rows if r["status"] == "NO_MAPPING")}')
print(f'  LOCAL_ONLY: {sum(1 for r in updated_rows if r["status"] == "LOCAL_ONLY")}')
print(f'\nRemaining unmapped: {len(unmapped)}')
