"""
Verify folder provenance based on DynamoDB source_pdf_uri records
This shows which source PDF was ACTUALLY used to create each folder
"""
import csv
import boto3
from pathlib import Path

dynamodb = boto3.resource('dynamodb')
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('Querying DynamoDB for source provenance...\n')

# Get all DynamoDB records
all_records = []
response = TABLE.scan()
while True:
    all_records.extend(response.get('Items', []))
    if 'LastEvaluatedKey' not in response:
        break
    response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

print(f'Found {len(all_records)} DynamoDB records\n')

# Extract provenance mappings
# Map by normalized filename since source_pdf_uri points to S3, not SheetMusic
import re

def normalize_name(name):
    """Remove brackets, underscores, special chars for matching"""
    return re.sub(r'[^a-z0-9]', '', name.lower())

provenance_by_name = {}  # normalized_name -> record
for record in all_records:
    source_uri = record.get('source_pdf_uri', '')
    if source_uri:
        # Extract filename from S3 URI
        # Format: s3://jsmith-output/Artist/Artist - Album [format]
        filename = source_uri.split('/')[-1]
        normalized = normalize_name(filename)

        provenance_by_name[normalized] = {
            'book_id': record.get('book_id'),
            'local_path': record.get('local_output_path', ''),
            's3_path': record.get('s3_output_path', ''),
            'source_uri': source_uri,
            'source_filename': filename
        }

print(f'Found {len(provenance_by_name)} source PDFs with provenance records\n')

# Get all source PDFs in SheetMusic
sheet_music = Path('d:/Work/songbook-splitter/SheetMusic')
all_source_pdfs = {}
for pdf_path in sheet_music.glob('**/*.pdf'):
    relative = pdf_path.relative_to(sheet_music).as_posix()
    all_source_pdfs[relative] = str(pdf_path)

print(f'Found {len(all_source_pdfs)} source PDFs in SheetMusic\n')

# Build definitive mapping based on provenance
rows = []
matched_locals = set()

for source_pdf in sorted(all_source_pdfs.keys()):
    # Normalize the source PDF filename for matching (remove .pdf extension first)
    source_filename = source_pdf.split('/')[-1].replace('.pdf', '')
    source_normalized = normalize_name(source_filename)

    if source_normalized in provenance_by_name:
        prov = provenance_by_name[source_normalized]
        local_path = prov['local_path']
        s3_path = prov['s3_path']
        book_id = prov['book_id']

        # Check if this local folder was already matched to another source
        if local_path and local_path in matched_locals:
            print(f'WARNING: Duplicate local folder mapping!')
            print(f'  Local: {local_path}')
            print(f'  Source: {source_pdf}')
            print(f'  This indicates multiple source PDFs claiming the same folder')
            print()

        if local_path:
            matched_locals.add(local_path)

        rows.append({
            'source_pdf': source_pdf,
            'local_folder': local_path if local_path else 'UNIDENTIFIED',
            's3_folder': s3_path if s3_path else 'UNIDENTIFIED',
            'book_id': book_id,
            'status': 'VERIFIED'
        })
    else:
        rows.append({
            'source_pdf': source_pdf,
            'local_folder': 'UNIDENTIFIED',
            's3_folder': 'UNIDENTIFIED',
            'book_id': 'NONE',
            'status': 'NO_MAPPING'
        })

# Check for local folders without source PDFs
# (These would be in ProcessedSongs or Archive but not in the provenance map)
all_local_folders = set()
for record in all_records:
    local_path = record.get('local_output_path', '')
    if local_path:
        all_local_folders.add(local_path)

unmatched_locals = all_local_folders - matched_locals
for local_folder in sorted(unmatched_locals):
    # Find the record for this local folder
    record = next((r for r in all_records if r.get('local_output_path') == local_folder), None)
    if record:
        rows.append({
            'source_pdf': 'UNIDENTIFIED',
            'local_folder': local_folder,
            's3_folder': record.get('s3_output_path', 'UNIDENTIFIED'),
            'book_id': record.get('book_id', 'NONE'),
            'status': 'LOCAL_ONLY'
        })

# Save provenance-based mapping
with open('data/analysis/provenance_verified_mapping.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'{"="*80}')
print('PROVENANCE VERIFICATION SUMMARY')
print(f'{"="*80}')
print(f'Total source PDFs: {len(all_source_pdfs)}')
print(f'Verified mappings: {sum(1 for r in rows if r["status"] == "VERIFIED")}')
print(f'No mapping: {sum(1 for r in rows if r["status"] == "NO_MAPPING")}')
print(f'Local only: {sum(1 for r in rows if r["status"] == "LOCAL_ONLY")}')
print(f'\nSaved to: data/analysis/provenance_verified_mapping.csv')
