"""
Comprehensive verification of PERFECT folders before archiving
Checks:
1. File count and names match between local and S3
2. File sizes match between local and S3
3. All 5 artifacts exist in artifacts/{book_id}/
4. Manifest exists and is valid in output/{book_id}/
5. DynamoDB entry exists and matches
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# AWS setup
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

# Paths
LOCAL_ROOT = Path('d:/Work/songbook-splitter/ProcessedSongs')

# Required artifacts (matching analyze_match_quality_with_files.py)
REQUIRED_ARTIFACTS = [
    'toc_discovery.json',
    'toc_parse.json',
    'page_mapping.json',
    'verified_songs.json',
    'output_files.json'
]

# Load match quality data
print("Loading PERFECT folders from match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

perfect_folders = match_data['quality_tiers']['perfect']
print(f"Found {len(perfect_folders)} PERFECT folders to verify\n")

# Verification results
verified = []
failed = []
issues = defaultdict(list)

for i, folder in enumerate(perfect_folders, 1):
    local_path = folder.get('local_path', '')
    s3_path = folder.get('s3_path', '')
    book_id = folder.get('book_id', '')

    if i % 25 == 0:
        print(f"Verifying {i}/{len(perfect_folders)}...")

    folder_issues = []

    # Skip if no valid book_id
    if not book_id or book_id in ['fuzzy', 'unknown', '']:
        folder_issues.append(f"Invalid book_id: {book_id}")
        issues['invalid_book_id'].append(local_path)
        failed.append({
            'local_path': local_path,
            's3_path': s3_path,
            'book_id': book_id,
            'issues': folder_issues
        })
        continue

    # 1. Verify local files exist
    local_folder = LOCAL_ROOT / local_path
    if not local_folder.exists():
        folder_issues.append("Local folder does not exist")
        issues['no_local_folder'].append(local_path)
    else:
        local_files = {}
        for pdf_file in local_folder.glob('*.pdf'):
            local_files[pdf_file.name] = pdf_file.stat().st_size

        # 2. Verify S3 files exist
        s3_files = {}
        try:
            response = s3.list_objects_v2(Bucket=BUCKET, Prefix=s3_path + '/')
            if response.get('Contents'):
                for obj in response['Contents']:
                    if obj['Key'].endswith('.pdf'):
                        filename = obj['Key'].split('/')[-1]
                        s3_files[filename] = obj['Size']
        except Exception as e:
            folder_issues.append(f"S3 listing error: {e}")
            issues['s3_listing_error'].append(local_path)

        # 3. Compare files (count, names, sizes)
        if len(local_files) != len(s3_files):
            folder_issues.append(f"File count mismatch: {len(local_files)} local vs {len(s3_files)} S3")
            issues['file_count_mismatch'].append(local_path)

        # Check for missing files
        local_only = set(local_files.keys()) - set(s3_files.keys())
        s3_only = set(s3_files.keys()) - set(local_files.keys())

        if local_only:
            folder_issues.append(f"Local-only files: {len(local_only)}")
            issues['local_only_files'].append(local_path)

        if s3_only:
            folder_issues.append(f"S3-only files: {len(s3_only)}")
            issues['s3_only_files'].append(local_path)

        # Check file sizes for matching files
        size_mismatches = []
        for filename in set(local_files.keys()) & set(s3_files.keys()):
            if local_files[filename] != s3_files[filename]:
                size_mismatches.append(filename)

        if size_mismatches:
            folder_issues.append(f"Size mismatches: {len(size_mismatches)} files")
            issues['size_mismatches'].append(local_path)

    # 4. Verify artifacts exist
    missing_artifacts = []
    for artifact in REQUIRED_ARTIFACTS:
        try:
            s3.head_object(Bucket=BUCKET, Key=f'artifacts/{book_id}/{artifact}')
        except:
            missing_artifacts.append(artifact)

    if missing_artifacts:
        folder_issues.append(f"Missing artifacts: {', '.join(missing_artifacts)}")
        issues['missing_artifacts'].append(local_path)

    # 5. Verify manifest exists
    try:
        response = s3.get_object(Bucket=BUCKET, Key=f'output/{book_id}/manifest.json')
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Verify manifest has expected fields
        if not manifest.get('book_name'):
            folder_issues.append("Manifest missing book_name")
            issues['invalid_manifest'].append(local_path)

        if manifest.get('s3_path') != s3_path:
            folder_issues.append(f"Manifest s3_path mismatch: {manifest.get('s3_path')} vs {s3_path}")
            issues['manifest_path_mismatch'].append(local_path)

    except Exception as e:
        folder_issues.append(f"Manifest error: {e}")
        issues['manifest_error'].append(local_path)

    # 6. Verify DynamoDB entry
    try:
        response = TABLE.query(
            KeyConditionExpression='book_id = :bid',
            ExpressionAttributeValues={':bid': book_id},
            ScanIndexForward=False,
            Limit=1
        )

        if not response['Items']:
            folder_issues.append("No DynamoDB entry found")
            issues['no_dynamodb_entry'].append(local_path)
        else:
            ddb_item = response['Items'][0]

            # Check if already archived
            if ddb_item.get('archived'):
                folder_issues.append("Already marked as archived in DynamoDB")
                issues['already_archived'].append(local_path)

    except Exception as e:
        folder_issues.append(f"DynamoDB error: {e}")
        issues['dynamodb_error'].append(local_path)

    # Record result
    if folder_issues:
        failed.append({
            'local_path': local_path,
            's3_path': s3_path,
            'book_id': book_id,
            'issues': folder_issues
        })
    else:
        verified.append({
            'local_path': local_path,
            's3_path': s3_path,
            'book_id': book_id
        })

# Print summary
print(f"\n{'='*80}")
print("VERIFICATION SUMMARY")
print(f"{'='*80}")
print(f"Total PERFECT folders: {len(perfect_folders)}")
print(f"Verified OK:           {len(verified)}")
print(f"Failed verification:   {len(failed)}")
print()

if issues:
    print(f"{'='*80}")
    print("ISSUE BREAKDOWN")
    print(f"{'='*80}")
    for issue_type, folders in sorted(issues.items()):
        print(f"{issue_type}: {len(folders)}")
    print()

if failed:
    print(f"{'='*80}")
    print("FAILED FOLDERS (first 20)")
    print(f"{'='*80}")
    for fail in failed[:20]:
        print(f"\n{fail['local_path']}")
        print(f"  Book ID: {fail['book_id']}")
        print(f"  Issues:")
        for issue in fail['issues']:
            print(f"    - {issue}")

    if len(failed) > 20:
        print(f"\n... and {len(failed) - 20} more failed folders")

# Save results
results = {
    'total_folders': len(perfect_folders),
    'verified': len(verified),
    'failed': len(failed),
    'verified_folders': verified,
    'failed_folders': failed,
    'issue_summary': dict(issues)
}

with open('data/analysis/perfect_folder_verification.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*80}")
print(f"Verification results saved to: data/analysis/perfect_folder_verification.json")
print(f"{'='*80}")

if failed:
    print(f"\nWARNING: {len(failed)} folders failed verification!")
    print("Review the issues before proceeding with archiving.")
else:
    print(f"\nSUCCESS: All {len(verified)} PERFECT folders verified!")
    print("Safe to proceed with archiving.")
