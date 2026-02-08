"""
Fix the bad fuzzy matches - revert incorrect matches to NO_MAPPING/LOCAL_ONLY
"""
import csv

print('Fixing bad fuzzy matches...')

# Read the complete mapping
complete_rows = []
with open('data/analysis/complete_songbook_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        complete_rows.append(row)

# Define the bad matches to revert (source_pdf -> should be NO_MAPPING)
bad_source_pdfs = [
    'Elton John/Elton John - The Ultimate Collection Vol 2.pdf',
    'Elvis Presley/Elvis Presley - The Compleat _PVG Book_.pdf',
    'Eric Clapton/Eric Clapton - The Cream Of Clapton.pdf',
    'Mamas and the Papas/Mamas And The Papas - Songbook _PVG_.pdf',
    '_Broadway Shows/Various Artists - 25th Annual Putnam County Spelling Bee.pdf',
    '_Movie and TV/Various Artists - Complete TV And Film.pdf'
]

# Track local folders that need to be restored as LOCAL_ONLY
bad_local_folders = []

# Revert bad source PDFs
reverted_count = 0
for row in complete_rows:
    if row['status'] == 'FUZZY_MATCHED' and row['source_pdf'] in bad_source_pdfs:
        print(f"Reverting: {row['source_pdf']}")
        print(f"  Was matched to: {row['local_folder']}")
        bad_local_folders.append(row['local_folder'])
        row['local_folder'] = 'UNIDENTIFIED'
        row['s3_folder'] = 'UNIDENTIFIED'
        row['book_id'] = 'NONE'
        row['status'] = 'NO_MAPPING'
        reverted_count += 1

print(f'\nReverted {reverted_count} bad source PDF matches')

# Now add back the local folders that were incorrectly matched
added_count = 0
for local_folder in bad_local_folders:
    # Check if this local folder already exists in another row
    exists = any(r['local_folder'] == local_folder for r in complete_rows)
    if not exists:
        # Need to look up the s3_folder for this local
        # Search through rows that might have this local
        s3_folder = 'UNIDENTIFIED'

        # Add as LOCAL_ONLY
        complete_rows.append({
            'source_pdf': 'UNIDENTIFIED',
            'local_folder': local_folder,
            's3_folder': s3_folder,
            'book_id': 'NONE',
            'status': 'LOCAL_ONLY'
        })
        added_count += 1
        print(f"Restored LOCAL_ONLY: {local_folder}")

print(f'\nRestored {added_count} local folders as LOCAL_ONLY')

# Save updated complete mapping
with open('data/analysis/complete_songbook_mapping.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(complete_rows)

print('Complete mapping updated')

# Regenerate unmapped-only CSV
print('\nRegenerating unmapped_songbooks_only.csv...')

unmapped_only = []
matched_locals = set()

# Collect all matched locals
for row in complete_rows:
    if row['status'] in ['MAPPED', 'FUZZY_MATCHED']:
        matched_locals.add(row['local_folder'])

# Add unmapped source PDFs and unmatched local folders
for row in complete_rows:
    if row['status'] == 'NO_MAPPING':
        unmapped_only.append(row)
    elif row['status'] == 'LOCAL_ONLY':
        if row['local_folder'] not in matched_locals:
            unmapped_only.append(row)

print(f'Filtered to {len(unmapped_only)} unmapped entries')

# Save unmapped-only CSV
with open('data/analysis/unmapped_songbooks_only.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(unmapped_only)

print('Unmapped-only CSV regenerated')

# Print summary
print(f'\n{"="*80}')
print('BAD FUZZY MATCHES FIXED')
print(f'{"="*80}')
print(f'Reverted bad matches: {reverted_count}')
print(f'Restored LOCAL_ONLY folders: {added_count}')
print(f'Remaining unmapped entries: {len(unmapped_only)}')

# Count by status
source_unmapped = sum(1 for r in unmapped_only if r['status'] == 'NO_MAPPING')
local_unmapped = sum(1 for r in unmapped_only if r['status'] == 'LOCAL_ONLY')
print(f'  - Source PDFs without matches: {source_unmapped}')
print(f'  - Local folders without source: {local_unmapped}')

# Count good fuzzy matches still in place
good_fuzzy = sum(1 for r in complete_rows if r['status'] == 'FUZZY_MATCHED')
print(f'  - Good fuzzy matches kept: {good_fuzzy}')
