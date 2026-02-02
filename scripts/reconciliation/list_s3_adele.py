"""
List all Adele files in S3 to understand the current structure
"""
import boto3

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

print("Listing all objects under output/Adele/...\n")

paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=S3_BUCKET, Prefix='output/Adele/')

all_objects = []
for page in pages:
    if 'Contents' in page:
        all_objects.extend(page['Contents'])

print(f"Found {len(all_objects)} total objects\n")

# Group by folder
folders = {}
for obj in all_objects:
    key = obj['Key']
    # Extract folder path (everything before the last /)
    parts = key.split('/')
    if len(parts) >= 3:  # output/Adele/FolderName/...
        folder = '/'.join(parts[:3])  # output/Adele/FolderName
        if folder not in folders:
            folders[folder] = []
        folders[folder].append(key)

print(f"Found {len(folders)} folders:\n")
for folder, files in sorted(folders.items()):
    print(f"{folder}/")
    print(f"  {len(files)} files")
    # Show first few files
    for f in files[:3]:
        filename = f.split('/')[-1]
        print(f"    - {filename}")
    if len(files) > 3:
        print(f"    ... and {len(files) - 3} more")
    print()
