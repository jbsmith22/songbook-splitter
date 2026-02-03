"""
Final provenance database with:
1. Manifests from S3
2. Song-by-song TOC matching
3. Proper completion logic
"""
import json
import boto3
import re

def normalize_title(title):
    """Normalize song title for matching"""
    return re.sub(r'[^a-z0-9]', '', title.lower())

def find_matching_file(toc_title, actual_files):
    """Try to find a matching file for a TOC entry"""
    normalized_toc = normalize_title(toc_title)

    for song_file in actual_files:
        filename = song_file['filename']
        normalized_filename = normalize_title(filename)

        # Check if TOC title is in filename
        if normalized_toc in normalized_filename:
            return filename

    return None

print('='*80)
print('FINALIZING PROVENANCE DATABASE')
print('='*80)

s3 = boto3.client('s3')
BUCKET = 'jsmith-output'

# Load database
print('\n1. Loading database...')
with open('data/analysis/complete_provenance_database.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f'   Loaded {len(data["songbooks"])} songbooks')

# Step 1: Load manifests from S3
print('\n2. Loading manifests from S3...')
manifests_found = 0
for i, book in enumerate(data['songbooks']):
    book_id = book['mapping']['book_id']

    if book_id == 'NONE':
        book['manifest'] = {'exists': False}
        continue

    try:
        obj = s3.get_object(Bucket=BUCKET, Key=f'output/{book_id}/manifest.json')
        manifest = json.loads(obj['Body'].read())

        book['manifest'] = {
            'location': f's3://{BUCKET}/output/{book_id}/manifest.json',
            'exists': True,
            'book_name': manifest.get('book_name'),
            'song_count': len(manifest.get('songs', [])),
            'songs': manifest.get('songs', [])
        }
        manifests_found += 1
    except:
        book['manifest'] = {'exists': False}

    if (i + 1) % 100 == 0:
        print(f'   Processed {i+1}/{len(data["songbooks"])}...')

print(f'   Found {manifests_found} manifests')

# Step 2: Song-by-song matching
print('\n3. Performing song-by-song TOC matching...')
complete_count = 0
incomplete_count = 0
missing_count = 0

for i, book in enumerate(data['songbooks']):
    toc_entries = book['toc']['entries']
    actual_songs = book['local']['songs']
    issues = []

    # Check for critical missing components
    if not book['source_pdf']['exists']:
        issues.append('SOURCE_PDF_MISSING')
    if not book['local']['exists']:
        issues.append('LOCAL_FOLDER_MISSING')
    if not book['dynamodb']:
        issues.append('NO_DYNAMODB_RECORD')
    if not book['manifest']['exists']:
        issues.append('MANIFEST_MISSING')

    # If critically missing, mark as MISSING
    if 'SOURCE_PDF_MISSING' in issues or 'LOCAL_FOLDER_MISSING' in issues:
        book['verification']['status'] = 'MISSING'
        book['verification']['issues'] = issues
        book['verification']['missing_toc_songs'] = []
        book['verification']['all_toc_songs_present'] = False
        missing_count += 1
        continue

    # Match each TOC song to actual files
    missing_toc_songs = []
    if len(toc_entries) > 0:
        for entry in toc_entries:
            toc_title = entry.get('title') or entry.get('song_title', '')
            if not toc_title:
                continue

            matching_file = find_matching_file(toc_title, actual_songs)
            if not matching_file:
                missing_toc_songs.append(toc_title)

        if missing_toc_songs:
            issues.append(f'MISSING_SONGS:{len(missing_toc_songs)}')

    # Check for page gaps
    if book['verification'].get('gap_count', 0) > 0:
        issues.append(f'PAGE_GAPS:{book["verification"]["gap_count"]}')

    # Check if songs missing from extraction list (informational only)
    if len(book['extraction'].get('missing_from_extraction', [])) > 0:
        issues.append(f'MISSING_FROM_EXTRACTION:{len(book["extraction"]["missing_from_extraction"])}')

    # Store results
    book['verification']['missing_toc_songs'] = missing_toc_songs
    book['verification']['all_toc_songs_present'] = len(missing_toc_songs) == 0
    book['verification']['issues'] = issues

    # Determine final status
    # Complete if: no missing TOC songs, has DynamoDB, has manifest, no gaps
    critical_issues = [i for i in issues if not i.startswith('MISSING_FROM_EXTRACTION')]

    if len(critical_issues) == 0:
        book['verification']['status'] = 'COMPLETE'
        complete_count += 1
    else:
        book['verification']['status'] = 'INCOMPLETE'
        incomplete_count += 1

    # Mark manifest as present if it exists
    if book['manifest']['exists']:
        book['local']['manifest_present'] = True

    if (i + 1) % 100 == 0:
        print(f'   Processed {i+1}/{len(data["songbooks"])}...')

# Update statistics
data['statistics']['complete'] = complete_count
data['statistics']['incomplete'] = incomplete_count
data['statistics']['missing_local'] = missing_count
data['statistics']['has_manifest'] = manifests_found

# Save
print('\n4. Saving finalized database...')
with open('data/analysis/complete_provenance_database.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, default=str)

print('\n' + '='*80)
print('FINALIZATION COMPLETE')
print('='*80)
print(f'Complete: {complete_count} ({complete_count/len(data["songbooks"])*100:.1f}%)')
print(f'Incomplete: {incomplete_count} ({incomplete_count/len(data["songbooks"])*100:.1f}%)')
print(f'Missing: {missing_count} ({missing_count/len(data["songbooks"])*100:.1f}%)')
print(f'Has manifest: {manifests_found}')
print('\nSaved: data/analysis/complete_provenance_database.json')
