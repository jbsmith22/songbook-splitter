"""
Restore previous versions of files that were incorrectly overwritten by flatten operation
"""
import json
import boto3
from collections import defaultdict
from datetime import datetime, timezone

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Load match quality data to find files with size mismatches
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

# Collect all files that have size mismatches
files_to_check = []

for tier_name, folders in match_data['quality_tiers'].items():
    for folder in folders:
        fc = folder.get('file_comparison', {})
        size_mismatches = fc.get('size_mismatches', [])

        if not size_mismatches:
            continue

        s3_path = folder.get('s3_path', '')

        for mismatch in size_mismatches:
            filename = mismatch.get('filename', '')
            s3_size = mismatch.get('s3_size', 0)
            files_to_check.append({
                's3_key': f"{s3_path}/{filename}",
                'current_size': s3_size
            })

print(f"Found {len(files_to_check)} files with size mismatches to check\n")

# Flatten operation happened around 2026-02-01 17:56 UTC
# We want versions from BEFORE that time
flatten_time = datetime(2026, 2, 1, 17, 50, 0, tzinfo=timezone.utc)

stats = defaultdict(int)
errors = []
restorations = []

for file_info in files_to_check:
    s3_key = file_info['s3_key']
    current_size = file_info['current_size']

    try:
        # List all versions of this file
        response = s3_client.list_object_versions(
            Bucket=bucket,
            Prefix=s3_key,
            MaxKeys=100
        )

        versions = response.get('Versions', [])
        if not versions:
            stats['no_versions'] += 1
            continue

        # Find a version from before the flatten operation that is larger
        best_version = None
        for version in versions:
            version_time = version['LastModified']
            version_size = version['Size']
            version_id = version['VersionId']

            # We want a version from before the flatten AND larger than current
            if version_time < flatten_time and version_size > current_size:
                # Keep track of the largest version from before flatten
                if best_version is None or version_size > best_version['size']:
                    best_version = {
                        'version_id': version_id,
                        'size': version_size,
                        'time': version_time
                    }

        if best_version:
            # Restore this version by copying it to be the current version
            s3_client.copy_object(
                Bucket=bucket,
                CopySource={
                    'Bucket': bucket,
                    'Key': s3_key,
                    'VersionId': best_version['version_id']
                },
                Key=s3_key
            )

            restorations.append({
                'file': s3_key,
                'old_size': current_size,
                'restored_size': best_version['size'],
                'restored_from': best_version['time']
            })

            stats['restored'] += 1
            print(f"Restored: {s3_key}")
            print(f"  {current_size:,} bytes -> {best_version['size']:,} bytes")
            print(f"  From version: {best_version['time']}")
        else:
            stats['no_better_version'] += 1

    except Exception as e:
        errors.append(f"Failed to process {s3_key}: {e}")
        stats['errors'] += 1

print(f"\n{'='*60}")
print("S3 VERSION RESTORATION SUMMARY")
print(f"{'='*60}")
print(f"Files checked:        {len(files_to_check)}")
print(f"Files restored:       {stats['restored']}")
print(f"No versions found:    {stats['no_versions']}")
print(f"No better version:    {stats['no_better_version']}")
print(f"Errors:               {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

# Save restoration log
if restorations:
    with open('data/analysis/s3_version_restorations.json', 'w') as f:
        json.dump(restorations, f, indent=2, default=str)
    print(f"\nRestoration log saved to data/analysis/s3_version_restorations.json")

print("\nOK S3 version restoration complete!")
print("Re-run match quality analysis to verify improvements.")
