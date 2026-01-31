import boto3

# Initialize S3 client
s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'jsmith-output'

# Search for specific folder names
search_terms = [
    "Seven Wishes",
    "Robbie Robertson - Songbook",
    "Ultimate 80",
    "Little Shop Of Horrors"
]

print("SEARCHING FOR FOLDERS IN S3")
print("=" * 80)

# Get all objects
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket)

found_folders = {}

for page in pages:
    if 'Contents' not in page:
        continue
        
    for obj in page['Contents']:
        key = obj['Key']
        
        # Check if any search term is in the key
        for term in search_terms:
            if term.lower() in key.lower():
                # Extract folder path (everything before the filename)
                parts = key.split('/')
                if len(parts) >= 2:
                    folder = '/'.join(parts[:-1])
                    if folder not in found_folders:
                        found_folders[folder] = []
                    found_folders[folder].append(obj['Key'])

print("\nFOUND FOLDERS:")
for folder, files in sorted(found_folders.items()):
    print(f"\n{folder}")
    print(f"  Files: {len(files)}")
    for f in files[:3]:  # Show first 3 files
        print(f"    - {f.split('/')[-1]}")
    if len(files) > 3:
        print(f"    ... and {len(files) - 3} more")
