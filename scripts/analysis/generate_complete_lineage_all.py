#!/usr/bin/env python3
"""
Generate complete data lineage for ALL V2 books in DynamoDB.
Performs physical verification of all data stores.
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict
from decimal import Decimal

def decimal_to_number(obj):
    """Convert Decimal to int or float for JSON serialization."""
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

OUTPUT_BUCKET = 'jsmith-output'
INPUT_BUCKET = 'jsmith-input'

# 13+ artifact types to verify
ARTIFACT_TYPES = [
    'toc_discovery.json',
    'toc_parsing.json',
    'page_analysis.json',
    'page_mapping.json',
    'song_verification.json',
    'output_files.json',
    'toc_enhanced.json',
    'split_decisions.json',
    'vision_analysis.json',
    'manual_split.json',
    'manual_toc.json',
    'reprocessing_metadata.json',
    'processing_log.json'
]

def check_artifact_exists(book_id, artifact_name):
    """Check if artifact exists in S3."""
    key = f'artifacts/{book_id}/{artifact_name}'
    try:
        s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
        return True
    except:
        return False

def get_artifact_summary(book_id, artifact_name):
    """Get summary info from artifact."""
    key = f'artifacts/{book_id}/{artifact_name}'
    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        data = json.loads(response['Body'].read())

        # Extract relevant summary based on artifact type
        if artifact_name == 'page_analysis.json':
            return {
                'songs_count': len(data.get('songs', [])),
                'pages_analyzed': len(data.get('pages', []))
            }
        elif artifact_name == 'output_files.json':
            return {
                'output_files_count': len(data.get('output_files', []))
            }
        elif artifact_name == 'song_verification.json':
            return {
                'verified_songs': len(data.get('verified_songs', []))
            }
        else:
            return {'exists': True}
    except:
        return None

def check_s3_output_manifest(book_id):
    """Check if S3 output manifest exists."""
    key = f'output/{book_id}/manifest.json'
    try:
        s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
        return True
    except:
        return False

def count_s3_output_pdfs(book_id):
    """Count PDFs in S3 output using output_files.json artifact."""
    try:
        key = f'artifacts/{book_id}/output_files.json'
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        data = json.loads(response['Body'].read())
        output_files = data.get('output_files', [])

        if not output_files:
            return 0

        # Extract prefix from first file
        first_uri = output_files[0].get('output_uri', '')
        if not first_uri.startswith('s3://'):
            return 0

        path = first_uri.replace(f's3://{OUTPUT_BUCKET}/', '')
        if '/Songs/' in path:
            prefix = path[:path.index('/Songs/') + len('/Songs/')]
        else:
            return 0

        # Count PDFs with this prefix
        paginator = s3.get_paginator('list_objects_v2')
        count = 0
        for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.pdf'):
                    count += 1
        return count
    except:
        return 0

def find_local_manifest(book_id):
    """Find local manifest for book."""
    # Check ProcessedSongs_Final folders
    processed_dir = Path('ProcessedSongs_Final')
    if processed_dir.exists():
        for manifest_file in processed_dir.rglob('manifest.json'):
            try:
                with open(manifest_file) as f:
                    data = json.load(f)
                    if data.get('book_id') == book_id:
                        return {
                            'exists': True,
                            'path': str(manifest_file),
                            'folder': str(manifest_file.parent),
                            'songs_count': len(data.get('songs', []))
                        }
            except:
                continue
    return {'exists': False}

def get_all_v2_books():
    """Get all V2 books from DynamoDB."""
    print("Scanning DynamoDB for all V2 books...")
    books = []

    response = table.scan(
        FilterExpression='begins_with(book_id, :v2)',
        ExpressionAttributeValues={':v2': 'v2-'}
    )

    books.extend(response['Items'])

    while 'LastEvaluatedKey' in response:
        response = table.scan(
            FilterExpression='begins_with(book_id, :v2)',
            ExpressionAttributeValues={':v2': 'v2-'},
            ExclusiveStartKey=response['LastEvaluatedKey']
        )
        books.extend(response['Items'])

    print(f"  Found {len(books)} V2 books in DynamoDB")
    return books

def verify_book(book_id, dynamodb_item):
    """Perform complete verification of all data stores for a book."""
    # Check all S3 artifacts
    s3_artifacts = {}
    for artifact_name in ARTIFACT_TYPES:
        exists = check_artifact_exists(book_id, artifact_name)
        summary = None
        if exists and artifact_name in ['page_analysis.json', 'output_files.json', 'song_verification.json']:
            summary = get_artifact_summary(book_id, artifact_name)
        s3_artifacts[artifact_name] = {
            'exists': exists,
            'summary': summary
        }

    # Check S3 output
    s3_output_manifest = check_s3_output_manifest(book_id)
    s3_output_pdfs = count_s3_output_pdfs(book_id)

    # Check local files
    local = find_local_manifest(book_id)

    # Calculate completeness
    artifacts_present = sum(1 for a in s3_artifacts.values() if a['exists'])
    completeness_pct = (artifacts_present / len(ARTIFACT_TYPES)) * 100

    # Check consistency
    page_analysis_summary = s3_artifacts.get('page_analysis.json', {}).get('summary')
    output_files_summary = s3_artifacts.get('output_files.json', {}).get('summary')

    page_analysis_songs = page_analysis_summary.get('songs_count', 0) if page_analysis_summary else 0
    output_files_count = output_files_summary.get('output_files_count', 0) if output_files_summary else 0

    consistent = page_analysis_songs == output_files_count if page_analysis_songs and output_files_count else False

    return {
        'book_id': book_id,
        'dynamodb': {
            'exists': True,
            'status': dynamodb_item.get('status'),
            'artist': dynamodb_item.get('artist'),
            'book_name': dynamodb_item.get('book_name'),
            'songs_extracted': decimal_to_number(dynamodb_item.get('songs_extracted')),
            'source_pdf_uri': dynamodb_item.get('source_pdf_uri')
        },
        's3_artifacts': s3_artifacts,
        's3_output': {
            'manifest_exists': s3_output_manifest,
            'pdf_count': s3_output_pdfs
        },
        'local': local,
        'completeness': {
            'percentage': completeness_pct,
            'artifacts_present': artifacts_present,
            'total_artifacts': len(ARTIFACT_TYPES)
        },
        'consistency': {
            'status': 'CONSISTENT' if consistent else 'INCONSISTENT',
            'page_analysis_songs': page_analysis_songs,
            'output_files_count': output_files_count,
            's3_pdf_count': s3_output_pdfs
        }
    }

def main():
    print("="*80)
    print("COMPLETE DATA LINEAGE VERIFICATION")
    print("="*80)

    # Get all V2 books from DynamoDB
    all_dynamodb_books = get_all_v2_books()

    # Group by source PDF to get only the latest/best version of each unique book
    print("Deduplicating by source PDF...")
    books_by_source = {}

    for item in all_dynamodb_books:
        source_uri = item.get('source_pdf_uri', '')
        if not source_uri:
            continue

        # Prefer successful books, then in_progress, then failed
        status = item.get('status', '')
        priority = 0 if status == 'success' else (1 if status == 'in_progress' else 2)

        source_key = source_uri.replace('s3://jsmith-input/', '')

        if source_key not in books_by_source or books_by_source[source_key][1] > priority:
            books_by_source[source_key] = (item, priority)

    # Extract just the book items
    dynamodb_books = [book_data[0] for book_data in books_by_source.values()]

    print(f"  {len(all_dynamodb_books)} total DynamoDB entries")
    print(f"  {len(dynamodb_books)} unique source PDFs")

    print(f"\nVerifying all data stores for {len(dynamodb_books)} unique books...")
    print("(This will take several minutes...)\n")

    complete_lineage = {
        'generated_at': Path('data/analysis/complete_lineage_data.json').stat().st_mtime if Path('data/analysis/complete_lineage_data.json').exists() else None,
        'total_books': len(dynamodb_books),
        'total_entries': len(all_dynamodb_books),
        'books': []
    }

    for i, item in enumerate(dynamodb_books, 1):
        book_id = item['book_id']
        if i % 25 == 0:
            print(f"  [{i}/{len(dynamodb_books)}] {book_id}")

        book_lineage = verify_book(book_id, item)
        complete_lineage['books'].append(book_lineage)

    # Save complete lineage data
    output_file = Path('data/analysis/complete_lineage_data.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_lineage, f, indent=2, default=decimal_to_number)

    print(f"\n{'='*80}")
    print("VERIFICATION COMPLETE")
    print(f"{'='*80}")
    print(f"OK Complete lineage data saved to: {output_file}")
    print(f"  Total unique books: {len(complete_lineage['books'])}")
    print(f"  Total DynamoDB entries: {complete_lineage['total_entries']} (includes retries)")

    avg_completeness = sum(b['completeness']['percentage'] for b in complete_lineage['books']) / len(complete_lineage['books'])
    print(f"  Average completeness: {avg_completeness:.1f}%")

    consistent_books = sum(1 for b in complete_lineage['books'] if b['consistency']['status'] == 'CONSISTENT')
    print(f"  Consistent books: {consistent_books}/{len(complete_lineage['books'])}")

    success_books = sum(1 for b in complete_lineage['books'] if b['dynamodb']['status'] == 'success')
    print(f"  Successful books: {success_books}/{len(complete_lineage['books'])}")

    local_synced = sum(1 for b in complete_lineage['books'] if b['local']['exists'])
    print(f"  Local files synced: {local_synced}/{len(complete_lineage['books'])}")

if __name__ == '__main__':
    main()
