#!/usr/bin/env python3
"""Quick check of how many books are unprocessed."""
import boto3
import hashlib
from pathlib import Path

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

def generate_book_id(source_pdf_path: str, version: int = 2) -> str:
    """Generate deterministic book ID from source PDF path."""
    content = f"{source_pdf_path}-v{version}"
    hash_obj = hashlib.md5(content.encode())
    return f"v{version}-{hash_obj.hexdigest()}"

# Get processed source PDFs (not book IDs, since IDs can have retry suffixes)
print("Scanning DynamoDB for processed books...")
response = table.scan(
    FilterExpression='begins_with(book_id, :v2)',
    ExpressionAttributeValues={':v2': 'v2-'}
)

processed_sources = set()
for item in response['Items']:
    if item.get('status') == 'success' and 'source_pdf_uri' in item:
        # Extract relative path from S3 URI
        uri = item['source_pdf_uri']
        if uri.startswith('s3://jsmith-input/'):
            rel_path = uri.replace('s3://jsmith-input/', '')
            processed_sources.add(rel_path)

while 'LastEvaluatedKey' in response:
    response = table.scan(
        FilterExpression='begins_with(book_id, :v2)',
        ExpressionAttributeValues={':v2': 'v2-'},
        ExclusiveStartKey=response['LastEvaluatedKey']
    )
    for item in response['Items']:
        if item.get('status') == 'success' and 'source_pdf_uri' in item:
            uri = item['source_pdf_uri']
            if uri.startswith('s3://jsmith-input/'):
                rel_path = uri.replace('s3://jsmith-input/', '')
                processed_sources.add(rel_path)

print(f"OK Found {len(processed_sources)} processed V2 books")

# Count total PDFs
sheetmusic_dir = Path('SheetMusic')
all_pdfs = list(sheetmusic_dir.rglob('*.pdf'))
print(f"OK Found {len(all_pdfs)} total PDFs in SheetMusic")

# Count unprocessed
unprocessed_count = 0
for pdf_path in all_pdfs:
    rel_path = pdf_path.relative_to(sheetmusic_dir)
    source_pdf = str(rel_path).replace('\\', '/')

    if source_pdf not in processed_sources:
        unprocessed_count += 1

print(f"\n{'='*60}")
print(f"UNPROCESSED BOOKS: {unprocessed_count}")
print(f"{'='*60}")
print(f"\nYou can process them with:")
print(f"  python scripts/batch_process_books.py 100")
