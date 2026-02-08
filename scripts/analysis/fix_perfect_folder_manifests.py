"""
Fix manifest s3_path mismatches for PERFECT folders before archiving
Updates manifests to use the correct normalized s3_path (matching actual folder location)
"""
import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

# Load verification results
print("Loading verification results...")
with open('data/analysis/perfect_folder_verification.json', 'r') as f:
    verification = json.load(f)

# Get folders with manifest path mismatches
folders_to_fix = []
for folder in verification['failed_folders']:
    issues = folder['issues']
    if any('Manifest s3_path mismatch' in issue for issue in issues):
        # Skip already archived folders
        if not any('already archived' in issue.lower() for issue in issues):
            folders_to_fix.append(folder)

print(f"Found {len(folders_to_fix)} manifests to fix\n")

fixed_count = 0
error_count = 0

for folder in folders_to_fix:
    book_id = folder['book_id']
    local_path = folder['local_path']
    s3_path = folder['s3_path']

    # Extract the mismatch from issues
    mismatch_issue = [i for i in folder['issues'] if 'Manifest s3_path mismatch' in i][0]
    # Parse: "Manifest s3_path mismatch: <old> vs <new>"
    parts = mismatch_issue.split(': ')[1].split(' vs ')
    old_s3_path = parts[0]
    new_s3_path = parts[1]

    print(f"Fixing: {local_path}")
    print(f"  Old manifest S3: {old_s3_path}")
    print(f"  New manifest S3: {new_s3_path}")

    try:
        # Download current manifest
        manifest_key = f"output/{book_id}/manifest.json"
        response = s3.get_object(Bucket=BUCKET, Key=manifest_key)
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Update S3 path in manifest
        manifest['s3_path'] = new_s3_path

        # Update book_name if it contains the old path
        if 'book_name' in manifest:
            old_suffix = old_s3_path.split('/')[-1]
            new_suffix = new_s3_path.split('/')[-1]
            manifest['book_name'] = manifest['book_name'].replace(old_suffix, new_suffix)

        # Update song paths if they exist
        if 'songs' in manifest:
            for song in manifest['songs']:
                if 'output_path' in song:
                    song['output_path'] = song['output_path'].replace(old_s3_path, new_s3_path)

        # Add update timestamp
        manifest['manifest_fixed_timestamp'] = datetime.now().isoformat()
        manifest['manifest_fix_reason'] = 'Updated S3 path to match normalized folder name before archiving'

        # Upload corrected manifest
        s3.put_object(
            Bucket=BUCKET,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2),
            ContentType='application/json'
        )

        fixed_count += 1
        print(f"  OK Fixed ({fixed_count}/{len(folders_to_fix)})\n")

    except Exception as e:
        error_count += 1
        print(f"  ERROR: {e}\n")

print(f"{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"Manifests to fix: {len(folders_to_fix)}")
print(f"Successfully fixed: {fixed_count}")
print(f"Errors: {error_count}")
print()
print("Next step: Re-run verify_perfect_folders.py to confirm all are verified")
