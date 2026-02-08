"""
Apply fuzzy matching to unmapped source PDFs and update the comprehensive CSV
"""
import csv
import json
import re
from pathlib import Path

print('Applying fuzzy matching to unmapped source PDFs...')

# Read the unmapped CSV
unmapped_rows = []
with open('data/analysis/unmapped_songbooks_only.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        unmapped_rows.append(row)

# Get the 17 source PDFs with NO_MAPPING status
source_pdfs = [r for r in unmapped_rows if r['status'] == 'NO_MAPPING']
print(f'Found {len(source_pdfs)} source PDFs needing fuzzy matching')

# Get all local folders from the CSV
local_folders = [r for r in unmapped_rows if r['status'] == 'LOCAL_ONLY']
print(f'Found {len(local_folders)} local folders available for matching')

# Fuzzy matching function
def normalize_alphanumeric(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())

# Store matches
matches = []

for source_row in source_pdfs:
    source_pdf = source_row['source_pdf']
    source_filename = source_pdf.split('/')[-1].replace('.pdf', '')
    source_norm = normalize_alphanumeric(source_filename)

    best_match = None
    best_score = 0

    for local_row in local_folders:
        local_folder = local_row['local_folder']
        local_filename = local_folder.split('/')[-1]
        local_norm = normalize_alphanumeric(local_filename)

        # Calculate match score
        if source_norm == local_norm:
            score = 1.0
        elif source_norm in local_norm:
            score = len(source_norm) / len(local_norm)
        elif local_norm in source_norm:
            score = len(local_norm) / len(source_norm)
        else:
            # Character overlap
            overlap = len(set(source_norm) & set(local_norm))
            total = len(set(source_norm) | set(local_norm))
            score = overlap / total if total > 0 else 0

        if score > best_score:
            best_score = score
            best_match = local_row

    # Only accept high-confidence matches (>= 0.7)
    if best_match and best_score >= 0.7:
        matches.append({
            'source_pdf': source_pdf,
            'local_folder': best_match['local_folder'],
            's3_folder': best_match['s3_folder'],
            'score': best_score
        })
        print(f'MATCH ({best_score:.2f}): {source_filename}')
        print(f'     -> {best_match["local_folder"]}')

print(f'\nTotal matches found: {len(matches)}')

# Now update the complete mapping CSV
print('\nUpdating complete_songbook_mapping.csv...')

# Read the complete mapping
complete_rows = []
with open('data/analysis/complete_songbook_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        complete_rows.append(row)

# Create a lookup dict for the matches
match_lookup = {m['source_pdf']: m for m in matches}

# Update rows
updated_count = 0
for row in complete_rows:
    if row['status'] == 'NO_MAPPING' and row['source_pdf'] in match_lookup:
        match = match_lookup[row['source_pdf']]
        row['local_folder'] = match['local_folder']
        row['s3_folder'] = match['s3_folder']
        row['status'] = 'FUZZY_MATCHED'
        updated_count += 1
        print(f"Updated: {row['source_pdf']}")

print(f'\nUpdated {updated_count} rows in complete mapping')

# Save updated complete mapping
with open('data/analysis/complete_songbook_mapping.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(complete_rows)

print('Complete mapping updated')

# Now regenerate the unmapped-only CSV
print('\nRegenerating unmapped_songbooks_only.csv...')

unmapped_only = []
matched_locals = set()

# First pass: add all unmapped source PDFs and track which locals got matched
for row in complete_rows:
    if row['status'] == 'NO_MAPPING':
        unmapped_only.append(row)
    elif row['status'] == 'FUZZY_MATCHED':
        # Track the local folder that got matched
        matched_locals.add(row['local_folder'])

# Second pass: add LOCAL_ONLY rows that weren't matched
for row in complete_rows:
    if row['status'] == 'LOCAL_ONLY' and row['local_folder'] not in matched_locals:
        unmapped_only.append(row)

print(f'Filtered to {len(unmapped_only)} unmapped entries')

# Save unmapped-only CSV
with open('data/analysis/unmapped_songbooks_only.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unmapped_only)

print('Unmapped-only CSV regenerated')

print(f'\n{"="*80}')
print('FUZZY MATCHING COMPLETE')
print(f'{"="*80}')
print(f'Fuzzy matches applied: {len(matches)}')
print(f'Complete mapping updated: {updated_count} rows')
print(f'Remaining unmapped entries: {len(unmapped_only)}')
print(f'  - Source PDFs without matches: {sum(1 for r in unmapped_only if r["status"] == "NO_MAPPING")}')
print(f'  - Local folders without source: {sum(1 for r in unmapped_only if r["status"] == "LOCAL_ONLY")}')
