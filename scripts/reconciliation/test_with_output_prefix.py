"""
Test if adding output/ prefix finds the files
"""
import boto3

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

# Test with output/ prefix
artist_path = 'Adele/19 [pvg Book]'

prefixes_to_try = [
    f"output/{artist_path}/",
    f"output/{artist_path}/Songs/",
    f"output/{artist_path}/songs/"
]

print("Testing with output/ prefix...\n")

for prefix in prefixes_to_try:
    print(f"Trying: {prefix}")
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
            if 'Contents' in page:
                pdf_files = [obj for obj in page['Contents'] if obj['Key'].endswith('.pdf')]
                print(f"  Found {len(pdf_files)} PDF files")
                for obj in pdf_files[:3]:
                    print(f"    - {obj['Key']}")
                if len(pdf_files) > 3:
                    print(f"    ... and {len(pdf_files) - 3} more")
                break
        else:
            print(f"  No objects found")
    except Exception as e:
        print(f"  ERROR: {e}")
    print()
