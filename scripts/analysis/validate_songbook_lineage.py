"""
Comprehensive validation of songbook data across S3, DynamoDB, and local filesystem.
Maps lineage and prepares for reconciliation with local as source of truth.
"""
import json
import boto3
import os
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

S3_BUCKET = 'jsmith-output'
DYNAMODB_TABLE = 'jsmith-processing-ledger'
LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

class SongbookValidator:
    def __init__(self):
        self.s3_folders = {}  # path -> metadata
        self.dynamodb_records = {}  # book_id -> record
        self.local_folders = {}  # path -> metadata
        self.manifests = {}  # book_id -> manifest data
        self.book_id_to_s3_path = {}  # Reverse mapping
        self.duplicates = defaultdict(list)  # original_path -> [book_ids]

    def scan_local_structure(self):
        """Scan local ProcessedSongs directory (source of truth)"""
        print("\n=== Scanning Local Structure (Source of Truth) ===")

        if not LOCAL_ROOT.exists():
            print(f"WARNING: Local root {LOCAL_ROOT} does not exist!")
            return

        for artist_dir in sorted(LOCAL_ROOT.iterdir()):
            if not artist_dir.is_dir():
                continue

            artist = artist_dir.name

            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue

                album = album_dir.name
                songs = list(album_dir.glob('*.pdf'))

                key = f"{artist}/{album}"
                self.local_folders[key] = {
                    'artist': artist,
                    'album': album,
                    'song_count': len(songs),
                    'path': str(album_dir)
                }

        print(f"Found {len(self.local_folders)} local album folders")

    def scan_s3_structure(self):
        """Scan S3 bucket for song folders (excluding artifacts/output)"""
        print("\n=== Scanning S3 Structure ===")

        paginator = s3.get_paginator('list_objects_v2')

        # Track folders by counting files
        folder_files = defaultdict(list)

        for page in paginator.paginate(Bucket=S3_BUCKET):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']

                # Skip metadata folders
                if key.startswith('artifacts/') or key.startswith('output/'):
                    continue

                # Only process PDF files
                if not key.endswith('.pdf'):
                    continue

                # Extract artist/album from path
                parts = key.split('/')
                if len(parts) >= 3:
                    artist = parts[0]
                    album = parts[1]
                    filename = parts[-1]

                    folder_key = f"{artist}/{album}"
                    folder_files[folder_key].append({
                        'filename': filename,
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat()
                    })

        # Build folder metadata
        for folder_key, files in folder_files.items():
            artist, album = folder_key.split('/', 1)
            self.s3_folders[folder_key] = {
                'artist': artist,
                'album': album,
                'song_count': len(files),
                'total_size': sum(f['size'] for f in files),
                'files': files
            }

        print(f"Found {len(self.s3_folders)} S3 album folders")

    def scan_dynamodb(self):
        """Scan DynamoDB for all processing records"""
        print("\n=== Scanning DynamoDB ===")

        paginator = dynamodb.get_paginator('scan')

        for page in paginator.paginate(TableName=DYNAMODB_TABLE):
            for item in page['Items']:
                book_id = item['book_id']['S']

                record = {
                    'book_id': book_id,
                    'artist': item.get('artist', {}).get('S', ''),
                    'book_name': item.get('book_name', {}).get('S', ''),
                    'source_pdf_uri': item.get('source_pdf_uri', {}).get('S', ''),
                    'manifest_uri': item.get('manifest_uri', {}).get('S', ''),
                    'status': item.get('status', {}).get('S', ''),
                    'songs_extracted': int(item.get('songs_extracted', {}).get('N', 0)),
                    'processing_timestamp': int(item.get('processing_timestamp', {}).get('N', 0)),
                    'last_updated': item.get('last_updated', {}).get('S', ''),
                    'cost_usd': float(item.get('cost_usd', {}).get('N', 0))
                }

                self.dynamodb_records[book_id] = record

                # Track duplicates by source PDF
                if record['source_pdf_uri']:
                    self.duplicates[record['source_pdf_uri']].append(book_id)

        print(f"Found {len(self.dynamodb_records)} DynamoDB records")
        print(f"Found {len([k for k, v in self.duplicates.items() if len(v) > 1])} source PDFs with multiple runs")

    def load_manifests(self):
        """Load manifest files from S3 output/ folder"""
        print("\n=== Loading Manifests ===")

        paginator = s3.get_paginator('list_objects_v2')
        manifest_count = 0

        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix='output/'):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']
                if key.endswith('manifest.json'):
                    # Extract book_id from path: output/{book_id}/manifest.json
                    book_id = key.split('/')[1]

                    try:
                        response = s3.get_object(Bucket=S3_BUCKET, Key=key)
                        manifest_data = json.loads(response['Body'].read())
                        self.manifests[book_id] = manifest_data
                        manifest_count += 1
                    except Exception as e:
                        print(f"  Error loading manifest {key}: {e}")

        print(f"Loaded {manifest_count} manifests")

    def build_book_id_to_s3_mapping(self):
        """Build reverse mapping from book_id to current S3 path using manifests"""
        print("\n=== Building book_id -> S3 Path Mapping ===")

        for book_id, manifest in self.manifests.items():
            # Try to determine S3 path from manifest
            artist = manifest.get('artist', '')
            book_name = manifest.get('book_name', '')

            # Check if manifest has output info
            if 'output' in manifest and 'output_directory' in manifest['output']:
                output_dir = manifest['output']['output_directory']
                # Parse S3 path like: s3://bucket/Artist/Album/
                if output_dir.startswith('s3://'):
                    parts = output_dir.replace('s3://' + S3_BUCKET + '/', '').strip('/').split('/')
                    if len(parts) >= 2:
                        folder_key = f"{parts[0]}/{parts[1]}"
                        self.book_id_to_s3_path[book_id] = folder_key

            # Also try DynamoDB source path
            if book_id not in self.book_id_to_s3_path and book_id in self.dynamodb_records:
                record = self.dynamodb_records[book_id]
                # Try to infer from artist/book_name
                # This may not match current S3 if renamed!
                folder_key = f"{record['artist']}/{record['book_name']}"
                self.book_id_to_s3_path[book_id] = folder_key

        print(f"Mapped {len(self.book_id_to_s3_path)} book_ids to S3 paths")

    def validate_cross_references(self):
        """Cross-reference S3, DynamoDB, and local to find mismatches"""
        print("\n=== Cross-Reference Validation ===")

        results = {
            's3_only': [],  # In S3 but not in local or DynamoDB
            'local_only': [],  # In local but not in S3
            'no_dynamodb': [],  # In S3/local but no DynamoDB record
            'matched': [],  # Fully matched across all three
            'duplicates': [],  # Multiple DynamoDB records for same content
            'renamed': [],  # Different names between sources
        }

        # Check each S3 folder
        for s3_path, s3_data in self.s3_folders.items():
            # Find corresponding book_id(s)
            matching_book_ids = [bid for bid, path in self.book_id_to_s3_path.items()
                                if path == s3_path]

            # Check if in local
            in_local = s3_path in self.local_folders

            # Check if has DynamoDB record
            has_dynamodb = len(matching_book_ids) > 0

            if in_local and has_dynamodb:
                results['matched'].append({
                    's3_path': s3_path,
                    'local_path': s3_path,
                    'book_ids': matching_book_ids,
                    's3_songs': s3_data['song_count'],
                    'local_songs': self.local_folders[s3_path]['song_count']
                })
            elif not in_local:
                results['s3_only'].append({
                    's3_path': s3_path,
                    'book_ids': matching_book_ids,
                    'song_count': s3_data['song_count']
                })
            elif not has_dynamodb:
                results['no_dynamodb'].append({
                    's3_path': s3_path,
                    'local_path': s3_path,
                    's3_songs': s3_data['song_count'],
                    'local_songs': self.local_folders[s3_path]['song_count']
                })

        # Check each local folder
        for local_path, local_data in self.local_folders.items():
            if local_path not in self.s3_folders:
                results['local_only'].append({
                    'local_path': local_path,
                    'song_count': local_data['song_count']
                })

        # Find duplicates (same source processed multiple times)
        for source_pdf, book_ids in self.duplicates.items():
            if len(book_ids) > 1:
                # Sort by processing timestamp to find latest
                sorted_ids = sorted(book_ids,
                                   key=lambda bid: self.dynamodb_records[bid]['processing_timestamp'],
                                   reverse=True)

                results['duplicates'].append({
                    'source_pdf': source_pdf,
                    'book_ids': sorted_ids,
                    'latest_book_id': sorted_ids[0],
                    'count': len(book_ids),
                    'timestamps': [self.dynamodb_records[bid]['processing_timestamp'] for bid in sorted_ids]
                })

        return results

    def generate_report(self, results):
        """Generate comprehensive validation report"""
        report = []
        report.append("=" * 80)
        report.append("SONGBOOK DATA VALIDATION REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)

        # Summary statistics
        report.append("\n## SUMMARY STATISTICS")
        report.append(f"Local folders (SOURCE OF TRUTH): {len(self.local_folders)}")
        report.append(f"S3 folders: {len(self.s3_folders)}")
        report.append(f"DynamoDB records: {len(self.dynamodb_records)}")
        report.append(f"Manifests loaded: {len(self.manifests)}")

        # Matched records
        report.append(f"\n## MATCHED RECORDS: {len(results['matched'])}")
        report.append("Folders that exist in all three locations with proper lineage")
        if results['matched']:
            report.append("\nSample matched records:")
            for item in results['matched'][:5]:
                report.append(f"  ✓ {item['s3_path']}")
                report.append(f"    Book IDs: {', '.join(item['book_ids'])}")
                report.append(f"    Songs: S3={item['s3_songs']}, Local={item['local_songs']}")

        # S3 only (not in local)
        report.append(f"\n## S3 ONLY (Not in Local): {len(results['s3_only'])}")
        report.append("Folders in S3 that don't exist in local ProcessedSongs")
        report.append("ACTION: These may need to be deleted or moved to local")
        if results['s3_only']:
            for item in results['s3_only'][:20]:
                report.append(f"  ⚠️  {item['s3_path']} ({item['song_count']} songs)")
                if item['book_ids']:
                    report.append(f"      Book IDs: {', '.join(item['book_ids'])}")

        # Local only (not in S3)
        report.append(f"\n## LOCAL ONLY (Not in S3): {len(results['local_only'])}")
        report.append("Folders in local that don't exist in S3")
        report.append("ACTION: These need to be uploaded to S3")
        if results['local_only']:
            for item in results['local_only'][:20]:
                report.append(f"  📁 {item['local_path']} ({item['song_count']} songs)")

        # No DynamoDB record
        report.append(f"\n## NO DYNAMODB RECORD: {len(results['no_dynamodb'])}")
        report.append("Folders that exist but have no processing history")
        report.append("ACTION: These may be manually created or need metadata recreation")
        if results['no_dynamodb']:
            for item in results['no_dynamodb'][:20]:
                report.append(f"  ❓ {item['s3_path']}")

        # Duplicates
        report.append(f"\n## DUPLICATE PROCESSING RUNS: {len(results['duplicates'])}")
        report.append("Source PDFs that were processed multiple times")
        report.append("ACTION: Keep latest, track lineage of others")
        if results['duplicates']:
            for item in results['duplicates'][:20]:
                report.append(f"  🔄 {item['source_pdf']}")
                report.append(f"      Runs: {item['count']}, Latest: {item['latest_book_id']}")
                report.append(f"      Book IDs: {', '.join(item['book_ids'])}")

        # Recommendations
        report.append("\n" + "=" * 80)
        report.append("## RECOMMENDATIONS FOR RECONCILIATION")
        report.append("=" * 80)
        report.append("\n1. SYNC S3 TO LOCAL (Source of Truth)")
        report.append(f"   - Upload {len(results['local_only'])} local folders to S3")
        report.append(f"   - Review {len(results['s3_only'])} S3-only folders (delete or move to local)")

        report.append("\n2. UPDATE DYNAMODB RECORDS")
        report.append("   - Create/update records to match current folder names")
        report.append("   - Preserve lineage with 'previous_book_ids' or 'renamed_from' fields")

        report.append("\n3. HANDLE DUPLICATES")
        report.append(f"   - {len(results['duplicates'])} source PDFs with multiple runs")
        report.append("   - Keep latest processing run")
        report.append("   - Archive older book_ids but preserve in lineage")

        report.append("\n4. UPDATE MANIFESTS")
        report.append("   - Regenerate manifests with current folder paths")
        report.append("   - Add lineage tracking (original_source, renamed_from, etc.)")

        return "\n".join(report)

def main():
    print("=" * 80)
    print("SONGBOOK LINEAGE VALIDATION")
    print("=" * 80)

    validator = SongbookValidator()

    # Step 1: Scan all sources
    validator.scan_local_structure()
    validator.scan_s3_structure()
    validator.scan_dynamodb()
    validator.load_manifests()

    # Step 2: Build mappings
    validator.build_book_id_to_s3_mapping()

    # Step 3: Validate and cross-reference
    results = validator.validate_cross_references()

    # Step 4: Generate report
    report = validator.generate_report(results)

    # Step 5: Save report
    output_file = 'data/analysis/songbook_validation_report.txt'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✓ Report saved to {output_file}")
    print("\n" + report)

    # Step 6: Save detailed JSON
    json_file = 'data/analysis/songbook_validation_data.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'local_folders': len(validator.local_folders),
                's3_folders': len(validator.s3_folders),
                'dynamodb_records': len(validator.dynamodb_records),
                'manifests': len(validator.manifests)
            },
            'results': results,
            'book_id_mapping': validator.book_id_to_s3_path,
            'duplicates': dict(validator.duplicates)
        }, f, indent=2, default=str)

    print(f"✓ Detailed data saved to {json_file}")

if __name__ == '__main__':
    main()
