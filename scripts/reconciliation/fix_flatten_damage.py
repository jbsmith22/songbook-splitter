"""
Fix damage from flatten operation by restoring larger local files to S3
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'
local_base = Path('SheetMusicIndividualSheets')

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

# Get all folders with size mismatches where local is larger
stats = defaultdict(int)
errors = []

for tier_name, folders in match_data['quality_tiers'].items():
    for folder in folders:
        fc = folder.get('file_comparison', {})
        size_mismatches = fc.get('size_mismatches', [])

        if not size_mismatches:
            continue

        local_path = folder.get('local_path', '')
        s3_path = folder.get('s3_path', '')

        for mismatch in size_mismatches:
            filename = mismatch.get('filename', '')
            local_size = mismatch.get('local_size', 0)
            s3_size = mismatch.get('s3_size', 0)

            # Only fix if local is larger (better version)
            if local_size > s3_size:
                local_file = local_base / local_path / filename
                s3_key = f"{s3_path}/{filename}"

                if not local_file.exists():
                    errors.append(f"Local file not found: {local_file}")
                    stats['missing_local'] += 1
                    continue

                try:
                    # Upload larger local version to S3
                    s3_client.upload_file(str(local_file), bucket, s3_key)
                    stats['restored'] += 1
                    stats['folders_affected'] += 1

                    print(f"Restored: {s3_key}")
                    print(f"  {local_size:,} bytes (local) -> {s3_size:,} bytes (S3)")

                except Exception as e:
                    errors.append(f"Failed to upload {local_file}: {e}")
                    stats['errors'] += 1

print(f"\n{'='*60}")
print("FIX FLATTEN DAMAGE SUMMARY")
print(f"{'='*60}")
print(f"Files restored:       {stats['restored']}")
print(f"Missing local files:  {stats['missing_local']}")
print(f"Errors:               {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK Flatten damage repair complete!")
print("Re-run match quality analysis to verify fixes.")
