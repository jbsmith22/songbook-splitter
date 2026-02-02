"""
Comprehensive validation with SMART FUZZY MATCHING
Uses mapping files and normalization rules to find matches
"""
import json
import boto3
import os
import csv
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

S3_BUCKET = 'jsmith-output'
DYNAMODB_TABLE = 'jsmith-processing-ledger'
LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

def normalize_path(path):
    """Normalize path for fuzzy matching"""
    normalized = path.lower()
    # Replace brackets and parenthesis with underscores
    normalized = re.sub(r'[\[\]\(\)]', '_', normalized)
    # Remove multiple underscores
    normalized = re.sub(r'_+', '_', normalized)
    # Remove trailing/leading underscores
    normalized = normalized.strip('_')
    # Remove /songs/ subfolder
    normalized = normalized.replace('/songs/', '/')
    # Remove spaces around hyphens
    normalized = re.sub(r'\s*-\s*', '-', normalized)
    # Normalize multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized

def extract_path_variants(path):
    """Generate multiple path variants for matching"""
    variants = set()

    # Original
    variants.add(path)
    variants.add(normalize_path(path))

    parts = path.split('/')
    if len(parts) >= 2:
        artist = parts[0]
        album = parts[1]

        # Remove duplicate artist name from album
        # e.g., "Beatles/Beatles - Abbey Road" -> "Beatles/Abbey Road"
        album_variants = [album]

        # Try removing artist prefix
        prefixes = [f"{artist} - ", f"{artist}-", f"{artist} "]
        for prefix in prefixes:
            if album.lower().startswith(prefix.lower()):
                album_variants.append(album[len(prefix):])

        for album_var in album_variants:
            variants.add(f"{artist}/{album_var}")
            variants.add(normalize_path(f"{artist}/{album_var}"))

            # Also try with /Songs/ subfolder
            variants.add(f"{artist}/{album_var}/Songs")
            variants.add(normalize_path(f"{artist}/{album_var}/Songs"))

    return variants

class SmartValidator:
    def __init__(self):
        self.s3_folders = {}
        self.dynamodb_records = {}
        self.local_folders = {}
        self.manifests = {}
        self.path_mappings = {}  # old_book_id -> new_book_id and path info
        self.book_id_to_local = {}
        self.book_id_to_s3 = {}

        # Reverse lookups for normalized paths
        self.normalized_local = {}  # normalized -> original path
        self.normalized_s3 = {}

    def load_path_mappings(self):
        """Load path_mapping.csv"""
        print("\n=== Loading Path Mappings ===")

        mapping_file = 'data/reconciliation/path_mapping.csv'
        if not os.path.exists(mapping_file):
            print(f"  WARNING: {mapping_file} not found")
            return

        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_id = row['old_book_id']
                new_id = row['new_book_id']

                self.path_mappings[old_id] = {
                    'new_book_id': new_id if new_id else old_id,
                    'old_uri': row['old_uri'],
                    'new_uri': row['new_uri'],
                    'old_artist': row['old_artist'],
                    'old_book_name': row['old_book_name'],
                    'new_artist': row['new_artist'],
                    'new_book_name': row['new_book_name'],
                    'match_type': row['match_type']
                }

        print(f"Loaded {len(self.path_mappings)} path mappings")

    def scan_local_structure(self):
        """Scan local with normalization"""
        print("\n=== Scanning Local Structure ===")

        if not LOCAL_ROOT.exists():
            print(f"WARNING: {LOCAL_ROOT} does not exist")
            return

        for artist_dir in sorted(LOCAL_ROOT.iterdir()):
            if not artist_dir.is_dir():
                continue

            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue

                songs = list(album_dir.glob('*.pdf'))
                key = f"{artist_dir.name}/{album_dir.name}"

                self.local_folders[key] = {
                    'artist': artist_dir.name,
                    'album': album_dir.name,
                    'song_count': len(songs),
                    'path': str(album_dir)
                }

                # Build normalized lookup
                for variant in extract_path_variants(key):
                    self.normalized_local[variant] = key

        print(f"Found {len(self.local_folders)} local folders")
        print(f"Generated {len(self.normalized_local)} normalized variants")

    def scan_s3_structure(self):
        """Scan S3 with normalization"""
        print("\n=== Scanning S3 Structure ===")

        paginator = s3.get_paginator('list_objects_v2')
        folder_files = defaultdict(list)

        for page in paginator.paginate(Bucket=S3_BUCKET):
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']

                if key.startswith('artifacts/') or key.startswith('output/'):
                    continue
                if not key.endswith('.pdf'):
                    continue

                parts = key.split('/')
                if len(parts) >= 3:
                    artist = parts[0]
                    album = parts[1]
                    filename = parts[-1]

                    folder_key = f"{artist}/{album}"
                    folder_files[folder_key].append({
                        'filename': filename,
                        'size': obj['Size']
                    })

        for folder_key, files in folder_files.items():
            artist, album = folder_key.split('/', 1)
            self.s3_folders[folder_key] = {
                'artist': artist,
                'album': album,
                'song_count': len(files),
                'total_size': sum(f['size'] for f in files)
            }

            # Build normalized lookup
            for variant in extract_path_variants(folder_key):
                self.normalized_s3[variant] = folder_key

        print(f"Found {len(self.s3_folders)} S3 folders")
        print(f"Generated {len(self.normalized_s3)} normalized variants")

    def scan_dynamodb(self):
        """Scan DynamoDB"""
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
                    'songs_extracted': int(item.get('songs_extracted', {}).get('N', 0)),
                    'processing_timestamp': int(item.get('processing_timestamp', {}).get('N', 0)),
                }

                self.dynamodb_records[book_id] = record

        print(f"Found {len(self.dynamodb_records)} DynamoDB records")

    def build_smart_mappings(self):
        """Build smart book_id -> local/S3 mappings"""
        print("\n=== Building Smart Mappings ===")

        for book_id, record in self.dynamodb_records.items():
            artist = record['artist']
            book_name = record['book_name']

            # Get mapped book_id if exists
            if book_id in self.path_mappings:
                mapping = self.path_mappings[book_id]
                new_id = mapping['new_book_id']
                new_artist = mapping['new_artist']
                new_book_name = mapping['new_book_name']

                # Use new values
                artist = new_artist if new_artist else artist
                book_name = new_book_name if new_book_name else book_name

            # Try to find in local
            search_paths = [
                f"{artist}/{book_name}",
                f"{artist}/{artist} - {book_name}",
            ]

            for search_path in search_paths:
                # Try exact match
                if search_path in self.local_folders:
                    self.book_id_to_local[book_id] = search_path
                    break

                # Try normalized match
                for variant in extract_path_variants(search_path):
                    if variant in self.normalized_local:
                        self.book_id_to_local[book_id] = self.normalized_local[variant]
                        break

                if book_id in self.book_id_to_local:
                    break

            # Try to find in S3
            for search_path in search_paths:
                if search_path in self.s3_folders:
                    self.book_id_to_s3[book_id] = search_path
                    break

                for variant in extract_path_variants(search_path):
                    if variant in self.normalized_s3:
                        self.book_id_to_s3[book_id] = self.normalized_s3[variant]
                        break

                if book_id in self.book_id_to_s3:
                    break

        print(f"Mapped {len(self.book_id_to_local)} book_ids to local folders")
        print(f"Mapped {len(self.book_id_to_s3)} book_ids to S3 folders")

    def validate_smart(self):
        """Smart cross-reference validation"""
        print("\n=== Smart Validation ===")

        results = {
            'matched': [],
            's3_only': [],
            'local_only': [],
            'no_dynamodb': [],
        }

        # Track which folders we've matched
        matched_local = set()
        matched_s3 = set()

        # Match by book_id
        for book_id, local_path in self.book_id_to_local.items():
            s3_path = self.book_id_to_s3.get(book_id)

            if s3_path:
                # Fully matched
                results['matched'].append({
                    'book_id': book_id,
                    'local_path': local_path,
                    's3_path': s3_path,
                    'local_songs': self.local_folders[local_path]['song_count'],
                    's3_songs': self.s3_folders[s3_path]['song_count'],
                    'match_type': 'book_id_mapping'
                })
                matched_local.add(local_path)
                matched_s3.add(s3_path)

        # Try fuzzy matching for unmatched folders
        for local_path in self.local_folders:
            if local_path in matched_local:
                continue

            # Try to find fuzzy match in S3
            for variant in extract_path_variants(local_path):
                if variant in self.normalized_s3:
                    s3_path = self.normalized_s3[variant]
                    if s3_path not in matched_s3:
                        results['matched'].append({
                            'book_id': 'unknown',
                            'local_path': local_path,
                            's3_path': s3_path,
                            'local_songs': self.local_folders[local_path]['song_count'],
                            's3_songs': self.s3_folders[s3_path]['song_count'],
                            'match_type': 'fuzzy'
                        })
                        matched_local.add(local_path)
                        matched_s3.add(s3_path)
                        break

        # Local only
        for local_path in self.local_folders:
            if local_path not in matched_local:
                results['local_only'].append({
                    'local_path': local_path,
                    'song_count': self.local_folders[local_path]['song_count']
                })

        # S3 only
        for s3_path in self.s3_folders:
            if s3_path not in matched_s3:
                results['s3_only'].append({
                    's3_path': s3_path,
                    'song_count': self.s3_folders[s3_path]['song_count']
                })

        return results

    def generate_report(self, results):
        """Generate report"""
        report = []
        report.append("=" * 80)
        report.append("SMART SONGBOOK VALIDATION REPORT V2")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)

        report.append("\n## SUMMARY")
        report.append(f"Local folders (SOURCE OF TRUTH): {len(self.local_folders)}")
        report.append(f"S3 folders: {len(self.s3_folders)}")
        report.append(f"DynamoDB records: {len(self.dynamodb_records)}")
        report.append(f"Path mappings loaded: {len(self.path_mappings)}")

        report.append(f"\n## MATCHED: {len(results['matched'])} ({len(results['matched'])/len(self.local_folders)*100:.1f}%)")
        report.append("Folders successfully matched between local and S3")

        match_types = defaultdict(int)
        for m in results['matched']:
            match_types[m['match_type']] += 1

        for match_type, count in match_types.items():
            report.append(f"  - {match_type}: {count}")

        # Show sample mismatches in song counts
        mismatches = [m for m in results['matched'] if m['local_songs'] != m['s3_songs']]
        if mismatches:
            report.append(f"\n  Song count mismatches: {len(mismatches)}")
            for m in mismatches[:10]:
                report.append(f"    {m['local_path']}: Local={m['local_songs']}, S3={m['s3_songs']}")

        report.append(f"\n## S3 ONLY: {len(results['s3_only'])}")
        report.append("Folders in S3 but not in local (likely old/duplicate)")
        if results['s3_only']:
            for item in results['s3_only'][:30]:
                report.append(f"  {item['s3_path']} ({item['song_count']} songs)")

        report.append(f"\n## LOCAL ONLY: {len(results['local_only'])}")
        report.append("Folders in local but not in S3 (investigation needed)")
        if results['local_only']:
            for item in results['local_only'][:30]:
                report.append(f"  {item['local_path']} ({item['song_count']} songs)")

        report.append("\n" + "=" * 80)
        report.append("## NEXT STEPS")
        report.append("=" * 80)
        report.append(f"\n1. DELETE {len(results['s3_only'])} old/duplicate S3 folders")
        report.append(f"2. INVESTIGATE {len(results['local_only'])} local-only folders")
        report.append(f"3. FIX song count mismatches for {len(mismatches)} folders")
        report.append(f"4. UPDATE DynamoDB to reflect current paths")

        return "\n".join(report)

def main():
    print("SMART SONGBOOK VALIDATION V2")
    print("=" * 80)

    validator = SmartValidator()

    validator.load_path_mappings()
    validator.scan_local_structure()
    validator.scan_s3_structure()
    validator.scan_dynamodb()
    validator.build_smart_mappings()

    results = validator.validate_smart()
    report = validator.generate_report(results)

    output_file = 'data/analysis/songbook_validation_v2_report.txt'
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to {output_file}")
    print("\n" + report)

    # Save JSON
    json_file = 'data/analysis/songbook_validation_v2_data.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'local_folders': len(validator.local_folders),
                's3_folders': len(validator.s3_folders),
                'dynamodb_records': len(validator.dynamodb_records),
                'matched': len(results['matched']),
                's3_only': len(results['s3_only']),
                'local_only': len(results['local_only'])
            },
            'results': results
        }, f, indent=2, default=str)

    print(f"Data saved to {json_file}")

if __name__ == '__main__':
    main()
