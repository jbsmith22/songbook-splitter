"""
Fix manifest S3 paths to match actual S3 locations (use underscore format matching local)
"""
import json
import boto3
from datetime import datetime

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

poor_folders = match_data['quality_tiers']['poor']
print(f"Checking {len(poor_folders)} POOR folders...\n")

manifests_to_fix = []

for folder in poor_folders:
    local_path = folder['local_path']
    s3_path_from_manifest = folder['s3_path']
    book_id = folder.get('book_id', '')

    # Check if manifest S3 path differs from local path (the correct format)
    if s3_path_from_manifest != local_path:
        # Verify files actually exist at local path format on S3
        try:
            response = s3.list_objects_v2(
                Bucket=BUCKET,
                Prefix=local_path + '/',
                MaxKeys=5
            )

            if response.get('Contents'):
                manifests_to_fix.append({
                    'book_id': book_id,
                    'local_path': local_path,
                    'old_s3_path': s3_path_from_manifest,
                    'new_s3_path': local_path,  # Correct S3 path = local path
                })
                print(f"  {local_path}")
                print(f"    Old manifest S3: {s3_path_from_manifest}")
                print(f"    New manifest S3: {local_path}")
        except Exception as e:
            pass

print(f"\n{'='*80}")
print(f"Found {len(manifests_to_fix)} manifests to fix")
print(f"{'='*80}\n")

if not manifests_to_fix:
    print("No manifests need fixing!")
    exit(0)

# Fix each manifest
fixed_count = 0
error_count = 0

for item in manifests_to_fix:
    book_id = item['book_id']
    local_path = item['local_path']
    old_s3_path = item['old_s3_path']
    new_s3_path = item['new_s3_path']

    # Manifests are stored at output/{book_id}/manifest.json
    manifest_key = f"output/{book_id}/manifest.json"

    try:
        # Download current manifest from output location
        response = s3.get_object(Bucket=BUCKET, Key=manifest_key)
        manifest = json.loads(response['Body'].read().decode('utf-8'))

        # Update S3 path in manifest
        manifest['s3_path'] = new_s3_path
        manifest['book_name'] = manifest['book_name'].replace(old_s3_path.split('/')[-1], new_s3_path.split('/')[-1])

        # Update song paths if they exist
        if 'songs' in manifest:
            for song in manifest['songs']:
                if 'output_path' in song:
                    song['output_path'] = song['output_path'].replace(old_s3_path, new_s3_path)

        # Add update timestamp
        manifest['manifest_fixed_timestamp'] = datetime.now().isoformat()
        manifest['manifest_fix_reason'] = 'Updated S3 path to match actual file location'

        # Upload corrected manifest (already in correct location)
        s3.put_object(
            Bucket=BUCKET,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2),
            ContentType='application/json'
        )

        fixed_count += 1
        print(f"[{fixed_count}/{len(manifests_to_fix)}] Fixed: {local_path}")

    except Exception as e:
        error_count += 1
        print(f"ERROR fixing {local_path}: {e}")

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"Manifests fixed: {fixed_count}")
print(f"Errors: {error_count}")
print(f"\nNext step: Re-run match quality analysis to verify")
