"""
Trace complete lineage of a specific songbook: Carole King - Tapestry
"""
import json
import boto3
from pathlib import Path

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('='*80)
print('COMPLETE LINEAGE: Carole King - Tapestry')
print('='*80)

# 1. Find source PDF
sheet_music = Path('d:/Work/songbook-splitter/SheetMusic')
source_pdfs = list(sheet_music.glob('**/Carole King*Tapestry*.pdf'))

if source_pdfs:
    source_pdf = source_pdfs[0]
    relative_path = source_pdf.relative_to(sheet_music).as_posix()
    print(f'\n1. SOURCE PDF')
    print(f'   Location: {source_pdf}')
    print(f'   Relative: {relative_path}')
    print(f'   Size: {source_pdf.stat().st_size:,} bytes')
    print(f'   Exists: {source_pdf.exists()}')
else:
    print('\n1. SOURCE PDF: NOT FOUND')
    relative_path = None

# 2. Check DynamoDB
print(f'\n2. DYNAMODB RECORD')
if relative_path:
    # Query by scanning for this source PDF
    response = TABLE.scan()
    found_record = None
    for item in response.get('Items', []):
        source_uri = item.get('source_pdf_uri', '')
        if 'Carole King' in source_uri and 'Tapestry' in source_uri:
            found_record = item
            break

    if found_record:
        print(f'   Book ID: {found_record.get("book_id")}')
        print(f'   Source URI: {found_record.get("source_pdf_uri")}')
        print(f'   Local Path: {found_record.get("local_output_path")}')
        print(f'   S3 Path: {found_record.get("s3_output_path")}')
        print(f'   Processing Status: {found_record.get("processing_status", "N/A")}')

        book_id = found_record.get('book_id')
        local_path = found_record.get('local_output_path')
        s3_path = found_record.get('s3_output_path')
    else:
        print('   NOT FOUND in DynamoDB')
        book_id = None
        local_path = None
        s3_path = None
else:
    print('   Cannot query - no source PDF found')
    book_id = None
    local_path = None
    s3_path = None

# 3. Check local folder
print(f'\n3. LOCAL FOLDER')
if local_path:
    # Check both active and archive
    active_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')
    archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')

    local_folder = active_root / local_path.replace('/', '\\')
    if not local_folder.exists():
        local_folder = archive_root / local_path.replace('/', '\\')
        location = 'archive'
    else:
        location = 'active'

    if local_folder.exists():
        print(f'   Location: {local_folder}')
        print(f'   Storage: {location}')
        print(f'   Exists: True')

        # Count files
        pdf_files = list(local_folder.glob('*.pdf'))
        print(f'   PDF Files: {len(pdf_files)}')

        # Check for manifest
        manifest_path = local_folder / 'manifest.json'
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            print(f'   Manifest: YES')
            print(f'   Songs in manifest: {len(manifest.get("songs", []))}')
        else:
            print(f'   Manifest: NO')
            manifest = None
    else:
        print(f'   Location: {local_path}')
        print(f'   Exists: False')
        manifest = None
else:
    print('   Path unknown')
    manifest = None

# 4. Check S3
print(f'\n4. S3 FOLDER')
if s3_path:
    print(f'   Path: s3://{BUCKET}/{s3_path}')

    # List files
    try:
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET, Prefix=s3_path + '/')

        s3_files = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
                    })

        print(f'   Files: {len(s3_files)}')
        if s3_files:
            print(f'   First file: {s3_files[0]["key"]}')
            print(f'   Total size: {sum(f["size"] for f in s3_files):,} bytes')
    except Exception as e:
        print(f'   Error listing: {e}')
else:
    print('   Path unknown')

# 5. Check manifest on S3
print(f'\n5. MANIFEST (S3)')
if book_id:
    manifest_key = f'output/{book_id}/manifest.json'
    try:
        manifest_obj = s3.get_object(Bucket=BUCKET, Key=manifest_key)
        manifest_s3 = json.loads(manifest_obj['Body'].read())
        print(f'   Location: s3://{BUCKET}/{manifest_key}')
        print(f'   Exists: True')
        print(f'   Songs: {len(manifest_s3.get("songs", []))}')
        print(f'   Book Name: {manifest_s3.get("book_name", "N/A")}')

        # Show first few songs
        if manifest_s3.get('songs'):
            print(f'   Sample songs:')
            for song in manifest_s3['songs'][:3]:
                print(f'     - {song.get("title", "Untitled")}')
    except s3.exceptions.NoSuchKey:
        print(f'   Location: s3://{BUCKET}/{manifest_key}')
        print(f'   Exists: False')
    except Exception as e:
        print(f'   Error: {e}')
else:
    print('   Book ID unknown')

# 6. Check artifacts on S3
print(f'\n6. ARTIFACTS (S3)')
if book_id:
    artifacts_prefix = f'artifacts/{book_id}/'
    required_artifacts = [
        'toc_discovery.json',
        'toc_parse.json',
        'page_mapping.json',
        'verified_songs.json',
        'output_files.json'
    ]

    print(f'   Location: s3://{BUCKET}/{artifacts_prefix}')

    for artifact in required_artifacts:
        artifact_key = artifacts_prefix + artifact
        try:
            s3.head_object(Bucket=BUCKET, Key=artifact_key)
            print(f'   {artifact}: EXISTS')
        except s3.exceptions.ClientError:
            print(f'   {artifact}: MISSING')
else:
    print('   Book ID unknown')

print(f'\n{"="*80}')
print('END OF LINEAGE TRACE')
print(f'{"="*80}')
