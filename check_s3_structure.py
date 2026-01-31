import boto3

# Initialize S3 client
s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'jsmith-output'

# Check a few specific folders
test_folders = [
    "Night Ranger - Seven Wishes [jap Score]",
    "Robbie Robertson - Songbook [guitar Tab]",
    "Various Artists - Ultimate 80's Songs"
]

print("CHECKING S3 STRUCTURE")
print("=" * 80)

for folder in test_folders:
    print(f"\n{folder}")
    
    # Try with trailing slash
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix=folder, MaxKeys=5)
    
    count = 0
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                print(f"  {obj['Key']}")
                count += 1
                if count >= 5:
                    break
        if count >= 5:
            break
    
    if count == 0:
        print("  (no files found)")
