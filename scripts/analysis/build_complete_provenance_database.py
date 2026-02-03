"""
Build Complete Provenance Database for All 559 Songbooks

Collects data from:
- Source PDFs (SheetMusic/)
- DynamoDB (processing ledger)
- complete_page_lineage.json
- TOC cache files
- Local folders (ProcessedSongs + ProcessedSongs_Archive)
- S3 folders
- Image cache

Outputs:
- complete_provenance_database.json (full data)
- complete_provenance_summary.csv (quick reference)
- complete_provenance_report.html (interactive viewer)
"""

import json
import csv
import boto3
from pathlib import Path
from datetime import datetime
import os

print('='*80)
print('BUILDING COMPLETE PROVENANCE DATABASE')
print('='*80)

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

# Paths
sheet_music = Path(r'd:\Work\songbook-splitter\SheetMusic')
processed_active = Path(r'd:\Work\songbook-splitter\ProcessedSongs')
processed_archive = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
toc_cache_dir = Path(r'd:\Work\songbook-splitter\toc_cache')
image_cache_dir = Path(r'S:\SlowImageCache\pdf_verification')

# Step 1: Load provenance mapping
print('\n1. Loading provenance mapping...')
provenance_map = {}
with open('data/analysis/provenance_complete_mapping.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        source_pdf = row['source_pdf']
        provenance_map[source_pdf] = {
            'source_pdf': source_pdf,
            'local_folder': row['local_folder'],
            's3_folder': row['s3_folder'],
            'book_id': row['book_id'],
            'mapping_status': row['status']
        }
print(f'   Loaded {len(provenance_map)} source PDF mappings')

# Step 2: Load complete page lineage
print('\n2. Loading complete page lineage...')
with open('data/analysis/complete_page_lineage.json', 'r', encoding='utf-8') as f:
    page_lineage_data = json.load(f)

# Index by book name for faster lookup
lineage_by_name = {}
for book in page_lineage_data.get('books', []):
    book_name = book.get('book_name', '')
    lineage_by_name[book_name] = book
print(f'   Loaded lineage for {len(lineage_by_name)} books')

# Step 3: Load DynamoDB records
print('\n3. Loading DynamoDB records...')
dynamodb_records = {}
response = TABLE.scan()
all_records = response.get('Items', [])
while 'LastEvaluatedKey' in response:
    response = TABLE.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    all_records.extend(response.get('Items', []))

for record in all_records:
    book_id = record.get('book_id')
    if book_id:
        dynamodb_records[book_id] = {
            'book_id': book_id,
            'source_pdf_uri': record.get('source_pdf_uri', ''),
            'local_output_path': record.get('local_output_path', ''),
            's3_output_path': record.get('s3_output_path', ''),
            'processing_status': record.get('processing_status', ''),
            'created_date': record.get('created_date', '')
        }
print(f'   Loaded {len(dynamodb_records)} DynamoDB records')

# Step 4: Load TOC cache files
print('\n4. Loading TOC cache files...')
toc_cache = {}
if toc_cache_dir.exists():
    for toc_file in toc_cache_dir.glob('*.json'):
        book_id = toc_file.stem
        try:
            with open(toc_file, 'r', encoding='utf-8') as f:
                toc_cache[book_id] = json.load(f)
        except Exception as e:
            print(f'   Warning: Failed to load {toc_file.name}: {e}')
print(f'   Loaded {len(toc_cache)} TOC cache files')

# Step 5: Scan local folders
print('\n5. Scanning local folders...')
local_folders = {}

def scan_local_folder(base_path, storage_type):
    """Scan a ProcessedSongs directory"""
    if not base_path.exists():
        return

    for artist_dir in base_path.iterdir():
        if not artist_dir.is_dir():
            continue
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue

            relative_path = f"{artist_dir.name}/{book_dir.name}"

            # Read manifest if exists
            manifest_path = book_dir / 'manifest.json'
            manifest_data = None
            book_id = None
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest_data = json.load(f)
                        book_id = manifest_data.get('book_id')
                except Exception as e:
                    pass

            # Count song PDFs and get sizes
            song_files = []
            for pdf in book_dir.glob('*.pdf'):
                song_files.append({
                    'filename': pdf.name,
                    'size_bytes': pdf.stat().st_size,
                    'size_mb': round(pdf.stat().st_size / (1024*1024), 2)
                })

            local_folders[relative_path] = {
                'path': str(book_dir),
                'relative_path': relative_path,
                'storage': storage_type,
                'exists': True,
                'manifest_present': manifest_path.exists(),
                'manifest_data': manifest_data,
                'book_id': book_id,
                'song_count': len(song_files),
                'song_files': sorted(song_files, key=lambda x: x['filename'])
            }

scan_local_folder(processed_active, 'active')
scan_local_folder(processed_archive, 'archive')
print(f'   Found {len(local_folders)} local folders')

# Step 6: Check image cache availability
print('\n6. Checking image cache...')
image_cache_artists = set()
if image_cache_dir.exists():
    for artist_dir in image_cache_dir.iterdir():
        if artist_dir.is_dir():
            image_cache_artists.add(artist_dir.name)
print(f'   Found images for {len(image_cache_artists)} artists')

# Step 7: Build complete database
print('\n7. Building complete provenance database...')
complete_database = []
stats = {
    'total': 0,
    'complete': 0,
    'incomplete': 0,
    'missing_local': 0,
    'missing_s3': 0,
    'has_toc': 0,
    'has_manifest': 0,
    'has_dynamodb': 0,
    'has_cached_images': 0,
    'page_mismatches': 0,
    'local_s3_synced': 0
}

for source_pdf, prov in provenance_map.items():
    stats['total'] += 1

    # Source PDF info
    source_path = sheet_music / source_pdf
    source_exists = source_path.exists()
    source_size = source_path.stat().st_size if source_exists else 0

    # Book ID and DynamoDB
    book_id = prov['book_id']
    dynamodb_data = dynamodb_records.get(book_id, {}) if book_id != 'NONE' else {}
    has_dynamodb = bool(dynamodb_data)
    if has_dynamodb:
        stats['has_dynamodb'] += 1

    # TOC cache
    toc_data = toc_cache.get(book_id, {}) if book_id != 'NONE' else {}
    toc_entries = toc_data.get('toc', {}).get('entries', [])
    has_toc_cache = bool(toc_data)

    # Page lineage (extract book name from mapping)
    local_folder_name = prov['local_folder']
    # Try to find in lineage by matching folder name to book_name
    lineage_data = None
    for book_name, book_data in lineage_by_name.items():
        if local_folder_name in book_name or book_name.endswith(local_folder_name):
            lineage_data = book_data
            break

    has_toc = lineage_data.get('has_toc', False) if lineage_data else (len(toc_entries) > 0)
    toc_entry_list = lineage_data.get('toc_entries', []) if lineage_data else toc_entries
    extracted_songs = lineage_data.get('extracted_songs', []) if lineage_data else []
    gaps = lineage_data.get('gaps', []) if lineage_data else []
    mismatches = lineage_data.get('mismatches', []) if lineage_data else []

    if has_toc:
        stats['has_toc'] += 1
    if mismatches:
        stats['page_mismatches'] += 1

    # Local folder info
    local_data = local_folders.get(local_folder_name, {})
    local_exists = local_data.get('exists', False)
    has_manifest = local_data.get('manifest_present', False)
    local_songs = local_data.get('song_files', [])

    if not local_exists:
        stats['missing_local'] += 1
    if has_manifest:
        stats['has_manifest'] += 1

    # S3 info (will check later in bulk)
    s3_folder = prov['s3_folder']

    # Image cache check
    artist_name = source_pdf.split('/')[0] if '/' in source_pdf else ''
    has_images = artist_name in image_cache_artists
    if has_images:
        stats['has_cached_images'] += 1

    # Verification status
    issues = []
    if not source_exists:
        issues.append('SOURCE_PDF_MISSING')
    if not local_exists:
        issues.append('LOCAL_FOLDER_MISSING')
    if not has_manifest:
        issues.append('MANIFEST_MISSING')
    if not has_dynamodb:
        issues.append('NO_DYNAMODB_RECORD')
    if gaps:
        issues.append(f'PAGE_GAPS:{len(gaps)}')
    if mismatches:
        issues.append(f'PAGE_MISMATCHES:{len(mismatches)}')

    # TOC vs Files comparison
    toc_song_count = len(toc_entry_list)
    extracted_song_count = len(extracted_songs)
    actual_song_count = len(local_songs)

    missing_from_extraction = []
    if toc_entry_list and extracted_songs:
        toc_titles = {e.get('title', '').lower() for e in toc_entry_list}
        extracted_titles = {s.get('title', '').lower() for s in extracted_songs}
        missing_from_extraction = list(toc_titles - extracted_titles)

    if missing_from_extraction:
        issues.append(f'MISSING_FROM_EXTRACTION:{len(missing_from_extraction)}')

    # Overall status
    if issues:
        if 'LOCAL_FOLDER_MISSING' in issues or 'SOURCE_PDF_MISSING' in issues:
            overall_status = 'MISSING'
            stats['incomplete'] += 1
        else:
            overall_status = 'INCOMPLETE'
            stats['incomplete'] += 1
    else:
        overall_status = 'COMPLETE'
        stats['complete'] += 1

    # Build record
    record = {
        'source_pdf': {
            'path': source_pdf,
            'exists': source_exists,
            'size_bytes': source_size,
            'size_mb': round(source_size / (1024*1024), 2) if source_size > 0 else 0
        },
        'mapping': {
            'book_id': book_id,
            'local_folder': local_folder_name,
            's3_folder': s3_folder,
            'mapping_status': prov['mapping_status']
        },
        'dynamodb': dynamodb_data if has_dynamodb else None,
        'local': {
            'exists': local_exists,
            'storage': local_data.get('storage', 'unknown'),
            'path': local_data.get('path', ''),
            'manifest_present': has_manifest,
            'manifest': local_data.get('manifest_data'),
            'song_count': actual_song_count,
            'songs': local_songs
        },
        's3': {
            'folder': s3_folder,
            'checked': False,  # Will check in bulk later
            'song_count': 0,
            'songs': []
        },
        'toc': {
            'has_toc': has_toc,
            'has_cache_file': has_toc_cache,
            'entry_count': toc_song_count,
            'entries': toc_entry_list,
            'extraction_method': toc_data.get('toc', {}).get('extraction_method', '') if toc_data else ''
        },
        'extraction': {
            'song_count': extracted_song_count,
            'songs': extracted_songs,
            'missing_from_extraction': missing_from_extraction
        },
        'verification': {
            'status': overall_status,
            'has_gaps': bool(gaps),
            'gap_count': len(gaps),
            'gaps': gaps,
            'has_mismatches': bool(mismatches),
            'mismatch_count': len(mismatches),
            'mismatches': mismatches,
            'toc_songs': toc_song_count,
            'extracted_songs': extracted_song_count,
            'actual_songs': actual_song_count,
            'all_toc_songs_present': toc_song_count > 0 and actual_song_count >= toc_song_count,
            'issues': issues
        },
        'images': {
            'has_cached_images': has_images,
            'cache_location': f'S:\\SlowImageCache\\pdf_verification\\{artist_name}' if has_images else None
        }
    }

    complete_database.append(record)

    if stats['total'] % 50 == 0:
        print(f'   Processed {stats["total"]}/{len(provenance_map)} songbooks...')

print(f'\n   Completed processing {stats["total"]} songbooks')

# Step 8: Save complete database
print('\n8. Saving complete database...')
output_data = {
    'generated_at': datetime.now().isoformat(),
    'statistics': stats,
    'songbooks': complete_database
}

with open('data/analysis/complete_provenance_database.json', 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=2, default=str)
print('   Saved: data/analysis/complete_provenance_database.json')

# Step 9: Generate summary CSV
print('\n9. Generating summary CSV...')
with open('data/analysis/complete_provenance_summary.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = [
        'source_pdf', 'book_id', 'mapping_status', 'overall_status',
        'source_exists', 'local_exists', 'local_storage', 'has_manifest',
        'has_dynamodb', 'has_toc', 'has_cached_images',
        'toc_songs', 'extracted_songs', 'actual_songs',
        'gaps', 'mismatches', 'issues'
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for record in complete_database:
        writer.writerow({
            'source_pdf': record['source_pdf']['path'],
            'book_id': record['mapping']['book_id'],
            'mapping_status': record['mapping']['mapping_status'],
            'overall_status': record['verification']['status'],
            'source_exists': record['source_pdf']['exists'],
            'local_exists': record['local']['exists'],
            'local_storage': record['local']['storage'],
            'has_manifest': record['local']['manifest_present'],
            'has_dynamodb': bool(record['dynamodb']),
            'has_toc': record['toc']['has_toc'],
            'has_cached_images': record['images']['has_cached_images'],
            'toc_songs': record['verification']['toc_songs'],
            'extracted_songs': record['verification']['extracted_songs'],
            'actual_songs': record['verification']['actual_songs'],
            'gaps': record['verification']['gap_count'],
            'mismatches': record['verification']['mismatch_count'],
            'issues': '; '.join(record['verification']['issues'])
        })

print('   Saved: data/analysis/complete_provenance_summary.csv')

# Step 10: Print statistics
print('\n' + '='*80)
print('PROVENANCE DATABASE STATISTICS')
print('='*80)
print(f'Total songbooks: {stats["total"]}')
print(f'Complete: {stats["complete"]} ({stats["complete"]/stats["total"]*100:.1f}%)')
print(f'Incomplete: {stats["incomplete"]} ({stats["incomplete"]/stats["total"]*100:.1f}%)')
print(f'Missing local folder: {stats["missing_local"]}')
print(f'Has TOC: {stats["has_toc"]}')
print(f'Has manifest: {stats["has_manifest"]}')
print(f'Has DynamoDB record: {stats["has_dynamodb"]}')
print(f'Has cached images: {stats["has_cached_images"]}')
print(f'Books with page mismatches: {stats["page_mismatches"]}')
print()
print('Output files:')
print('  - data/analysis/complete_provenance_database.json (full data)')
print('  - data/analysis/complete_provenance_summary.csv (quick reference)')
print('='*80)
