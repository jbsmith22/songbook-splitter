"""
Update DynamoDB and manifests for renamed folders
"""
import json
import boto3

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('Loading rename log...')
with open('data/analysis/naming_fix_log.json', 'r', encoding='utf-8') as f:
    log = json.load(f)

successful_renames = [r for r in log['rename_log'] if r['status'] == 'success']
print(f'Found {len(successful_renames)} successful renames to update\n')

stats = {
    'dynamodb_updated': 0,
    'manifests_updated': 0,
    'errors': 0
}

errors = []

# Scan all DynamoDB records once
print('Scanning all DynamoDB records...')
all_records = []
response = TABLE.scan()
while True:
    all_records.extend(response.get('Items', []))
    if 'LastEvaluatedKey' not in response:
        break
    response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])

print(f'Found {len(all_records)} total DynamoDB records\n')

# Process each rename
for i, rename in enumerate(successful_renames, 1):
    old_path = rename['old_path']
    new_path = rename['new_path']

    print(f'[{i}/{len(successful_renames)}] {old_path} -> {new_path}')

    try:
        # Find matching DynamoDB records
        matching_records = []
        for record in all_records:
            local_path = record.get('local_output_path', '')
            s3_path = record.get('s3_output_path', '')

            # Check if this record matches the old path
            if old_path in local_path or old_path in s3_path:
                matching_records.append(record)

        if not matching_records:
            print(f'  No DynamoDB records found')
            print()
            continue

        # Update each matching record
        for record in matching_records:
            book_id = record.get('book_id')
            if not book_id:
                continue

            old_local = record.get('local_output_path', '')
            old_s3 = record.get('s3_output_path', '')

            # Update paths
            new_local = old_local.replace(old_path, new_path)
            new_s3 = old_s3.replace(old_path, new_path)

            # Update DynamoDB
            TABLE.update_item(
                Key={'book_id': book_id},
                UpdateExpression='SET local_output_path = :local, s3_output_path = :s3',
                ExpressionAttributeValues={
                    ':local': new_local,
                    ':s3': new_s3
                }
            )
            stats['dynamodb_updated'] += 1

            # Update manifest
            manifest_key = f"output/{book_id}/manifest.json"
            try:
                manifest_obj = s3.get_object(Bucket=BUCKET, Key=manifest_key)
                manifest = json.loads(manifest_obj['Body'].read())

                # Update paths in manifest
                updated = False
                if 'local_path' in manifest and old_path in manifest['local_path']:
                    manifest['local_path'] = manifest['local_path'].replace(old_path, new_path)
                    updated = True

                if 's3_path' in manifest and old_path in manifest['s3_path']:
                    manifest['s3_path'] = manifest['s3_path'].replace(old_path, new_path)
                    updated = True

                # Update song output paths
                if 'songs' in manifest:
                    for song in manifest['songs']:
                        if 'output_path' in song and old_path in song['output_path']:
                            song['output_path'] = song['output_path'].replace(old_path, new_path)
                            updated = True

                if updated:
                    # Save updated manifest
                    s3.put_object(
                        Bucket=BUCKET,
                        Key=manifest_key,
                        Body=json.dumps(manifest, indent=2),
                        ContentType='application/json'
                    )
                    stats['manifests_updated'] += 1

            except s3.exceptions.NoSuchKey:
                pass  # No manifest found, skip
            except Exception as e:
                print(f'  Manifest error for {book_id}: {e}')

        print(f'  DynamoDB: UPDATED {len(matching_records)} records')
        print(f'  Manifests: UPDATED {len(matching_records)}')
        print()

    except Exception as e:
        stats['errors'] += 1
        errors.append({'rename': f"{old_path} -> {new_path}", 'error': str(e)})
        print(f'  ERROR: {e}\n')

print(f'{"="*80}')
print('DYNAMODB AND MANIFEST UPDATE SUMMARY')
print(f'{"="*80}')
print(f'Renames to process:    {len(successful_renames)}')
print(f'DynamoDB updated:      {stats["dynamodb_updated"]}')
print(f'Manifests updated:     {stats["manifests_updated"]}')
print(f'Errors:                {stats["errors"]}')

if errors:
    print(f'\nErrors encountered:')
    for error in errors:
        print(f'  {error["rename"]}: {error["error"]}')

print('\nDynamoDB and manifest updates complete!')
