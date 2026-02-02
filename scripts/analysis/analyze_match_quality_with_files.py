"""
Enhanced Match Quality Analysis with FILE-LEVEL validation
Analyzes EXACT matches by:
1. File count (local == S3)
2. Alphabetic folder name match (case insensitive)
3. Metadata confirmation (manifest + artifacts)
4. FILE-LEVEL: Same filenames and MD5 checksums (location in /Songs/ subfolder doesn't matter)
"""
import json
import boto3
import re
import hashlib
from pathlib import Path
from collections import defaultdict

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'
LOCAL_ROOT = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

def strip_to_alpha(text):
    """Remove all non-alphabetic characters and lowercase"""
    return re.sub(r'[^a-zA-Z]', '', text).lower()

def compute_local_file_md5(file_path):
    """Compute MD5 hash of a local file"""
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5.update(chunk)
    return md5.hexdigest()

def get_s3_file_md5(bucket, key):
    """Get MD5 hash of S3 file (from ETag if not multipart)"""
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        etag = response['ETag'].strip('"')

        # If ETag contains a hyphen, it's a multipart upload and not a simple MD5
        if '-' in etag:
            # Download and compute MD5 for multipart uploads
            obj = s3.get_object(Bucket=bucket, Key=key)
            md5 = hashlib.md5()
            for chunk in iter(lambda: obj['Body'].read(8192), b''):
                md5.update(chunk)
            return md5.hexdigest()
        else:
            return etag
    except Exception as e:
        return None

def check_manifest_exists(book_id):
    """Check if manifest.json exists for this book_id"""
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=f'output/{book_id}/manifest.json')
        return True
    except:
        return False

def get_manifest_content(book_id):
    """Fetch and return the manifest.json content for this book_id"""
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=f'output/{book_id}/manifest.json')
        manifest_text = response['Body'].read().decode('utf-8')
        return json.loads(manifest_text)
    except Exception as e:
        return None

def check_artifacts_exist(book_id):
    """Check if all 5 artifact files exist for this book_id"""
    required_files = [
        'toc_discovery.json',
        'toc_parse.json',
        'page_mapping.json',
        'verified_songs.json',
        'output_files.json'
    ]

    found = []
    for filename in required_files:
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=f'artifacts/{book_id}/{filename}')
            found.append(filename)
        except:
            pass

    return len(found), found

def get_local_files(local_path):
    """Get all PDF files in local folder with sizes"""
    full_path = LOCAL_ROOT / local_path
    files = {}
    for pdf_file in full_path.glob('*.pdf'):
        files[pdf_file.name] = {
            'path': str(pdf_file),
            'size': pdf_file.stat().st_size
        }
    return files

def get_s3_files(s3_path):
    """Get all PDF files in S3 folder with sizes (handles /Songs/ subfolder)"""
    files = {}

    # Try both with and without /Songs/ subfolder
    prefixes = [
        f"{s3_path}/",
        f"{s3_path}/Songs/",
        f"{s3_path}/songs/"
    ]

    for prefix in prefixes:
        try:
            paginator = s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        key = obj['Key']
                        if key.endswith('.pdf'):
                            filename = key.split('/')[-1]
                            # Only add if not already found (prefer non-Songs version)
                            if filename not in files:
                                files[filename] = {
                                    'key': key,
                                    'size': obj['Size']
                                }
        except:
            continue

    return files

class EnhancedMatchAnalyzer:
    def __init__(self):
        self.validation_results = None
        self.quality_tiers = {
            'perfect': [],      # Exact count + exact name + full metadata + all files match
            'excellent': [],    # Exact count + exact name + partial metadata + most files match
            'good': [],         # Exact count + fuzzy name + metadata + files match
            'fair': [],         # Exact count + fuzzy name + some file mismatches
            'weak': [],         # Different count + metadata + some files match
            'poor': []          # Different count + no metadata + major file mismatches
        }
        self.file_comparison_cache = {}

    def load_validation_results(self):
        """Load final_validation_data.json"""
        print("\n=== Loading Validation Results ===")
        with open('data/analysis/final_validation_data.json', 'r') as f:
            data = json.load(f)
            self.validation_results = data['matched']
        print(f"Loaded {len(self.validation_results)} matched folders")

    def compare_files(self, local_path, s3_path):
        """
        Compare files between local and S3
        Uses filename + filesize matching (no MD5)
        Returns: file comparison details
        """
        local_files = get_local_files(local_path)
        s3_files = get_s3_files(s3_path)

        local_names = set(local_files.keys())
        s3_names = set(s3_files.keys())

        matching_names = local_names & s3_names
        local_only = local_names - s3_names
        s3_only = s3_names - local_names

        # Check size matches for files with matching names
        matching_files = 0
        size_mismatches = []

        for filename in matching_names:
            local_size = local_files[filename]['size']
            s3_size = s3_files[filename]['size']

            if local_size == s3_size:
                # Same name + same size = match
                matching_files += 1
            else:
                # Same name but different sizes
                size_mismatches.append({
                    'filename': filename,
                    'local_size': local_size,
                    's3_size': s3_size
                })

        # Build file lists with sizes
        local_only_with_sizes = [
            {'filename': f, 'size': local_files[f]['size']}
            for f in local_only
        ]
        s3_only_with_sizes = [
            {'filename': f, 'size': s3_files[f]['size']}
            for f in s3_only
        ]

        return {
            'total_local': len(local_files),
            'total_s3': len(s3_files),
            'matching_names': len(matching_names),
            'matching_files': matching_files,  # Same name + same size
            'local_only_files': local_only_with_sizes,
            's3_only_files': s3_only_with_sizes,
            'size_mismatches': size_mismatches
        }

    def analyze_match_quality(self):
        """Analyze each matched folder for quality INCLUDING file-level comparison"""
        print("\n=== Analyzing Match Quality (with file-level validation) ===")
        print("NOTE: Using filename + filesize matching (no MD5)")

        for i, match in enumerate(self.validation_results):
            if (i + 1) % 25 == 0:
                print(f"  Processed {i + 1}/{len(self.validation_results)}...")

            book_id = match['book_id']
            local_path = match['local_path']
            s3_path = match['s3_path']
            local_songs = match['local_songs']
            s3_songs = match['s3_songs']

            # Folder-level checks
            exact_count = (local_songs == s3_songs)
            exact_alpha_name = (strip_to_alpha(local_path) == strip_to_alpha(s3_path))

            # Metadata checks
            has_manifest = False
            artifacts_count = 0
            artifacts_list = []
            manifest_content = None

            if book_id not in ['fuzzy', 'unknown', '']:
                has_manifest = check_manifest_exists(book_id)
                artifacts_count, artifacts_list = check_artifacts_exist(book_id)
                if has_manifest:
                    manifest_content = get_manifest_content(book_id)

            has_full_metadata = has_manifest and artifacts_count == 5
            has_partial_metadata = has_manifest or artifacts_count > 0

            # File-level comparison
            file_comparison = self.compare_files(local_path, s3_path)

            # Use actual file counts from comparison (more accurate than validation counts)
            local_songs = file_comparison['total_local']
            s3_songs = file_comparison['total_s3']
            exact_count = (local_songs == s3_songs)

            all_files_match = (
                file_comparison['total_local'] == file_comparison['total_s3'] and
                file_comparison['matching_files'] == file_comparison['total_local'] and
                len(file_comparison['size_mismatches']) == 0
            )

            most_files_match = (
                file_comparison['matching_files'] >= file_comparison['total_local'] * 0.8 if file_comparison['total_local'] > 0 else False
            )

            # Create record
            record = {
                'book_id': book_id,
                'local_path': local_path,
                's3_path': s3_path,
                'local_songs': local_songs,
                's3_songs': s3_songs,
                'exact_count': exact_count,
                'exact_alpha_name': exact_alpha_name,
                'has_manifest': has_manifest,
                'manifest_content': manifest_content,
                'artifacts_count': artifacts_count,
                'artifacts_list': artifacts_list,
                'file_comparison': file_comparison,
                'all_files_match': all_files_match,
                'most_files_match': most_files_match
            }

            # Categorize into quality tiers
            if exact_count and exact_alpha_name and has_full_metadata and all_files_match:
                self.quality_tiers['perfect'].append(record)
            elif exact_count and exact_alpha_name and has_partial_metadata and most_files_match:
                self.quality_tiers['excellent'].append(record)
            elif exact_count and has_full_metadata and most_files_match:
                self.quality_tiers['good'].append(record)
            elif exact_count and most_files_match:
                self.quality_tiers['fair'].append(record)
            elif has_full_metadata and most_files_match:
                self.quality_tiers['weak'].append(record)
            else:
                self.quality_tiers['poor'].append(record)

        print(f"  Completed analysis of {len(self.validation_results)} matches")

    def generate_report(self):
        """Generate detailed quality report"""
        lines = []
        lines.append("=" * 80)
        lines.append("ENHANCED MATCH QUALITY ANALYSIS WITH FILE-LEVEL VALIDATION")
        lines.append("=" * 80)

        lines.append("\n## QUALITY TIER BREAKDOWN")
        lines.append(f"Total matched folders: {len(self.validation_results)}")
        lines.append("")

        for tier, records in self.quality_tiers.items():
            pct = len(records) / len(self.validation_results) * 100 if self.validation_results else 0
            lines.append(f"{tier.upper()}: {len(records)} ({pct:.1f}%)")

        lines.append("\n" + "=" * 80)
        lines.append("## TIER DEFINITIONS")
        lines.append("=" * 80)

        lines.append("\nPERFECT: Exact count + Exact name + Full metadata + All files match (name+size)")
        lines.append("EXCELLENT: Exact count + Exact name + Partial metadata + Most files match")
        lines.append("GOOD: Exact count + Fuzzy name + Full metadata + Most files match")
        lines.append("FAIR: Exact count + Fuzzy name + Most files match")
        lines.append("WEAK: Different count + Full metadata + Most files match")
        lines.append("POOR: Different count + No/partial metadata + File mismatches")

        lines.append("\n" + "=" * 80)
        lines.append("## EXACT MATCH CRITERIA SUMMARY")
        lines.append("=" * 80)

        exact_count_matches = sum(len(records) for tier in ['perfect', 'excellent', 'good', 'fair']
                                  for records in [self.quality_tiers[tier]])
        exact_name_matches = sum(len(self.quality_tiers[t]) for t in ['perfect', 'excellent'])
        full_metadata_matches = sum(len(self.quality_tiers[t]) for t in ['perfect', 'good', 'weak'])
        all_files_match = len(self.quality_tiers['perfect'])

        lines.append(f"\nExact file count matches: {exact_count_matches}/{len(self.validation_results)} ({exact_count_matches/len(self.validation_results)*100:.1f}%)")
        lines.append(f"Exact alphabetic name matches: {exact_name_matches}/{len(self.validation_results)} ({exact_name_matches/len(self.validation_results)*100:.1f}%)")
        lines.append(f"Full metadata (manifest + 5 artifacts): {full_metadata_matches}/{len(self.validation_results)} ({full_metadata_matches/len(self.validation_results)*100:.1f}%)")
        lines.append(f"All files match (name + size): {all_files_match}/{len(self.validation_results)} ({all_files_match/len(self.validation_results)*100:.1f}%)")

        lines.append("\n" + "=" * 80)
        lines.append("## PERFECT MATCHES")
        lines.append("=" * 80)
        lines.append(f"\n{len(self.quality_tiers['perfect'])} folders with EXACT count, EXACT name, FULL metadata, and ALL FILES MATCH")

        for record in self.quality_tiers['perfect'][:20]:
            lines.append(f"  * {record['local_path']}")
            lines.append(f"    Book ID: {record['book_id']}")
            lines.append(f"    Songs: {record['local_songs']}")
            fc = record['file_comparison']
            lines.append(f"    Files: {fc['matching_files']}/{fc['total_local']} match (name+size)")
            lines.append("")

        if len(self.quality_tiers['perfect']) > 20:
            lines.append(f"  ... and {len(self.quality_tiers['perfect']) - 20} more")

        lines.append("\n" + "=" * 80)
        lines.append("## POOR MATCHES - INVESTIGATION NEEDED")
        lines.append("=" * 80)
        lines.append(f"\n{len(self.quality_tiers['poor'])} folders with file count/content mismatches or missing metadata")

        for record in self.quality_tiers['poor'][:30]:
            lines.append(f"  ! {record['local_path']}")
            lines.append(f"    S3 path: {record['s3_path']}")
            lines.append(f"    Songs: Local={record['local_songs']}, S3={record['s3_songs']}")
            lines.append(f"    Book ID: {record['book_id']}")
            lines.append(f"    Metadata: manifest={record['has_manifest']}, artifacts={record['artifacts_count']}/5")
            fc = record['file_comparison']
            lines.append(f"    Files: {fc['matching_files']}/{fc['total_local']} match (name+size), {len(fc.get('size_mismatches', []))} size mismatches")
            if fc['local_only_files']:
                local_files_str = ', '.join([f['filename'] for f in fc['local_only_files'][:3]])
                lines.append(f"    Local-only files: {local_files_str}")
            if fc['s3_only_files']:
                s3_files_str = ', '.join([f['filename'] for f in fc['s3_only_files'][:3]])
                lines.append(f"    S3-only files: {s3_files_str}")
            lines.append("")

        if len(self.quality_tiers['poor']) > 30:
            lines.append(f"  ... and {len(self.quality_tiers['poor']) - 30} more")

        return "\n".join(lines)

def main():
    analyzer = EnhancedMatchAnalyzer()
    analyzer.load_validation_results()
    analyzer.analyze_match_quality()
    report = analyzer.generate_report()

    # Save report (avoid console encoding issues)
    with open('data/analysis/match_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print("\n*** Report saved to data/analysis/match_quality_report.txt")

    # Save detailed JSON
    with open('data/analysis/match_quality_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'total_matches': len(analyzer.validation_results),
            'quality_tiers': analyzer.quality_tiers,
            'summary': {
                'perfect': len(analyzer.quality_tiers['perfect']),
                'excellent': len(analyzer.quality_tiers['excellent']),
                'good': len(analyzer.quality_tiers['good']),
                'fair': len(analyzer.quality_tiers['fair']),
                'weak': len(analyzer.quality_tiers['weak']),
                'poor': len(analyzer.quality_tiers['poor'])
            }
        }, f, indent=2, default=str)

    print(f"*** Data saved to data/analysis/match_quality_data.json")

    # Print summary to console
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    for tier, records in analyzer.quality_tiers.items():
        pct = len(records) / len(analyzer.validation_results) * 100
        print(f"{tier.upper()}: {len(records)} ({pct:.1f}%)")

if __name__ == '__main__':
    main()
