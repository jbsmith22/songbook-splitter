#!/usr/bin/env python3
"""
Show COMPLETE data picture for a single songbook.
Fetches and displays ALL artifacts, metadata, and files.
"""
import json
import sys
import boto3
from pathlib import Path
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'

def fetch_source_pdf_info(source_uri):
    """Get source PDF metadata."""
    if not source_uri or not source_uri.startswith('s3://'):
        return None

    key = source_uri.replace(f's3://{INPUT_BUCKET}/', '')
    try:
        response = s3.head_object(Bucket=INPUT_BUCKET, Key=key)
        return {
            's3_uri': source_uri,
            'size_bytes': response['ContentLength'],
            'last_modified': response['LastModified'].isoformat(),
            'exists': True
        }
    except:
        return {'s3_uri': source_uri, 'exists': False}

def fetch_dynamodb_record(book_id):
    """Get DynamoDB processing record."""
    try:
        response = table.get_item(Key={'book_id': book_id})
        return response.get('Item', None)
    except:
        return None

def fetch_s3_artifact(book_id, artifact_name):
    """Fetch a specific S3 artifact."""
    key = f'artifacts/{book_id}/{artifact_name}'
    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except:
        return None

def fetch_s3_output_manifest(book_id):
    """Fetch S3 output manifest."""
    key = f'output/{book_id}/manifest.json'
    try:
        response = s3.get_object(Bucket=OUTPUT_BUCKET, Key=key)
        return json.loads(response['Body'].read())
    except:
        return None

def list_s3_output_pdfs(book_id):
    """List all PDFs in S3 output folder."""
    prefix = f'output/{book_id}/'
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pdfs = []
        for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                if obj['Key'].endswith('.pdf'):
                    pdfs.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].isoformat()
                    })
        return pdfs
    except:
        return []

def find_local_data(book_id):
    """Find local manifest and PDFs for this book."""
    base = Path('ProcessedSongs_Final')

    # Search for manifest with this book_id
    for manifest_file in base.rglob('manifest.json'):
        try:
            with open(manifest_file) as f:
                manifest = json.load(f)
            if manifest.get('book_id') == book_id:
                folder = manifest_file.parent
                pdfs = list(folder.glob('*.pdf'))
                return {
                    'folder': str(folder.relative_to(base)),
                    'manifest': manifest,
                    'pdf_count': len(pdfs),
                    'pdfs': [{'name': p.name, 'size': p.stat().st_size} for p in pdfs]
                }
        except:
            continue

    return None

def find_provenance_entry(book_id):
    """Find entry in v2_provenance_data.js."""
    try:
        with open('data/analysis/v2_provenance_data.js', 'r', encoding='utf-8') as f:
            content = f.read()

        import re
        match = re.search(r'const V2_PROVENANCE_DATA = ({.*});', content, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            for book in data.get('songbooks', []):
                if book.get('mapping', {}).get('book_id') == book_id:
                    return book
    except:
        pass

    return None

def display_complete_data(book_id):
    """Fetch and display ALL data for a book."""

    print("=" * 100)
    print(f"COMPLETE DATA PICTURE FOR: {book_id}")
    print("=" * 100)
    print()

    # 1. DynamoDB
    print("1. DYNAMODB RECORD")
    print("-" * 100)
    dynamo = fetch_dynamodb_record(book_id)
    if dynamo:
        for key in sorted(dynamo.keys()):
            if key != 'execution_history':  # Skip long history
                print(f"  {key}: {dynamo[key]}")
    else:
        print("  ❌ NOT FOUND")
    print()

    # 2. Source PDF
    print("2. SOURCE PDF")
    print("-" * 100)
    source_uri = dynamo.get('source_pdf_uri') if dynamo else None
    if source_uri:
        source_info = fetch_source_pdf_info(source_uri)
        if source_info:
            for key, val in source_info.items():
                print(f"  {key}: {val}")
    else:
        print("  ❌ NO SOURCE URI IN DYNAMODB")
    print()

    # 3. S3 Artifacts
    print("3. S3 ARTIFACTS")
    print("-" * 100)
    artifacts = [
        'toc_discovery.json',
        'toc_parse.json',
        'page_analysis.json',
        'page_mapping.json',
        'verified_songs.json',
        'output_files.json'
    ]

    artifact_data = {}
    for artifact in artifacts:
        data = fetch_s3_artifact(book_id, artifact)
        artifact_data[artifact] = data

        if data:
            # Show summary
            if artifact == 'toc_discovery.json':
                pages = data.get('pages', [])
                print(f"  ✓ {artifact}: {len(pages)} candidate pages")
            elif artifact == 'toc_parse.json':
                songs = data.get('songs', [])
                print(f"  ✓ {artifact}: {len(songs)} songs from TOC")
            elif artifact == 'page_analysis.json':
                pages = data.get('pages', [])
                errors = sum(1 for p in pages if p.get('content_type') == 'error')
                print(f"  ✓ {artifact}: {len(pages)} pages, {errors} errors ({errors/len(pages)*100 if pages else 0:.1f}%)")
            elif artifact == 'page_mapping.json':
                songs = data.get('songs', [])
                print(f"  ✓ {artifact}: {len(songs)} mapped songs")
            elif artifact == 'verified_songs.json':
                songs = data.get('verified_songs', [])
                print(f"  ✓ {artifact}: {len(songs)} verified songs")
            elif artifact == 'output_files.json':
                files = data.get('output_files', [])
                print(f"  ✓ {artifact}: {len(files)} output files")
        else:
            print(f"  ❌ {artifact}: NOT FOUND")
    print()

    # 4. S3 Output
    print("4. S3 OUTPUT")
    print("-" * 100)
    output_manifest = fetch_s3_output_manifest(book_id)
    if output_manifest:
        print(f"  ✓ manifest.json exists")
        print(f"    - processing_timestamp: {output_manifest.get('processing_timestamp')}")
    else:
        print(f"  ❌ manifest.json NOT FOUND")

    output_pdfs = list_s3_output_pdfs(book_id)
    print(f"  PDFs in output/{book_id}/: {len(output_pdfs)}")
    print()

    # 5. Local Files
    print("5. LOCAL FILES (ProcessedSongs_Final)")
    print("-" * 100)
    local = find_local_data(book_id)
    if local:
        print(f"  ✓ Found in: {local['folder']}")
        print(f"    - manifest.json exists")
        print(f"    - PDFs: {local['pdf_count']}")
        print(f"    - Total songs in manifest: {local['manifest'].get('total_entries', 0)}")
    else:
        print(f"  ❌ NO LOCAL DATA FOUND")
    print()

    # 6. Provenance
    print("6. PROVENANCE TRACKING")
    print("-" * 100)
    prov = find_provenance_entry(book_id)
    if prov:
        print(f"  ✓ Entry found in v2_provenance_data.js")
        print(f"    - status: {prov.get('mapping', {}).get('mapping_status')}")
        print(f"    - actual_songs: {prov.get('verification', {}).get('actual_songs')}")
    else:
        print(f"  ❌ NO PROVENANCE ENTRY")
    print()

    # Summary Comparison
    print("7. DATA CONSISTENCY CHECK")
    print("-" * 100)

    verified_count = len(artifact_data.get('verified_songs.json', {}).get('verified_songs', [])) if artifact_data.get('verified_songs.json') else 0
    output_files_count = len(artifact_data.get('output_files.json', {}).get('output_files', [])) if artifact_data.get('output_files.json') else 0
    local_count = local['pdf_count'] if local else 0

    print(f"  verified_songs.json: {verified_count} songs")
    print(f"  output_files.json: {output_files_count} files")
    print(f"  Local PDFs: {local_count} files")

    if verified_count == output_files_count == local_count:
        print(f"  ✓ ALL COUNTS MATCH")
    else:
        print(f"  ❌ COUNTS DO NOT MATCH")

    print()
    print("=" * 100)

    # Save full data dump
    output_file = Path(f'data/analysis/complete_book_data_{book_id}.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'book_id': book_id,
            'timestamp': datetime.now().isoformat(),
            'dynamodb': dynamo,
            'source_pdf': source_info if source_uri else None,
            'artifacts': artifact_data,
            's3_output_manifest': output_manifest,
            's3_output_pdfs': output_pdfs,
            'local': local,
            'provenance': prov
        }, f, indent=2)

    print(f"Complete data saved to: {output_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python show_complete_book_data.py <book_id>")
        print()
        print("Example: python show_complete_book_data.py v2-00171fce4db3bdf9-2")
        sys.exit(1)

    book_id = sys.argv[1]
    display_complete_data(book_id)
