"""
Comprehensive audit of naming consistency across:
- Local archive folders
- S3 archive folders
- Manifests
- DynamoDB records
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('Starting comprehensive naming audit...\n')

# Step 1: Scan all local archived folders
print('Step 1: Scanning local archived folders...')
local_folders = []
for artist_dir in archive_root.iterdir():
    if not artist_dir.is_dir():
        continue

    for songbook_dir in artist_dir.iterdir():
        if not songbook_dir.is_dir():
            continue

        relative_path = songbook_dir.relative_to(archive_root).as_posix()
        artist = artist_dir.name
        songbook = songbook_dir.name

        local_folders.append({
            'artist': artist,
            'songbook': songbook,
            'path': relative_path
        })

print(f'Found {len(local_folders)} local archived folders\n')

# Step 2: Check naming pattern compliance
print('Step 2: Checking naming pattern compliance...')
issues = []

for folder in local_folders:
    artist = folder['artist']
    songbook = folder['songbook']

    # Expected pattern: songbook should start with "artist - "
    # Exception: category folders like _broadway Shows, _movie And Tv
    if artist.startswith('_'):
        # Category folder - should have "Various Artists - " or "<composer> - " prefix
        if not ' - ' in songbook:
            issues.append({
                'type': 'category_missing_prefix',
                'path': folder['path'],
                'artist': artist,
                'songbook': songbook,
                'expected': f"Various Artists - {songbook}" if not any(comp in songbook.lower() for comp in ['john williams', 'lerner', 'rogers', 'sondheim']) else f"<composer> - {songbook}"
            })
    else:
        # Regular artist folder - should have "artist - " prefix
        expected_prefix = f"{artist} - "
        if not songbook.startswith(expected_prefix):
            issues.append({
                'type': 'artist_missing_prefix',
                'path': folder['path'],
                'artist': artist,
                'songbook': songbook,
                'expected': f"{artist} - {songbook}"
            })

print(f'Found {len(issues)} local naming issues\n')

# Step 3: Query DynamoDB for all archived records
print('Step 3: Querying DynamoDB for archived records...')
archived_records = []

# Scan for all records with archive paths
response = TABLE.scan()
while True:
    for item in response.get('Items', []):
        local_path = item.get('local_output_path', '')
        s3_path = item.get('s3_output_path', '')

        if 'archive/completed' in s3_path or 'ProcessedSongs_Archive' in local_path:
            archived_records.append({
                'book_id': item.get('book_id'),
                'local_path': local_path,
                's3_path': s3_path,
                'source_pdf_uri': item.get('source_pdf_uri', '')
            })

    if 'LastEvaluatedKey' not in response:
        break
    response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

print(f'Found {len(archived_records)} archived DynamoDB records\n')

# Step 4: Check S3 paths match local paths
print('Step 4: Checking S3 path consistency...')
path_mismatches = []

for record in archived_records:
    local_path = record['local_path']
    s3_path = record['s3_path']

    # Extract the folder structure from both
    # Local: d:\Work\songbook-splitter\ProcessedSongs_Archive\<artist>\<songbook>
    # S3: archive/completed/<artist>/<songbook>

    if 'ProcessedSongs_Archive' in local_path and 'archive/completed' in s3_path:
        local_parts = local_path.split('ProcessedSongs_Archive\\')[-1].split('\\')
        s3_parts = s3_path.split('archive/completed/')[-1].split('/')

        if len(local_parts) >= 2 and len(s3_parts) >= 2:
            local_folder = f"{local_parts[0]}/{local_parts[1]}"
            s3_folder = f"{s3_parts[0]}/{s3_parts[1]}"

            # Normalize slashes for comparison
            local_folder_normalized = local_folder.replace('\\', '/')

            if local_folder_normalized != s3_folder:
                path_mismatches.append({
                    'book_id': record['book_id'],
                    'local_folder': local_folder_normalized,
                    's3_folder': s3_folder,
                    'full_local_path': local_path,
                    'full_s3_path': s3_path
                })

print(f'Found {len(path_mismatches)} path mismatches between local and S3\n')

# Step 5: Save audit results
audit_results = {
    'total_local_folders': len(local_folders),
    'local_naming_issues': len(issues),
    'total_dynamodb_records': len(archived_records),
    's3_path_mismatches': len(path_mismatches),
    'naming_issues': issues,
    'path_mismatches': path_mismatches
}

with open('data/analysis/naming_audit_results.json', 'w', encoding='utf-8') as f:
    json.dump(audit_results, f, indent=2)

# Print summary
print(f'{"="*80}')
print('COMPREHENSIVE NAMING AUDIT SUMMARY')
print(f'{"="*80}')
print(f'Total local folders:       {len(local_folders)}')
print(f'Local naming issues:       {len(issues)}')
print(f'Total DynamoDB records:    {len(archived_records)}')
print(f'S3 path mismatches:        {len(path_mismatches)}')
print()

if issues:
    print('Local naming issues by type:')
    by_type = defaultdict(list)
    for issue in issues:
        by_type[issue['type']].append(issue)

    for issue_type, issue_list in by_type.items():
        print(f'  {issue_type}: {len(issue_list)}')
        for issue in issue_list[:5]:
            print(f'    {issue["path"]}')
            print(f'      -> Should be: {issue["expected"]}')
        if len(issue_list) > 5:
            print(f'    ... and {len(issue_list) - 5} more')
    print()

if path_mismatches:
    print('S3 path mismatches (first 10):')
    for mismatch in path_mismatches[:10]:
        print(f'  Book ID: {mismatch["book_id"]}')
        print(f'    Local:  {mismatch["local_folder"]}')
        print(f'    S3:     {mismatch["s3_folder"]}')
    if len(path_mismatches) > 10:
        print(f'  ... and {len(path_mismatches) - 10} more')

print(f'\nAudit results saved to: data/analysis/naming_audit_results.json')
