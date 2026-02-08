"""
Fix all naming issues across local, S3, DynamoDB, and manifests
"""
import json
import shutil
import boto3
from pathlib import Path

archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('Loading naming issues...')
with open('data/analysis/naming_audit_results.json', 'r', encoding='utf-8') as f:
    audit = json.load(f)

issues = audit['naming_issues']
print(f'Found {len(issues)} folders to rename\n')

stats = {
    'local_renamed': 0,
    's3_moved': 0,
    's3_files_moved': 0,
    'dynamodb_updated': 0,
    'manifests_updated': 0,
    'errors': 0
}

errors = []
rename_log = []

for i, issue in enumerate(issues, 1):
    old_path = issue['path']
    artist = issue['artist']
    old_songbook = issue['songbook']
    new_songbook = issue['expected']  # This is the correct new songbook name
    new_path = f"{artist}/{new_songbook}"

    print(f'[{i}/{len(issues)}] {old_path}')
    print(f'         -> {new_path}')

    try:
        # 1. Rename local folder
        old_local = archive_root / old_path.replace('/', '\\')
        new_local = archive_root / new_path.replace('/', '\\')

        if old_local.exists():
            if new_local.exists():
                print(f'  Local: SKIP (target already exists)')
                continue

            old_local.rename(new_local)
            stats['local_renamed'] += 1
            print('  Local: RENAMED')
        else:
            print(f'  Local: NOT FOUND (skipping)')
            continue

        # 2. Move S3 folder (in archive/completed/)
        old_s3_prefix = f"archive/completed/{old_path}/"
        new_s3_prefix = f"archive/completed/{new_path}/"

        # List all objects in old S3 path
        paginator = s3.get_paginator('list_objects_v2')
        s3_files = []
        for page in paginator.paginate(Bucket=BUCKET, Prefix=old_s3_prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_files.append(obj['Key'])

        if s3_files:
            for s3_key in s3_files:
                # Copy to new location
                new_key = s3_key.replace(old_s3_prefix, new_s3_prefix, 1)
                s3.copy_object(
                    Bucket=BUCKET,
                    CopySource={'Bucket': BUCKET, 'Key': s3_key},
                    Key=new_key
                )
                # Delete old object
                s3.delete_object(Bucket=BUCKET, Key=s3_key)

            stats['s3_moved'] += 1
            stats['s3_files_moved'] += len(s3_files)
            print(f'  S3: MOVED {len(s3_files)} files')
        else:
            print('  S3: NO FILES FOUND')

        # 3. Update DynamoDB records
        # Query for records with this local path
        response = TABLE.scan(
            FilterExpression='contains(#local_path, :old_path)',
            ExpressionAttributeNames={'#local_path': 'local_output_path'},
            ExpressionAttributeValues={':old_path': old_path.replace('/', '\\')}
        )

        dynamodb_count = 0
        manifest_count = 0

        for item in response.get('Items', []):
            book_id = item.get('book_id')
            if not book_id:
                continue

            # Update local and S3 paths
            old_local_path = item.get('local_output_path', '')
            old_s3_path = item.get('s3_output_path', '')

            if old_path.replace('/', '\\') in old_local_path:
                new_local_path = old_local_path.replace(
                    old_path.replace('/', '\\'),
                    new_path.replace('/', '\\'),
                    1
                )
                new_s3_path = old_s3_path.replace(old_path, new_path, 1) if old_s3_path else ''

                TABLE.update_item(
                    Key={'book_id': book_id},
                    UpdateExpression='SET local_output_path = :local, s3_output_path = :s3',
                    ExpressionAttributeValues={
                        ':local': new_local_path,
                        ':s3': new_s3_path
                    }
                )
                dynamodb_count += 1

                # 4. Update manifest
                manifest_key = f"output/{book_id}/manifest.json"
                try:
                    manifest_obj = s3.get_object(Bucket=BUCKET, Key=manifest_key)
                    manifest = json.loads(manifest_obj['Body'].read())

                    # Update paths in manifest
                    if 'local_path' in manifest:
                        manifest['local_path'] = manifest['local_path'].replace(
                            old_path.replace('/', '\\'),
                            new_path.replace('/', '\\'),
                            1
                        )
                    if 's3_path' in manifest:
                        manifest['s3_path'] = manifest['s3_path'].replace(old_path, new_path, 1)

                    # Update song output paths
                    if 'songs' in manifest:
                        for song in manifest['songs']:
                            if 'output_path' in song:
                                song['output_path'] = song['output_path'].replace(old_path, new_path, 1)

                    # Save updated manifest
                    s3.put_object(
                        Bucket=BUCKET,
                        Key=manifest_key,
                        Body=json.dumps(manifest, indent=2),
                        ContentType='application/json'
                    )
                    manifest_count += 1
                except Exception as e:
                    print(f'  Manifest: ERROR - {e}')

        stats['dynamodb_updated'] += dynamodb_count
        stats['manifests_updated'] += manifest_count

        print(f'  DynamoDB: UPDATED {dynamodb_count} records')
        if manifest_count > 0:
            print(f'  Manifest: UPDATED {manifest_count}')

        rename_log.append({
            'old_path': old_path,
            'new_path': new_path,
            'status': 'success'
        })

        print()

    except Exception as e:
        stats['errors'] += 1
        errors.append({'folder': old_path, 'error': str(e)})
        rename_log.append({
            'old_path': old_path,
            'new_path': new_path,
            'status': 'error',
            'error': str(e)
        })
        print(f'  ERROR: {e}\n')

# Save rename log
with open('data/analysis/naming_fix_log.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_renames': len(issues),
        'stats': stats,
        'errors': errors,
        'rename_log': rename_log
    }, f, indent=2)

print(f'{"="*80}')
print('NAMING FIX SUMMARY')
print(f'{"="*80}')
print(f'Folders to rename:     {len(issues)}')
print(f'Local folders renamed: {stats["local_renamed"]}')
print(f'S3 folders moved:      {stats["s3_moved"]}')
print(f'S3 files moved:        {stats["s3_files_moved"]}')
print(f'DynamoDB updated:      {stats["dynamodb_updated"]}')
print(f'Manifests updated:     {stats["manifests_updated"]}')
print(f'Errors:                {stats["errors"]}')

if errors:
    print(f'\nErrors encountered:')
    for error in errors:
        print(f'  {error["folder"]}: {error["error"]}')

print('\nNaming fixes complete!')
print(f'Log saved to: data/analysis/naming_fix_log.json')
