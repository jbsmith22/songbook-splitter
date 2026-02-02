"""
Fix size mismatches by keeping the larger file version
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

excellent_folders = match_data['quality_tiers']['excellent']
print(f"Found {len(excellent_folders)} EXCELLENT folders\n")

stats = defaultdict(int)
errors = []

for i, folder in enumerate(excellent_folders, 1):
    local_path = folder.get('local_path', '')
    s3_path = folder.get('s3_path', '')
    fc = folder.get('file_comparison', {})
    size_mismatches = fc.get('size_mismatches', [])

    if not size_mismatches:
        continue

    print(f"\n[{i}/{len(excellent_folders)}] Processing: {local_path}")
    print(f"  Found {len(size_mismatches)} size mismatches")

    for mismatch in size_mismatches:
        filename = mismatch.get('filename', '')
        local_size = mismatch.get('local_size', 0)
        s3_size = mismatch.get('s3_size', 0)

        if not filename:
            continue

        # Determine which version is larger
        if s3_size > local_size:
            # S3 version is larger - download to local
            try:
                # Build S3 key (handle /Songs/ subfolder)
                s3_key = f"{s3_path}/{filename}"

                # Try with /Songs/ if direct path fails
                try:
                    s3_client.head_object(Bucket=bucket, Key=s3_key)
                except:
                    s3_key = f"{s3_path}/Songs/{filename}"

                local_file = local_base / local_path / filename
                local_file.parent.mkdir(parents=True, exist_ok=True)

                s3_client.download_file(bucket, s3_key, str(local_file))
                stats['s3_to_local_overwrites'] += 1
                print(f"    OK S3->Local: {filename} ({s3_size:,} > {local_size:,} bytes)")

            except Exception as e:
                errors.append(f"Failed to download {s3_key}: {e}")
                stats['errors'] += 1

        elif local_size > s3_size:
            # Local version is larger - upload to S3
            try:
                local_file = local_base / local_path / filename

                if not local_file.exists():
                    errors.append(f"Local file not found: {local_file}")
                    stats['errors'] += 1
                    continue

                # Build S3 key (handle /Songs/ subfolder)
                s3_key = f"{s3_path}/{filename}"

                # Check if Songs folder structure exists
                try:
                    s3_client.head_object(Bucket=bucket, Key=f"{s3_path}/Songs/{filename}")
                    s3_key = f"{s3_path}/Songs/{filename}"
                except:
                    pass

                s3_client.upload_file(str(local_file), bucket, s3_key)
                stats['local_to_s3_overwrites'] += 1
                print(f"    OK Local->S3: {filename} ({local_size:,} > {s3_size:,} bytes)")

            except Exception as e:
                errors.append(f"Failed to upload {local_file}: {e}")
                stats['errors'] += 1

        else:
            # Same size - shouldn't happen but skip
            stats['same_size_skipped'] += 1

print(f"\n{'='*60}")
print("FIX SIZE MISMATCHES SUMMARY")
print(f"{'='*60}")
print(f"Folders processed:        {len(excellent_folders)}")
print(f"S3->Local overwrites:     {stats['s3_to_local_overwrites']}")
print(f"Local->S3 overwrites:     {stats['local_to_s3_overwrites']}")
print(f"Same size (skipped):      {stats['same_size_skipped']}")
print(f"Errors:                   {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK Size mismatch fixes complete!")
