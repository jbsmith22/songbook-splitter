"""
Validate that manifests, artifacts, and DynamoDB entries accurately reflect reality
for PERFECT folders
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bucket = 'jsmith-output'
table = dynamodb.Table('jsmith-processing-ledger')

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

perfect_folders = match_data['quality_tiers']['perfect']
print(f"Found {len(perfect_folders)} PERFECT folders to validate\n")

stats = defaultdict(int)
issues = []

# Sample first 10 PERFECT folders for validation
sample_size = min(10, len(perfect_folders))
print(f"Validating sample of {sample_size} PERFECT folders...\n")

for i, folder in enumerate(perfect_folders[:sample_size], 1):
    book_id = folder.get('book_id', '')
    s3_path = folder.get('s3_path', '')

    if not book_id or book_id in ['fuzzy', 'unknown', '']:
        stats['no_book_id'] += 1
        continue

    print(f"[{i}/{sample_size}] Validating: {s3_path}")
    print(f"  Book ID: {book_id}")

    # 1. Check manifest accuracy
    manifest_accurate = True
    try:
        response = s3_client.get_object(Bucket=bucket, Key=f'output/{book_id}/manifest.json')
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Get actual S3 files
        actual_files = []
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{s3_path}/"):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.pdf'):
                        actual_files.append(obj['Key'].split('/')[-1])

        # Check if manifest lists files
        manifest_files = []
        if 'songs' in manifest:
            manifest_files = [s.get('output_filename', '') for s in manifest.get('songs', [])]
        elif 'output_files' in manifest:
            manifest_files = manifest.get('output_files', [])

        actual_set = set(actual_files)
        manifest_set = set(manifest_files)

        if actual_set != manifest_set:
            manifest_accurate = False
            missing_in_manifest = actual_set - manifest_set
            extra_in_manifest = manifest_set - actual_set
            issues.append({
                'folder': s3_path,
                'book_id': book_id,
                'type': 'manifest_mismatch',
                'actual_count': len(actual_files),
                'manifest_count': len(manifest_files),
                'missing_in_manifest': len(missing_in_manifest),
                'extra_in_manifest': len(extra_in_manifest)
            })
            print(f"    Manifest: MISMATCH (actual: {len(actual_files)}, manifest: {len(manifest_files)})")
        else:
            print(f"    Manifest: OK ({len(actual_files)} files)")
            stats['manifest_accurate'] += 1

    except Exception as e:
        print(f"    Manifest: ERROR - {e}")
        stats['manifest_errors'] += 1

    # 2. Check artifacts (output_files.json)
    try:
        response = s3_client.get_object(Bucket=bucket, Key=f'artifacts/{book_id}/output_files.json')
        output_files = json.loads(response['Body'].read().decode('utf-8'))

        artifact_files = []
        if isinstance(output_files, list):
            artifact_files = [f.split('/')[-1] if '/' in f else f for f in output_files]
        elif isinstance(output_files, dict):
            artifact_files = list(output_files.keys())

        if set(artifact_files) == set(actual_files):
            print(f"    Artifacts: OK ({len(artifact_files)} files)")
            stats['artifacts_accurate'] += 1
        else:
            print(f"    Artifacts: MISMATCH (actual: {len(actual_files)}, artifact: {len(artifact_files)})")
            issues.append({
                'folder': s3_path,
                'book_id': book_id,
                'type': 'artifact_mismatch',
                'actual_count': len(actual_files),
                'artifact_count': len(artifact_files)
            })

    except Exception as e:
        print(f"    Artifacts: ERROR - {e}")
        stats['artifact_errors'] += 1

    # 3. Check DynamoDB
    try:
        response = table.query(
            KeyConditionExpression='book_id = :bid',
            ExpressionAttributeValues={':bid': book_id},
            ScanIndexForward=False,
            Limit=1
        )

        if response['Items']:
            ddb_item = response['Items'][0]
            ddb_count = ddb_item.get('songs_extracted', 0)
            ddb_status = ddb_item.get('status', '')

            if ddb_count == len(actual_files) and ddb_status == 'success':
                print(f"    DynamoDB: OK (count: {ddb_count}, status: {ddb_status})")
                stats['dynamodb_accurate'] += 1
            else:
                print(f"    DynamoDB: MISMATCH (actual: {len(actual_files)}, ddb: {ddb_count}, status: {ddb_status})")
                issues.append({
                    'folder': s3_path,
                    'book_id': book_id,
                    'type': 'dynamodb_mismatch',
                    'actual_count': len(actual_files),
                    'ddb_count': ddb_count,
                    'status': ddb_status
                })
        else:
            print(f"    DynamoDB: MISSING")
            stats['dynamodb_missing'] += 1

    except Exception as e:
        print(f"    DynamoDB: ERROR - {e}")
        stats['dynamodb_errors'] += 1

    print()

# Summary
print(f"{'='*60}")
print("METADATA VALIDATION SUMMARY")
print(f"{'='*60}")
print(f"Folders validated:           {sample_size}")
print(f"Manifest accurate:           {stats['manifest_accurate']}/{sample_size}")
print(f"Artifacts accurate:          {stats['artifacts_accurate']}/{sample_size}")
print(f"DynamoDB accurate:           {stats['dynamodb_accurate']}/{sample_size}")
print(f"\nManifest errors:             {stats['manifest_errors']}")
print(f"Artifact errors:             {stats['artifact_errors']}")
print(f"DynamoDB errors:             {stats['dynamodb_errors']}")
print(f"DynamoDB missing:            {stats['dynamodb_missing']}")

if issues:
    print(f"\n{'='*60}")
    print(f"ISSUES FOUND ({len(issues)})")
    print(f"{'='*60}")
    for issue in issues[:10]:
        print(f"\n{issue['folder']}")
        print(f"  Type: {issue['type']}")
        if 'actual_count' in issue:
            print(f"  Actual files: {issue['actual_count']}")
        if 'manifest_count' in issue:
            print(f"  Manifest count: {issue['manifest_count']}")
        if 'artifact_count' in issue:
            print(f"  Artifact count: {issue['artifact_count']}")
        if 'ddb_count' in issue:
            print(f"  DynamoDB count: {issue['ddb_count']}")

# Calculate accuracy percentage
if sample_size > 0:
    manifest_pct = (stats['manifest_accurate'] / sample_size) * 100
    artifacts_pct = (stats['artifacts_accurate'] / sample_size) * 100
    dynamodb_pct = (stats['dynamodb_accurate'] / sample_size) * 100

    print(f"\n{'='*60}")
    print("ACCURACY RATES")
    print(f"{'='*60}")
    print(f"Manifest accuracy:   {manifest_pct:.1f}%")
    print(f"Artifacts accuracy:  {artifacts_pct:.1f}%")
    print(f"DynamoDB accuracy:   {dynamodb_pct:.1f}%")

print("\nOK Metadata validation complete!")
