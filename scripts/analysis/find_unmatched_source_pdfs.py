"""
Find source PDFs in SheetMusic that don't have PERFECT matches
"""
from pathlib import Path
import json
import csv
import boto3

# Load data
sheet_music = Path('d:/Work/songbook-splitter/SheetMusic')
all_source_pdfs = sorted([p.relative_to(sheet_music).as_posix() for p in sheet_music.glob('**/*.pdf')])

print(f'Total source PDFs in SheetMusic: {len(all_source_pdfs)}')

# Get PERFECT matches (archived folders)
with open('data/analysis/archived_perfect_folders.json', 'r') as f:
    archive_log = json.load(f)

print(f'Archived PERFECT folders: {len(archive_log["folders"])}')

# Get source URIs from archived folders via DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

perfect_source_pdfs = set()

print('\nQuerying DynamoDB for archived folder source PDFs...')
for i, folder in enumerate(archive_log['folders']):
    if (i + 1) % 50 == 0:
        print(f'  Queried {i+1}/{len(archive_log["folders"])}...')

    book_id = folder['book_id']
    try:
        response = table.query(
            KeyConditionExpression='book_id = :bid',
            ExpressionAttributeValues={':bid': book_id},
            ScanIndexForward=False,
            Limit=1
        )
        if response['Items']:
            source_uri = response['Items'][0].get('source_pdf_uri', '')
            if source_uri:
                # Extract path: s3://jsmith-output/path -> path
                path = source_uri.replace('s3://jsmith-output/', '')
                perfect_source_pdfs.add(path)
    except Exception as e:
        pass

print(f'\nFound {len(perfect_source_pdfs)} source PDFs with PERFECT matches')

# Find PDFs without PERFECT matches
unmatched_pdfs = []

print('\nComparing all source PDFs against PERFECT matches...')
for pdf_path in all_source_pdfs:
    # Normalize path for comparison
    pdf_norm = pdf_path.lower().replace('\\', '/').replace(' ', '').replace('_', '').replace('-', '')

    found_perfect = False
    for perfect_path in perfect_source_pdfs:
        perfect_norm = perfect_path.lower().replace('\\', '/').replace(' ', '').replace('_', '').replace('-', '')

        # Check if the filename matches (extract just the filename)
        pdf_filename = pdf_path.split('/')[-1].lower().replace('.pdf', '')
        perfect_filename = perfect_path.split('/')[-1].lower().replace('.pdf', '')

        # Normalize filenames
        pdf_filename_norm = pdf_filename.replace(' ', '').replace('_', '').replace('-', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')
        perfect_filename_norm = perfect_filename.replace(' ', '').replace('_', '').replace('-', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '')

        if pdf_filename_norm == perfect_filename_norm:
            found_perfect = True
            break

    if not found_perfect:
        unmatched_pdfs.append(pdf_path)

print(f'\n{"="*80}')
print(f'RESULTS')
print(f'{"="*80}')
print(f'Source PDFs without PERFECT matches: {len(unmatched_pdfs)}')
print()

# Save to CSV
csv_file = 'data/analysis/unmatched_source_pdfs.csv'
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Source PDF Path', 'Folder', 'Filename'])

    for pdf_path in unmatched_pdfs:
        parts = pdf_path.split('/')
        folder = parts[0] if len(parts) > 1 else ''
        filename = parts[-1]
        writer.writerow([pdf_path, folder, filename])

print(f'Saved {len(unmatched_pdfs)} unmatched PDFs to: {csv_file}')
print()

# Show first 31
print('First 31 unmatched source PDFs:')
for i, pdf in enumerate(unmatched_pdfs[:31], 1):
    print(f'{i:2d}. {pdf}')

if len(unmatched_pdfs) > 31:
    print(f'... and {len(unmatched_pdfs) - 31} more')
