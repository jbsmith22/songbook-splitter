"""
Test the get_s3_files function to see what it actually returns
"""
import boto3

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

def get_s3_files(s3_path):
    """Get all PDF files in S3 folder with sizes (handles /Songs/ subfolder)"""
    files = {}

    # Try both with and without /Songs/ subfolder
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    print(f"Searching for s3_path: {s3_path}")
    print(f"Trying prefixes:")
    for p in prefixes:
        print(f"  - {p}")
    print()

    for prefix in prefixes:
        print(f"Searching: {prefix}")
        try:
            paginator = s3.get_paginator('list_objects_v2')
            found_any = False
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
                if 'Contents' in page:
                    found_any = True
                    print(f"  Found {len(page['Contents'])} objects")
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.endswith('.pdf'):
                            filename = key.split('/')[-1]
                            # Only add if not already found (prefer non-Songs version)
                            if filename not in files:
                                files[filename] = {
                                    'key': key,
                                    'size': obj['Size']
                                }
                            print(f"    PDF: {filename}")
            if not found_any:
                print(f"  No objects found")
        except Exception as e:
            print(f"  ERROR: {e}")
            continue
        print()

    return files

# Test with Adele path
result = get_s3_files("Adele/19 [pvg Book]")
print(f"\nResult: {len(result)} files")
for filename, info in result.items():
    print(f"  {filename} - {info['size']} bytes")
