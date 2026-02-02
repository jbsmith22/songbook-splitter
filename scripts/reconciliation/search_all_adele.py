"""
Search entire output bucket for any files containing "Adele"
"""
import boto3

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

print("Searching entire output/ prefix for files containing 'Adele'...\n")

paginator = s3.get_paginator('list_objects_v2')
adele_files = []

for page in paginator.paginate(Bucket=S3_BUCKET, Prefix='output/'):
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            if 'Adele' in key or 'adele' in key:
                adele_files.append(obj)

print(f"Found {len(adele_files)} files/objects containing 'Adele':\n")

for obj in adele_files:
    key = obj['Key']
    size_kb = obj['Size'] / 1024
    is_pdf = 'PDF' if key.endswith('.pdf') else ''
    print(f"  {key} ({size_kb:.1f} KB) {is_pdf}")
