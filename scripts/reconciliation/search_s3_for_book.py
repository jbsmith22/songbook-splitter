"""
Search entire S3 bucket for files belonging to a specific book_id
"""
import boto3
import sys

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

book_id = '8e5ac0bec0eeed0f'  # Adele - 19

print(f"Searching for book_id: {book_id}\n")

# First check if manifest exists
print("Checking for manifest...")
try:
    response = s3.head_object(Bucket=S3_BUCKET, Key=f'output/{book_id}/manifest.json')
    print(f"  Found manifest at: output/{book_id}/manifest.json")
    print(f"  Size: {response['ContentLength']} bytes")
    print(f"  Last modified: {response['LastModified']}")

    # Get the manifest content
    response = s3.get_object(Bucket=S3_BUCKET, Key=f'output/{book_id}/manifest.json')
    import json
    manifest = json.loads(response['Body'].read().decode('utf-8'))

    print(f"\n  Manifest says:")
    print(f"    Artist: {manifest.get('artist')}")
    print(f"    Book: {manifest.get('book_name')}")
    print(f"    Source: {manifest.get('source_pdf')}")

    if 'output' in manifest and 'songs' in manifest['output']:
        print(f"    Songs in manifest: {len(manifest['output']['songs'])}")

except Exception as e:
    print(f"  ERROR: {e}")

# List all files for this book_id
print(f"\nListing all files under output/{book_id}/...")
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=S3_BUCKET, Prefix=f'output/{book_id}/')

all_objects = []
for page in pages:
    if 'Contents' in page:
        all_objects.extend(page['Contents'])

print(f"Found {len(all_objects)} files")
for obj in all_objects[:20]:
    key = obj['Key']
    size_kb = obj['Size'] / 1024
    print(f"  {key} ({size_kb:.1f} KB)")

if len(all_objects) > 20:
    print(f"  ... and {len(all_objects) - 20} more files")
