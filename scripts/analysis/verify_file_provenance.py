"""
Verify file-level provenance for each local folder
Check that every file in each folder came from the correct source PDF
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

# Paths
archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
active_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

print('File-level provenance verification\n')
print('=' * 80)

# Get all DynamoDB records
print('Loading DynamoDB records...')
all_records = []
response = TABLE.scan()
while True:
    all_records.extend(response.get('Items', []))
    if 'LastEvaluatedKey' not in response:
        break
    response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

print(f'Found {len(all_records)} records\n')

# Organize by local folder
folders = defaultdict(list)
for record in all_records:
    local_path = record.get('local_output_path', '')
    if local_path:
        folders[local_path].append(record)

print(f'Found {len(folders)} unique local folders\n')

# Check for folders with multiple source PDFs
duplicates = []
file_issues = []

for local_folder, records in folders.items():
    # Get unique source PDFs for this folder
    sources = set()
    for rec in records:
        source_uri = rec.get('source_pdf_uri', '')
        if source_uri:
            # Normalize source path
            if 'SheetMusic/' in source_uri or 'SheetMusic\\' in source_uri:
                parts = source_uri.replace('\\', '/').split('SheetMusic/')
                if len(parts) > 1:
                    sources.add(parts[1])

    if len(sources) > 1:
        duplicates.append({
            'local_folder': local_folder,
            'source_pdfs': list(sources),
            'record_count': len(records)
        })
        print(f'DUPLICATE: {local_folder}')
        print(f'  Multiple source PDFs:')
        for src in sources:
            print(f'    - {src}')
        print()

    # Verify files exist in the local folder
    folder_path = None
    if (archive_root / local_folder.replace('/', '\\')).exists():
        folder_path = archive_root / local_folder.replace('/', '\\')
    elif (active_root / local_folder.replace('/', '\\')).exists():
        folder_path = active_root / local_folder.replace('/', '\\')

    if folder_path and folder_path.exists():
        # List actual files
        actual_files = set()
        for file in folder_path.glob('*.pdf'):
            actual_files.add(file.name)

        # Get expected files from manifest/artifacts
        book_id = records[0].get('book_id')
        expected_files = set()

        if book_id:
            # Try to get manifest
            try:
                manifest_key = f"output/{book_id}/manifest.json"
                manifest_obj = s3.get_object(Bucket=BUCKET, Key=manifest_key)
                manifest = json.loads(manifest_obj['Body'].read())

                if 'songs' in manifest:
                    for song in manifest['songs']:
                        output_path = song.get('output_path', '')
                        if output_path:
                            filename = output_path.split('/')[-1]
                            expected_files.add(filename)
            except:
                pass

        # Compare
        missing = expected_files - actual_files
        extra = actual_files - expected_files

        if missing or extra:
            file_issues.append({
                'local_folder': local_folder,
                'source_pdf': list(sources)[0] if sources else 'UNKNOWN',
                'missing_files': list(missing),
                'extra_files': list(extra),
                'actual_count': len(actual_files),
                'expected_count': len(expected_files)
            })

# Save results
results = {
    'total_folders': len(folders),
    'folders_with_multiple_sources': len(duplicates),
    'folders_with_file_issues': len(file_issues),
    'duplicates': duplicates,
    'file_issues': file_issues
}

with open('data/analysis/file_provenance_issues.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2)

print(f'\n{"="*80}')
print('FILE PROVENANCE SUMMARY')
print(f'{"="*80}')
print(f'Total folders checked: {len(folders)}')
print(f'Folders with multiple source PDFs: {len(duplicates)}')
print(f'Folders with file count mismatches: {len(file_issues)}')
print(f'\nDetailed results saved to: data/analysis/file_provenance_issues.json')

if duplicates:
    print(f'\nDUPLICATE SOURCE MAPPINGS ({len(duplicates)}):')
    for dup in duplicates[:10]:
        print(f'  {dup["local_folder"]}')
        for src in dup['source_pdfs']:
            print(f'    <- {src}')
    if len(duplicates) > 10:
        print(f'  ... and {len(duplicates) - 10} more')
