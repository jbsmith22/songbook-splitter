"""
Move all files from /Songs/ subfolders up to parent folder in S3
Fixes the structural issue where files are nested one level too deep
"""
import boto3
from collections import defaultdict

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

print("Scanning S3 for files in /Songs/ subfolders...")

# Find all files in Songs subfolders
songs_files = []
paginator = s3_client.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket=bucket):
    if 'Contents' not in page:
        continue

    for obj in page['Contents']:
        key = obj['Key']

        # Skip if not a PDF or not in a Songs subfolder
        if not key.endswith('.pdf'):
            continue
        if '/Songs/' not in key:
            continue

        songs_files.append({
            'key': key,
            'size': obj['Size']
        })

print(f"Found {len(songs_files)} files in /Songs/ subfolders\n")

if not songs_files:
    print("No files to move!")
    exit(0)

# Ask for confirmation
print("This will move all files from /Songs/ subfolders to their parent folders.")
print(f"Example: Artist/Album/Songs/file.pdf -> Artist/Album/file.pdf")
print(f"\nTotal files to move: {len(songs_files)}")

# Move files
stats = defaultdict(int)
errors = []

print("\nMoving files...")
for i, file_info in enumerate(songs_files, 1):
    old_key = file_info['key']

    # Build new key by removing /Songs/
    new_key = old_key.replace('/Songs/', '/')

    try:
        # Copy to new location
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={'Bucket': bucket, 'Key': old_key},
            Key=new_key
        )

        # Delete old location
        s3_client.delete_object(Bucket=bucket, Key=old_key)

        stats['moved'] += 1

        if i % 100 == 0:
            print(f"  Moved {i}/{len(songs_files)} files...")

    except Exception as e:
        errors.append(f"Failed to move {old_key}: {e}")
        stats['errors'] += 1

print(f"\n{'='*60}")
print("FLATTEN SONGS FOLDERS SUMMARY")
print(f"{'='*60}")
print(f"Files moved:  {stats['moved']}")
print(f"Errors:       {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK Songs folder flattening complete!")
print("\nNow run validation and match quality analysis to see improvements.")
