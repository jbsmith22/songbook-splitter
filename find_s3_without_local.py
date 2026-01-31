import boto3
import os
from collections import defaultdict

# Get all local folders
local_folders = set()
output_base = r'ProcessedSongs'

for root, dirs, files in os.walk(output_base):
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    if pdf_files:
        rel_path = os.path.relpath(root, output_base)
        parts = rel_path.split(os.sep)
        if len(parts) >= 2:
            artist = parts[0]
            book = parts[1]
            folder_key = f"{artist}/{book}".lower()
            local_folders.add(folder_key)

print(f"Local folders: {len(local_folders)}")

# Get all S3 folders
s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'jsmith-output'

s3_folders = defaultdict(int)
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket)

for page in pages:
    if 'Contents' not in page:
        continue
    
    for obj in page['Contents']:
        key = obj['Key']
        if key.endswith('.pdf'):
            # Extract artist/book from key
            parts = key.split('/')
            if len(parts) >= 3:  # Artist/Book/Songs/file.pdf
                artist = parts[0]
                book = parts[1]
                folder_key = f"{artist}/{book}".lower()
                s3_folders[folder_key] += 1

print(f"S3 folders: {len(s3_folders)}")

# Find S3 folders not in local
s3_only = []
for s3_folder, count in s3_folders.items():
    if s3_folder not in local_folders:
        s3_only.append((s3_folder, count))

s3_only.sort(key=lambda x: -x[1])  # Sort by PDF count descending

print(f"\nS3 folders NOT in local: {len(s3_only)}")
print("\n" + "=" * 80)
print("S3 FOLDERS WITHOUT LOCAL MATCH (showing all)")
print("=" * 80)

for folder, count in s3_only:
    print(f"{folder} ({count} PDFs)")

# Save to file
with open('s3_folders_not_in_local.txt', 'w', encoding='utf-8') as f:
    f.write(f"S3 FOLDERS WITHOUT LOCAL MATCH\n")
    f.write(f"Total: {len(s3_only)} folders\n")
    f.write("=" * 80 + "\n\n")
    for folder, count in s3_only:
        f.write(f"{folder} ({count} PDFs)\n")

print(f"\n\nResults saved to: s3_folders_not_in_local.txt")
