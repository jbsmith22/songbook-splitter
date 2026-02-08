"""
Check for folders where manifest S3 path doesn't match actual S3 location
"""
import json
import boto3

# Load match quality data
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

poor_folders = match_data['quality_tiers']['poor']
print(f"Checking {len(poor_folders)} POOR folders...\n")

manifest_mismatch = []
actually_have_files = []

for folder in poor_folders:
    local_path = folder['local_path']
    s3_path_from_manifest = folder['s3_path']
    s3_songs = folder.get('s3_songs', 0)

    # Only check folders with S3=0
    if s3_songs == 0:
        # Check if files exist at the LOCAL path format on S3 (with underscores)
        try:
            response = s3.list_objects_v2(
                Bucket=BUCKET,
                Prefix=local_path + '/',
                MaxKeys=5
            )

            if response.get('Contents'):
                file_count = response['KeyCount']
                manifest_mismatch.append({
                    'local_path': local_path,
                    'manifest_s3_path': s3_path_from_manifest,
                    'actual_s3_path': local_path,
                    'files_found': file_count
                })
                actually_have_files.append(local_path)
                print(f"✗ {local_path}")
                print(f"  Manifest says: {s3_path_from_manifest}")
                print(f"  Actually at:   {local_path}")
                print(f"  Files found:   {file_count}+")
                print()

        except Exception as e:
            pass

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"POOR folders with manifest S3 path mismatch: {len(manifest_mismatch)}")
print(f"These folders actually HAVE files on S3, just at the wrong path in manifest")
