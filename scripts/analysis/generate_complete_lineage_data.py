#!/usr/bin/env python3
"""
Generate complete data lineage for all V2 books showing ALL 13+ artifacts.
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

def check_artifact_exists(book_id, artifact_name):
    """Check if S3 artifact exists."""
    key = f'artifacts/{book_id}/{artifact_name}'
    try:
        s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
        return True
    except:
        return False

def get_artifact_summary(book_id, artifact_name):
    """Get summary of artifact contents."""
    key = f'artifacts/{book_id}/{artifact_name}'
    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        data = json.loads(response['Body'].read())

        if artifact_name == 'toc_discovery.json':
            return {'pages': len(data.get('pages', []))}
        elif artifact_name == 'toc_parse.json':
            return {'songs': len(data.get('songs', []))}
        elif artifact_name == 'page_analysis.json':
            pages = data.get('pages', [])
            errors = sum(1 for p in pages if p.get('content_type') == 'error')
            return {
                'total_pages': len(pages),
                'errors': errors,
                'error_rate': round(errors/len(pages)*100, 1) if pages else 0
            }
        elif artifact_name == 'page_mapping.json':
            return {'songs': len(data.get('songs', []))}
        elif artifact_name == 'verified_songs.json':
            return {'songs': len(data.get('verified_songs', []))}
        elif artifact_name == 'output_files.json':
            return {'files': len(data.get('output_files', []))}
        return {}
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

def count_s3_output_pdfs_from_artifact(book_id):
    """Count PDFs by extracting the actual S3 path from output_files.json artifact."""
    try:
        # Get output_files.json which has the actual S3 paths
        key = f'artifacts/{book_id}/output_files.json'
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        data = json.loads(response['Body'].read())
        output_files = data.get('output_files', [])

        if not output_files:
            return 0

        # Extract the prefix from the first file's path
        # Path format: s3://jsmith-output/Acdc/Anthology/Songs/Acdc - Song.pdf
        first_uri = output_files[0].get('output_uri', '')
        if not first_uri.startswith('s3://'):
            return 0

        # Remove s3://jsmith-output/ and get path up to /Songs/
        path = first_uri.replace(f's3://{OUTPUT_BUCKET}/', '')
        # Extract prefix up to and including /Songs/
        if '/Songs/' in path:
            prefix = path[:path.index('/Songs/') + len('/Songs/')]
        else:
            return 0

        # Now count PDFs with this prefix
        paginator = s3.get_paginator('list_objects_v2')
        count = 0
        for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.pdf'):
                    count += 1
        return count
    except:
        return 0

def check_source_pdf(source_uri):
    """Check if source PDF exists."""
    if not source_uri or not source_uri.startswith('s3://'):
        return False
    key = source_uri.replace(f's3://{INPUT_BUCKET}/', '')
    try:
        s3.head_object(Bucket=INPUT_BUCKET, Key=key)
        return True
    except:
        return False

def get_dynamodb_record(book_id):
    """Get DynamoDB record summary."""
    try:
        response = table.get_item(Key={'book_id': book_id})
        item = response.get('Item')
        if item:
            return {
                'exists': True,
                'status': item.get('status'),
                'artist': item.get('artist'),
                'book_name': item.get('book_name'),
                'songs_extracted': decimal_to_number(item.get('songs_extracted')),
                'source_pdf_uri': item.get('source_pdf_uri')
            }
    except:
        pass
    return {'exists': False}

def find_local_manifest(book_id):
    """Find local manifest for book."""
    base = Path('ProcessedSongs_Final')
    for manifest_file in base.rglob('manifest.json'):
        try:
            with open(manifest_file) as f:
                manifest = json.load(f)
            if manifest.get('book_id') == book_id:
                folder = manifest_file.parent
                pdfs = list(folder.glob('*.pdf'))
                return {
                    'exists': True,
                    'folder': str(folder.relative_to(base)),
                    'pdf_count': len(pdfs),
                    'total_songs': manifest.get('total_entries', 0)
                }
        except:
            continue
    return {'exists': False}

def find_provenance_entry(book_id):
    """Check if provenance entry exists."""
    try:
        with open('data/analysis/v2_provenance_data.js', 'r', encoding='utf-8') as f:
            content = f.read()
        import re
        match = re.search(r'const V2_PROVENANCE_DATA = ({.*});', content, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            for book in data.get('songbooks', []):
                if book.get('mapping', {}).get('book_id') == book_id:
                    return {
                        'exists': True,
                        'status': book.get('mapping', {}).get('mapping_status'),
                        'actual_songs': book.get('verification', {}).get('actual_songs')
                    }
    except:
        pass
    return {'exists': False}

# Load V2 analysis to get book list
print("Loading V2 analysis...")
with open('data/analysis/v2_only_analysis.json') as f:
    v2_data = json.load(f)

print(f"Processing {len(v2_data['books'])} V2 books...")

complete_lineage = {
    'generated': '2026-02-06',
    'summary': v2_data['summary'],
    'books': []
}

artifacts_to_check = [
    'toc_discovery.json',
    'toc_parse.json',
    'page_analysis.json',
    'page_mapping.json',
    'verified_songs.json',
    'output_files.json'
]

for i, book in enumerate(v2_data['books'], 1):
    book_id = book['book_id']
    print(f"  [{i}/{len(v2_data['books'])}] {book_id}")

    # Get DynamoDB record
    dynamo = get_dynamodb_record(book_id)

    # Check source PDF
    source_pdf_exists = False
    if dynamo.get('source_pdf_uri'):
        source_pdf_exists = check_source_pdf(dynamo['source_pdf_uri'])

    # Check all S3 artifacts
    s3_artifacts = {}
    for artifact_name in artifacts_to_check:
        exists = check_artifact_exists(book_id, artifact_name)
        summary = None
        if exists:
            summary = get_artifact_summary(book_id, artifact_name)
        s3_artifacts[artifact_name] = {
            'exists': exists,
            'summary': summary
        }

    # Check S3 output
    s3_output_manifest = check_s3_output_manifest(book_id)
    s3_output_pdfs = count_s3_output_pdfs_from_artifact(book_id)

    # Check local files
    local = find_local_manifest(book_id)

    # Check provenance
    provenance = find_provenance_entry(book_id)

    # Calculate data completeness
    total_artifacts = 13  # 1 source + 1 dynamo + 6 s3 artifacts + 1 s3 manifest + 1 local manifest + 1 provenance + PDFs
    exists_count = sum([
        1 if source_pdf_exists else 0,
        1 if dynamo['exists'] else 0,
        sum(1 for a in s3_artifacts.values() if a['exists']),
        1 if s3_output_manifest else 0,
        1 if local['exists'] else 0,
        1 if provenance['exists'] else 0
    ])

    # Determine consistency status
    verified_count = s3_artifacts.get('verified_songs.json', {}).get('summary', {}).get('songs', 0) if s3_artifacts.get('verified_songs.json', {}).get('exists') else 0
    output_files_count = s3_artifacts.get('output_files.json', {}).get('summary', {}).get('files', 0) if s3_artifacts.get('output_files.json', {}).get('exists') else 0
    local_pdfs = local.get('pdf_count', 0) if local['exists'] else 0

    consistent = verified_count == output_files_count == local_pdfs if local['exists'] else verified_count == output_files_count

    book_lineage = {
        'book_id': book_id,
        'completeness': {
            'exists_count': exists_count,
            'total_expected': total_artifacts,
            'percentage': round(exists_count / total_artifacts * 100, 1)
        },
        'consistency': {
            'status': 'CONSISTENT' if consistent else 'INCONSISTENT',
            'verified_songs': verified_count,
            'output_files': output_files_count,
            'local_pdfs': local_pdfs
        },
        'artifacts': {
            '1_source_pdf': {
                'exists': source_pdf_exists,
                'uri': dynamo.get('source_pdf_uri', 'N/A')
            },
            '2_dynamodb': dynamo,
            '3_s3_artifacts': s3_artifacts,
            '4_s3_output_manifest': {
                'exists': s3_output_manifest
            },
            '5_s3_output_pdfs': {
                'count': s3_output_pdfs
            },
            '6_local_manifest': local,
            '7_local_pdfs': {
                'count': local_pdfs
            },
            '8_provenance': provenance
        },
        'page_analysis_error_rate': book.get('page_analysis_error_rate', 0),
        'local_folder': local.get('folder', 'N/A')
    }

    complete_lineage['books'].append(book_lineage)

# Save complete lineage data
output_file = Path('data/analysis/complete_lineage_data.json')
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(complete_lineage, f, indent=2, default=decimal_to_number)

print(f"\nOK Complete lineage data saved to: {output_file}")
print(f"  Total books: {len(complete_lineage['books'])}")
print(f"  Average completeness: {sum(b['completeness']['percentage'] for b in complete_lineage['books']) / len(complete_lineage['books']):.1f}%")

consistent_books = sum(1 for b in complete_lineage['books'] if b['consistency']['status'] == 'CONSISTENT')
print(f"  Consistent books: {consistent_books}/{len(complete_lineage['books'])}")
