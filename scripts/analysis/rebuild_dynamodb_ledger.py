"""
Rebuild DynamoDB ledger based on actual files in S3
"""
import json
import boto3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
bucket = 'jsmith-output'
table = dynamodb.Table('jsmith-processing-ledger')

# Load validation data
print("Loading validation data...")
with open('data/analysis/final_validation_data.json', 'r') as f:
    validation_data = json.load(f)

matched_folders = validation_data.get('matched', [])
print(f"Found {len(matched_folders)} matched folders\n")

stats = defaultdict(int)
errors = []

# Process each matched folder
for i, match in enumerate(matched_folders, 1):
    book_id = match.get('book_id', '')
    s3_path = match.get('s3_path', '')
    local_path = match.get('local_path', '')
    artist = s3_path.split('/')[0] if '/' in s3_path else ''
    book_name = '/'.join(s3_path.split('/')[1:]) if '/' in s3_path else s3_path

    if not book_id or book_id in ['fuzzy', 'unknown', '']:
        stats['no_book_id'] += 1
        continue

    if i % 50 == 0:
        print(f"Processing {i}/{len(matched_folders)}...")

    try:
        # Count actual S3 files
        file_count = 0
        paginator = s3_client.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=bucket, Prefix=f"{s3_path}/"):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.pdf'):
                        file_count += 1

        # Create DynamoDB entry
        item = {
            'book_id': book_id,
            'processing_timestamp': int(datetime.now().timestamp()),
            'status': 'success',
            'source_pdf_uri': f's3://{bucket}/{s3_path}',
            'artist': artist,
            'book_name': book_name,
            's3_output_path': s3_path,
            'local_output_path': local_path,
            'manifest_uri': f's3://{bucket}/output/{book_id}/manifest.json',
            'songs_extracted': file_count,
            'rebuilt_from_actual_files': True,
            'rebuild_timestamp': datetime.now().isoformat()
        }

        # Put item in DynamoDB
        table.put_item(Item=item)
        stats['entries_created'] += 1

    except Exception as e:
        errors.append(f"Failed to process {s3_path}: {e}")
        stats['errors'] += 1

print(f"\n{'='*60}")
print("REBUILD DYNAMODB LEDGER SUMMARY")
print(f"{'='*60}")
print(f"Folders processed:       {len(matched_folders)}")
print(f"Entries created:         {stats['entries_created']}")
print(f"No book_id:              {stats['no_book_id']}")
print(f"Errors:                  {stats['errors']}")

if errors:
    print(f"\n{'='*60}")
    print("ERRORS")
    print(f"{'='*60}")
    for error in errors[:20]:
        print(f"  {error}")
    if len(errors) > 20:
        print(f"  ... and {len(errors) - 20} more errors")

print("\nOK DynamoDB ledger rebuild complete!")
print("DynamoDB now accurately reflects actual files in S3.")
