"""
Fix duplicate mappings where multiple source PDFs map to the same local folder
"""
import csv
from collections import defaultdict

print('Analyzing duplicate mappings...')

# Read complete mapping
rows = []
with open('data/analysis/complete_songbook_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Find all local folders with multiple source PDFs
local_to_sources = defaultdict(list)
for row in rows:
    if row['status'] in ['MAPPED', 'FUZZY_MATCHED']:
        local_folder = row['local_folder']
        if local_folder != 'UNIDENTIFIED':
            local_to_sources[local_folder].append(row)

# Identify duplicates
duplicates = {k: v for k, v in local_to_sources.items() if len(v) > 1}

print(f'Found {len(duplicates)} local folders with multiple source PDFs\n')

if duplicates:
    print('DUPLICATE MAPPINGS:')
    for local_folder, sources in sorted(duplicates.items()):
        print(f'\n{local_folder} ({len(sources)} sources):')
        for source in sources:
            print(f'  - {source["source_pdf"]} ({source["status"]})')

# Fix: Keep only exact matches, mark fuzzy matches as NO_MAPPING if there's conflict
fixed_rows = []
for row in rows:
    if row['status'] == 'FUZZY_MATCHED':
        local_folder = row['local_folder']
        if local_folder in duplicates:
            # Check if there's a MAPPED (exact) match for this local folder
            sources = duplicates[local_folder]
            has_exact_match = any(s['status'] == 'MAPPED' for s in sources)

            if has_exact_match:
                # Revert this fuzzy match
                print(f"\nReverting fuzzy match: {row['source_pdf']} -> {local_folder}")
                row['local_folder'] = 'UNIDENTIFIED'
                row['s3_folder'] = 'UNIDENTIFIED'
                row['book_id'] = 'NONE'
                row['status'] = 'NO_MAPPING'
            else:
                # Multiple fuzzy matches - keep the best one
                # Find the best match (longest common substring)
                source_name = row['source_pdf'].split('/')[-1].replace('.pdf', '')
                local_name = local_folder.split('/')[-1]

                best_match = None
                best_score = 0

                for source in sources:
                    src_name = source['source_pdf'].split('/')[-1].replace('.pdf', '')
                    # Simple score: length of common characters
                    common = sum(1 for a, b in zip(src_name.lower(), local_name.lower()) if a == b)
                    if common > best_score:
                        best_score = common
                        best_match = source['source_pdf']

                if row['source_pdf'] != best_match:
                    print(f"\nReverting non-best fuzzy match: {row['source_pdf']} -> {local_folder}")
                    print(f"  Best match is: {best_match}")
                    row['local_folder'] = 'UNIDENTIFIED'
                    row['s3_folder'] = 'UNIDENTIFIED'
                    row['book_id'] = 'NONE'
                    row['status'] = 'NO_MAPPING'

    fixed_rows.append(row)

# Save fixed mapping
with open('data/analysis/complete_songbook_mapping.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(fixed_rows)

# Regenerate unmapped CSV
unmapped = [r for r in fixed_rows if r['status'] in ['NO_MAPPING', 'LOCAL_ONLY']]
with open('data/analysis/unmapped_songbooks_only.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unmapped)

print(f'\n{"="*80}')
print('DUPLICATE MAPPING FIX SUMMARY')
print(f'{"="*80}')
print(f'Duplicate local folders found: {len(duplicates)}')
print(f'Rows reverted to NO_MAPPING: {sum(1 for r in fixed_rows if r["status"] == "NO_MAPPING")}')
print(f'Remaining unmapped entries: {len(unmapped)}')
print(f'  - Source PDFs without mapping: {sum(1 for r in unmapped if r["status"] == "NO_MAPPING")}')
print(f'  - Local folders without source: {sum(1 for r in unmapped if r["status"] == "LOCAL_ONLY")}')
