"""
Generate v2 provenance data for the complete_provenance_viewer.

Scans S3 for existing v2 artifacts and Step Functions execution history
to accurately show which books have been processed.
"""
import json
import hashlib
import boto3
from pathlib import Path
from datetime import datetime

# Configuration
SHEETMUSIC_DIR = Path('SheetMusic')
INPUT_BUCKET = 'jsmith-input'
OUTPUT_BUCKET = 'jsmith-output'
BOOK_ID_PREFIX = 'v2-'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'

s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')


def get_v2_executions_map():
    """Get mapping of book_ids to source PDFs from Step Functions executions."""
    print("Fetching v2 executions from Step Functions...")

    book_id_map = {}  # book_id -> info

    for status in ['SUCCEEDED', 'RUNNING', 'FAILED']:
        try:
            paginator = sfn.get_paginator('list_executions')
            for page in paginator.paginate(
                stateMachineArn=STATE_MACHINE_ARN,
                statusFilter=status
            ):
                for ex in page.get('executions', []):
                    if not ex['name'].startswith('v2-'):
                        continue

                    try:
                        desc = sfn.describe_execution(executionArn=ex['executionArn'])
                        input_data = json.loads(desc.get('input', '{}'))
                        output = json.loads(desc.get('output', '{}'))

                        book_id = input_data.get('book_id')
                        source_uri = input_data.get('source_pdf_uri', '')

                        # Extract relative path from S3 URI
                        if source_uri.startswith(f's3://{INPUT_BUCKET}/'):
                            rel_path = source_uri.replace(f's3://{INPUT_BUCKET}/', '')
                        else:
                            rel_path = source_uri

                        # Get status from output
                        payload = output.get('Payload', {})
                        exec_status = payload.get('status', 'unknown')

                        if book_id and rel_path:
                            # Only keep the most recent execution for each book_id
                            if book_id not in book_id_map or exec_status == 'success':
                                book_id_map[book_id] = {
                                    'rel_path': rel_path,
                                    'artist': input_data.get('artist', ''),
                                    'book_name': input_data.get('book_name', ''),
                                    'execution_status': status,
                                    'internal_status': exec_status
                                }
                    except:
                        pass
        except:
            pass

    print(f"  Found {len(book_id_map)} v2 executions")
    return book_id_map


def get_existing_v2_artifacts():
    """Scan S3 for existing v2 artifact folders."""
    print("Scanning S3 for v2 artifacts...")

    v2_books = set()

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix='artifacts/v2-', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            # Extract book_id from prefix like "artifacts/v2-abc123/"
            book_id = prefix['Prefix'].replace('artifacts/', '').rstrip('/')
            v2_books.add(book_id)

    print(f"  Found {len(v2_books)} v2 artifact folders")
    return v2_books


def check_v2_artifacts(book_id: str) -> dict:
    """Check which v2 artifacts exist for a book."""
    artifacts = {
        'toc_discovery': False,
        'toc_parse': False,
        'page_analysis': False,
        'page_mapping': False,
        'verified_songs': False,
        'output_files': False,
    }

    artifact_details = {}

    try:
        prefix = f'artifacts/{book_id}/'
        response = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=prefix)

        for obj in response.get('Contents', []):
            key = obj['Key']
            filename = key.split('/')[-1]

            if filename == 'toc_discovery.json':
                artifacts['toc_discovery'] = True
                artifact_details['toc_discovery'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
            elif filename == 'toc_parse.json':
                artifacts['toc_parse'] = True
                artifact_details['toc_parse'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
            elif filename == 'page_analysis.json':
                artifacts['page_analysis'] = True
                artifact_details['page_analysis'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
            elif filename == 'page_mapping.json':
                artifacts['page_mapping'] = True
                artifact_details['page_mapping'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
            elif filename == 'verified_songs.json':
                artifacts['verified_songs'] = True
                artifact_details['verified_songs'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
            elif filename == 'output_files.json':
                artifacts['output_files'] = True
                artifact_details['output_files'] = {'size': obj['Size'], 'modified': obj['LastModified'].isoformat()}
    except:
        pass

    return {
        'has_artifacts': artifacts,
        'artifact_details': artifact_details
    }


def get_output_files_info(book_id: str) -> dict:
    """Get song count and details from output_files.json."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
        data = json.loads(obj['Body'].read())
        files = data.get('output_files', [])

        return {
            'song_count': len(files),
            'songs': [{'title': f.get('song_title'), 'pages': f.get('page_range')} for f in files],
            'total_size_bytes': sum(f.get('file_size_bytes', 0) for f in files)
        }
    except:
        return {'song_count': 0, 'songs': [], 'total_size_bytes': 0}


def get_page_mapping_info(book_id: str) -> dict:
    """Get page mapping confidence and details."""
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_mapping.json')
        data = json.loads(obj['Body'].read())

        return {
            'offset': data.get('offset', 0),
            'confidence': data.get('confidence', 0),
            'samples_verified': data.get('samples_verified', 0),
            'mapping_method': data.get('mapping_method', 'unknown')
        }
    except:
        return {'offset': 0, 'confidence': 0, 'samples_verified': 0, 'mapping_method': 'none'}


def get_toc_info(book_id: str) -> dict:
    """Get TOC song count from page_analysis.json or toc_parse.json."""
    try:
        # First try page_analysis.json (has toc_song_count)
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
        data = json.loads(obj['Body'].read())
        return {
            'toc_song_count': data.get('toc_song_count', 0),
            'detected_song_count': data.get('detected_song_count', 0),
            'matched_song_count': data.get('matched_song_count', 0)
        }
    except:
        pass

    try:
        # Fallback to toc_parse.json
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/toc_parse.json')
        data = json.loads(obj['Body'].read())
        entries = data.get('entries', [])
        return {
            'toc_song_count': len(entries),
            'detected_song_count': 0,
            'matched_song_count': 0
        }
    except:
        return {'toc_song_count': 0, 'detected_song_count': 0, 'matched_song_count': 0}


def scan_local_pdfs() -> dict:
    """Scan SheetMusic folder for all PDFs. Returns dict keyed by relative path."""
    print(f"Scanning {SHEETMUSIC_DIR} for PDFs...")
    pdfs = list(SHEETMUSIC_DIR.glob('**/*.pdf'))
    pdfs.extend(SHEETMUSIC_DIR.glob('**/*.PDF'))

    # Remove duplicates and build path map
    seen = set()
    path_map = {}
    for pdf in pdfs:
        key = str(pdf).lower()
        if key not in seen:
            seen.add(key)
            rel_path = str(pdf.relative_to(SHEETMUSIC_DIR)).replace('\\', '/')
            path_map[rel_path] = pdf

    print(f"  Found {len(path_map)} PDFs")
    return path_map


def generate_v2_provenance():
    """Generate v2 provenance data combining S3 artifacts and local files."""

    # Step 1: Get execution history to map book_ids to source files
    exec_map = get_v2_executions_map()

    # Step 2: Get existing v2 artifact folders
    artifact_book_ids = get_existing_v2_artifacts()

    # Step 3: Scan local PDFs
    local_pdfs = scan_local_pdfs()

    # Step 4: Build provenance for each local PDF
    songbooks = []
    stats = {
        'total': len(local_pdfs),
        'complete': 0,
        'incomplete': 0,
        'missing': 0,
        'has_artifacts': 0,
        'has_output_files': 0,
        'has_page_mapping': 0
    }

    # Create reverse map: rel_path -> book_id (from executions)
    # Prefer book_ids with -2 suffix (newer v2 format) over older ones
    path_to_book_id = {}
    for book_id, info in exec_map.items():
        rel_path = info['rel_path']
        existing = path_to_book_id.get(rel_path)
        # Prefer book_ids ending with -2 (correct v2 format)
        if existing is None or book_id.endswith('-2'):
            path_to_book_id[rel_path] = book_id

    print(f"\nProcessing {len(local_pdfs)} local books...")

    for i, (rel_path, pdf) in enumerate(sorted(local_pdfs.items())):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(local_pdfs)}...")

        # Find book_id for this file
        book_id = path_to_book_id.get(rel_path)

        # Parse path info
        parts = Path(rel_path).parts
        if len(parts) >= 2:
            artist = parts[0]
            filename = Path(rel_path).stem
            if ' - ' in filename:
                book_name = filename.split(' - ', 1)[1]
            else:
                book_name = filename
        else:
            artist = 'Unknown'
            book_name = Path(rel_path).stem

        # Check artifacts if we have a book_id
        has_artifacts = {
            'toc_discovery': False,
            'toc_parse': False,
            'page_analysis': False,
            'page_mapping': False,
            'verified_songs': False,
            'output_files': False,
        }
        artifact_details = {}
        output_info = {'song_count': 0, 'songs': [], 'total_size_bytes': 0}
        mapping_info = {'offset': 0, 'confidence': 0, 'samples_verified': 0, 'mapping_method': 'none'}
        toc_info = {'toc_song_count': 0, 'detected_song_count': 0, 'matched_song_count': 0}

        if book_id and book_id in artifact_book_ids:
            artifacts_data = check_v2_artifacts(book_id)
            has_artifacts = artifacts_data['has_artifacts']
            artifact_details = artifacts_data['artifact_details']

            if has_artifacts['output_files']:
                output_info = get_output_files_info(book_id)
                stats['has_output_files'] += 1

            if has_artifacts['page_mapping']:
                mapping_info = get_page_mapping_info(book_id)
                stats['has_page_mapping'] += 1

            if has_artifacts['page_analysis'] or has_artifacts['toc_parse']:
                toc_info = get_toc_info(book_id)

        # Determine status
        has_any_artifacts = any(has_artifacts.values())
        is_complete = (has_artifacts['output_files'] and
                      has_artifacts['page_mapping'] and
                      has_artifacts['verified_songs'])

        if is_complete:
            stats['complete'] += 1
            status = 'COMPLETE'
        elif has_any_artifacts:
            stats['incomplete'] += 1
            status = 'INCOMPLETE'
            stats['has_artifacts'] += 1
        else:
            stats['missing'] += 1
            status = 'MISSING'

        if has_any_artifacts:
            stats['has_artifacts'] += 1

        # Build issues list
        issues = []
        if not book_id:
            issues.append('Not yet processed')
        else:
            if not has_artifacts['toc_discovery']:
                issues.append('No TOC discovery')
            if not has_artifacts['toc_parse']:
                issues.append('No TOC parse')
            if not has_artifacts['page_analysis']:
                issues.append('No page analysis')
            if not has_artifacts['page_mapping']:
                issues.append('No page mapping')
            if not has_artifacts['output_files']:
                issues.append('No output files')
            if not has_artifacts['verified_songs']:
                issues.append('No verified songs')

        # Get execution status if available
        exec_info = exec_map.get(book_id, {})

        songbook = {
            'source_pdf': {
                'path': rel_path,
                'exists': True,
                'size_mb': round(pdf.stat().st_size / (1024 * 1024), 2)
            },
            'mapping': {
                'book_id': book_id or 'NOT_PROCESSED',
                'mapping_status': 'V2_PROCESSED' if is_complete else ('V2_PARTIAL' if has_any_artifacts else 'V2_PENDING'),
                'local_folder': str(pdf.parent.relative_to(SHEETMUSIC_DIR)).replace('\\', '/'),
                's3_folder': f'artifacts/{book_id}/' if book_id else None
            },
            'verification': {
                'status': status,
                'toc_songs': toc_info['toc_song_count'],
                'detected_songs': toc_info['detected_song_count'],
                'matched_songs': toc_info['matched_song_count'],
                'actual_songs': output_info['song_count'],
                'issues': issues
            },
            'execution': {
                'status': exec_info.get('execution_status', 'none'),
                'internal_status': exec_info.get('internal_status', 'none')
            },
            'artifacts': has_artifacts,
            'artifact_details': artifact_details,
            'page_mapping': mapping_info,
            'output_info': output_info,
            'toc': {
                'has_toc': has_artifacts['toc_parse']
            },
            'images': {
                'has_cached_images': False
            }
        }

        songbooks.append(songbook)

    # Sort: complete first, then incomplete, then missing
    status_order = {'COMPLETE': 0, 'INCOMPLETE': 1, 'MISSING': 2}
    songbooks.sort(key=lambda x: (status_order.get(x['verification']['status'], 3), x['source_pdf']['path']))

    result = {
        'generated_at': datetime.now().isoformat(),
        'version': 'v2',
        'statistics': stats,
        'songbooks': songbooks
    }

    return result


def main():
    print("Generating v2 provenance data...")
    print()

    data = generate_v2_provenance()

    # Save to file
    output_file = Path('data/analysis/v2_provenance_database.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    # Also save as JS for the viewer (avoids CORS issues with file:// URLs)
    js_file = Path('data/analysis/v2_provenance_data.js')
    with open(js_file, 'w') as f:
        f.write('// Generated v2 provenance data\n')
        f.write('const V2_PROVENANCE_DATA = ')
        json.dump(data, f)
        f.write(';')

    print()
    print("=" * 60)
    print("V2 PROVENANCE SUMMARY")
    print("=" * 60)
    print(f"Total books:       {data['statistics']['total']}")
    print(f"Complete:          {data['statistics']['complete']}")
    print(f"Incomplete:        {data['statistics']['incomplete']}")
    print(f"Missing:           {data['statistics']['missing']}")
    print(f"Has any artifacts: {data['statistics']['has_artifacts']}")
    print(f"Has output files:  {data['statistics']['has_output_files']}")
    print(f"Has page mapping:  {data['statistics']['has_page_mapping']}")
    print()
    print(f"Saved to: {output_file}")
    print(f"JS data:  {js_file}")
    print(f"\nViewer:   web/viewers/v2_provenance_viewer.html")

    # Show complete books
    complete = [b for b in data['songbooks'] if b['verification']['status'] == 'COMPLETE']
    if complete:
        print()
        print(f"COMPLETE BOOKS ({len(complete)}):")
        for book in complete[:30]:
            print(f"  {book['source_pdf']['path']} ({book['output_info']['song_count']} songs)")
        if len(complete) > 30:
            print(f"  ... and {len(complete) - 30} more")


if __name__ == '__main__':
    main()
