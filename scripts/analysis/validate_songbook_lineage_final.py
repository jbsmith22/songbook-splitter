"""
FINAL VERSION: Complete normalization with all edge cases
"""
import json
import boto3
import os
import csv
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.client('dynamodb')

S3_BUCKET = 'jsmith-output'
DYNAMODB_TABLE = 'jsmith-processing-ledger'
LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

def normalize_path(path):
    """COMPREHENSIVE path normalization"""
    normalized = path.lower()

    # Replace & with and
    normalized = re.sub(r'\s*&\s*', ' and ', normalized)

    # Remove apostrophes
    normalized = normalized.replace("'", "")

    # Replace brackets and parenthesis with underscores
    normalized = re.sub(r'[\[\]\(\)]', '_', normalized)

    # Remove multiple underscores
    normalized = re.sub(r'_+', '_', normalized)

    # Remove trailing/leading underscores
    normalized = normalized.strip('_')

    # Remove /songs/ subfolder
    normalized = normalized.replace('/songs/', '/')
    normalized = normalized.replace('/songs', '')

    # Normalize spaces around hyphens
    normalized = re.sub(r'\s*-\s*', '-', normalized)

    # Normalize multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)

    # Remove dots and commas
    normalized = normalized.replace('.', '').replace(',', '')

    return normalized

def extract_path_variants(path):
    """Generate ALL possible path variants"""
    variants = set()

    # Add original and normalized
    variants.add(path)
    variants.add(normalize_path(path))

    parts = path.split('/')
    if len(parts) >= 2:
        artist = parts[0]
        album = parts[1]

        # Generate album variants
        album_variants = [album]

        # Try removing artist prefix
        prefixes = [f"{artist} - ", f"{artist}-", f"{artist} "]
        for prefix in prefixes:
            if album.lower().startswith(prefix.lower()):
                album_variants.append(album[len(prefix):])

        # Try adding "Various Artists - " prefix
        if not album.lower().startswith('various artists'):
            album_variants.append(f"Various Artists - {album}")

        # Generate all combinations
        for album_var in album_variants:
            variants.add(f"{artist}/{album_var}")
            variants.add(normalize_path(f"{artist}/{album_var}"))

    return variants

class FinalValidator:
    def __init__(self):
        self.s3_folders = {}
        self.dynamodb_records = {}
        self.local_folders = {}
        self.path_mappings = {}
        self.book_id_to_local = {}
        self.book_id_to_s3 = {}
        self.normalized_local = {}
        self.normalized_s3 = {}

    def load_path_mappings(self):
        print("\n=== Loading Path Mappings ===")
        mapping_file = 'data/reconciliation/path_mapping.csv'
        if not os.path.exists(mapping_file):
            return

        with open(mapping_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                old_id = row['old_book_id']
                self.path_mappings[old_id] = {
                    'new_book_id': row['new_book_id'] if row['new_book_id'] else old_id,
                    'new_artist': row['new_artist'],
                    'new_book_name': row['new_book_name'],
                }

        print(f"Loaded {len(self.path_mappings)} mappings")

    def scan_local_structure(self):
        print("\n=== Scanning Local ===")

        for artist_dir in sorted(LOCAL_ROOT.iterdir()):
            if not artist_dir.is_dir():
                continue

            for album_dir in artist_dir.iterdir():
                if not album_dir.is_dir():
                    continue

                songs = list(album_dir.glob('*.pdf'))
                key = f"{artist_dir.name}/{album_dir.name}"

                self.local_folders[key] = {
                    'song_count': len(songs),
                }

                for variant in extract_path_variants(key):
                    self.normalized_local[variant] = key

        print(f"Local: {len(self.local_folders)} folders, {len(self.normalized_local)} variants")

    def scan_s3_structure(self):
        print("\n=== Scanning S3 ===")

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

                    # Handle /Songs/ subfolder
                    if len(parts) == 4 and parts[2].lower() == 'songs':
                        filename = parts[3]
                    else:
                        filename = parts[-1]

                    folder_key = f"{artist}/{album}"
                    folder_files[folder_key].append(filename)

        for folder_key, files in folder_files.items():
            self.s3_folders[folder_key] = {
                'song_count': len(files),
            }

            for variant in extract_path_variants(folder_key):
                self.normalized_s3[variant] = folder_key

        print(f"S3: {len(self.s3_folders)} folders, {len(self.normalized_s3)} variants")

    def scan_dynamodb(self):
        print("\n=== Scanning DynamoDB ===")

        paginator = dynamodb.get_paginator('scan')

        for page in paginator.paginate(TableName=DYNAMODB_TABLE):
            for item in page['Items']:
                book_id = item['book_id']['S']
                self.dynamodb_records[book_id] = {
                    'artist': item.get('artist', {}).get('S', ''),
                    'book_name': item.get('book_name', {}).get('S', ''),
                }

        print(f"DynamoDB: {len(self.dynamodb_records)} records")

    def build_mappings(self):
        print("\n=== Building Mappings ===")

        for book_id, record in self.dynamodb_records.items():
            artist = record['artist']
            book_name = record['book_name']

            # Get mapped values
            if book_id in self.path_mappings:
                mapping = self.path_mappings[book_id]
                artist = mapping['new_artist'] if mapping['new_artist'] else artist
                book_name = mapping['new_book_name'] if mapping['new_book_name'] else book_name

            # Find in local
            search_paths = [
                f"{artist}/{book_name}",
                f"{artist}/{artist} - {book_name}",
            ]

            for search_path in search_paths:
                if search_path in self.local_folders:
                    self.book_id_to_local[book_id] = search_path
                    break

                for variant in extract_path_variants(search_path):
                    if variant in self.normalized_local:
                        self.book_id_to_local[book_id] = self.normalized_local[variant]
                        break

                if book_id in self.book_id_to_local:
                    break

            # Find in S3
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

        print(f"Mapped {len(self.book_id_to_local)} to local, {len(self.book_id_to_s3)} to S3")

    def validate(self):
        print("\n=== Validating ===")

        results = {
            'matched': [],
            's3_only': [],
            'local_only': [],
        }

        matched_local = set()
        matched_s3 = set()

        # Match by book_id
        for book_id, local_path in self.book_id_to_local.items():
            s3_path = self.book_id_to_s3.get(book_id)

            if s3_path:
                results['matched'].append({
                    'book_id': book_id,
                    'local_path': local_path,
                    's3_path': s3_path,
                    'local_songs': self.local_folders[local_path]['song_count'],
                    's3_songs': self.s3_folders[s3_path]['song_count'],
                })
                matched_local.add(local_path)
                matched_s3.add(s3_path)

        # Fuzzy match remaining
        for local_path in self.local_folders:
            if local_path in matched_local:
                continue

            for variant in extract_path_variants(local_path):
                if variant in self.normalized_s3:
                    s3_path = self.normalized_s3[variant]
                    if s3_path not in matched_s3:
                        results['matched'].append({
                            'book_id': 'fuzzy',
                            'local_path': local_path,
                            's3_path': s3_path,
                            'local_songs': self.local_folders[local_path]['song_count'],
                            's3_songs': self.s3_folders[s3_path]['song_count'],
                        })
                        matched_local.add(local_path)
                        matched_s3.add(s3_path)
                        break

        # Collect unmatched
        for local_path in self.local_folders:
            if local_path not in matched_local:
                results['local_only'].append({
                    'local_path': local_path,
                    'song_count': self.local_folders[local_path]['song_count']
                })

        for s3_path in self.s3_folders:
            if s3_path not in matched_s3:
                results['s3_only'].append({
                    's3_path': s3_path,
                    'song_count': self.s3_folders[s3_path]['song_count']
                })

        return results

    def report(self, results):
        lines = []
        lines.append("=" * 80)
        lines.append("FINAL VALIDATION REPORT")
        lines.append("=" * 80)

        match_rate = len(results['matched'])/len(self.local_folders)*100
        lines.append(f"\nMATCHED: {len(results['matched'])}/{len(self.local_folders)} ({match_rate:.1f}%)")
        lines.append(f"S3 ONLY: {len(results['s3_only'])}")
        lines.append(f"LOCAL ONLY: {len(results['local_only'])}")

        if results['local_only']:
            lines.append("\n## LOCAL ONLY (not found in S3):")
            for item in results['local_only']:
                lines.append(f"  {item['local_path']} ({item['song_count']} songs)")

        mismatches = [m for m in results['matched']
                     if m['local_songs'] != m['s3_songs']]
        lines.append(f"\n## SONG COUNT MISMATCHES: {len(mismatches)}")
        for m in mismatches[:20]:
            lines.append(f"  {m['local_path']}: L={m['local_songs']}, S3={m['s3_songs']}")

        return "\n".join(lines)

def main():
    v = FinalValidator()
    v.load_path_mappings()
    v.scan_local_structure()
    v.scan_s3_structure()
    v.scan_dynamodb()
    v.build_mappings()
    results = v.validate()
    report = v.report(results)

    print("\n" + report)

    with open('data/analysis/final_validation_report.txt', 'w') as f:
        f.write(report)

    with open('data/analysis/final_validation_data.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print("\n*** Saved to data/analysis/final_validation_*")

if __name__ == '__main__':
    main()
