"""
Match Quality Analysis - Breakdown of 540 matched folders
Analyzes EXACT matches by:
1. File count (local == S3)
2. Alphabetic folder name match (case insensitive)
3. Metadata confirmation (manifest + artifacts)
"""
import json
import boto3
import re
from collections import defaultdict

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

def strip_to_alpha(text):
    """Remove all non-alphabetic characters and lowercase"""
    return re.sub(r'[^a-zA-Z]', '', text).lower()

def check_manifest_exists(book_id):
    """Check if manifest.json exists for this book_id"""
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=f'output/{book_id}/manifest.json')
        return True
    except:
        return False

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

class MatchQualityAnalyzer:
    def __init__(self):
        self.validation_results = None
        self.quality_tiers = {
            'perfect': [],      # Exact count + exact name + full metadata
            'excellent': [],    # Exact count + exact name + partial metadata
            'good': [],         # Exact count + fuzzy name + metadata
            'fair': [],         # Exact count + fuzzy name + no metadata
            'weak': [],         # Different count + fuzzy name + metadata
            'poor': []          # Different count + fuzzy name + no metadata
        }

    def load_validation_results(self):
        """Load final_validation_data.json"""
        print("\n=== Loading Validation Results ===")
        with open('data/analysis/final_validation_data.json', 'r') as f:
            data = json.load(f)
            self.validation_results = data['matched']
        print(f"Loaded {len(self.validation_results)} matched folders")

    def analyze_match_quality(self):
        """Analyze each matched folder for quality"""
        print("\n=== Analyzing Match Quality ===")

        for i, match in enumerate(self.validation_results):
            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1}/{len(self.validation_results)}...")

            book_id = match['book_id']
            local_path = match['local_path']
            s3_path = match['s3_path']
            local_songs = match['local_songs']
            s3_songs = match['s3_songs']

            # Check criteria
            exact_count = (local_songs == s3_songs)
            exact_alpha_name = (strip_to_alpha(local_path) == strip_to_alpha(s3_path))

            # Check metadata (skip if book_id is 'fuzzy' or 'unknown')
            has_manifest = False
            artifacts_count = 0
            artifacts_list = []

            if book_id not in ['fuzzy', 'unknown', '']:
                has_manifest = check_manifest_exists(book_id)
                artifacts_count, artifacts_list = check_artifacts_exist(book_id)

            has_full_metadata = has_manifest and artifacts_count == 5
            has_partial_metadata = has_manifest or artifacts_count > 0

            # Create match record
            record = {
                'book_id': book_id,
                'local_path': local_path,
                's3_path': s3_path,
                'local_songs': local_songs,
                's3_songs': s3_songs,
                'exact_count': exact_count,
                'exact_alpha_name': exact_alpha_name,
                'has_manifest': has_manifest,
                'artifacts_count': artifacts_count,
                'artifacts_list': artifacts_list
            }

            # Categorize into quality tiers
            if exact_count and exact_alpha_name and has_full_metadata:
                self.quality_tiers['perfect'].append(record)
            elif exact_count and exact_alpha_name and has_partial_metadata:
                self.quality_tiers['excellent'].append(record)
            elif exact_count and has_full_metadata:
                self.quality_tiers['good'].append(record)
            elif exact_count:
                self.quality_tiers['fair'].append(record)
            elif has_full_metadata:
                self.quality_tiers['weak'].append(record)
            else:
                self.quality_tiers['poor'].append(record)

        print(f"  Completed analysis of {len(self.validation_results)} matches")

    def generate_report(self):
        """Generate detailed quality report"""
        lines = []
        lines.append("=" * 80)
        lines.append("MATCH QUALITY ANALYSIS")
        lines.append("=" * 80)

        lines.append("\n## QUALITY TIER BREAKDOWN")
        lines.append(f"Total matched folders: {len(self.validation_results)}")
        lines.append("")

        # Summary counts
        for tier, records in self.quality_tiers.items():
            pct = len(records) / len(self.validation_results) * 100
            lines.append(f"{tier.upper()}: {len(records)} ({pct:.1f}%)")

        lines.append("\n" + "=" * 80)
        lines.append("## TIER DEFINITIONS")
        lines.append("=" * 80)

        lines.append("\nPERFECT: Exact file count + Exact alphabetic name + Full metadata")
        lines.append("EXCELLENT: Exact file count + Exact alphabetic name + Partial metadata")
        lines.append("GOOD: Exact file count + Fuzzy name + Full metadata")
        lines.append("FAIR: Exact file count + Fuzzy name + No/partial metadata")
        lines.append("WEAK: Different file count + Fuzzy name + Full metadata")
        lines.append("POOR: Different file count + Fuzzy name + No/partial metadata")

        lines.append("\n" + "=" * 80)
        lines.append("## EXACT MATCH CRITERIA SUMMARY")
        lines.append("=" * 80)

        exact_count_matches = sum(len(records) for tier in ['perfect', 'excellent', 'good', 'fair']
                                  for records in [self.quality_tiers[tier]])
        exact_name_matches = sum(len(self.quality_tiers[t]) for t in ['perfect', 'excellent'])
        full_metadata_matches = sum(len(self.quality_tiers[t]) for t in ['perfect', 'good', 'weak'])

        lines.append(f"\nExact file count matches: {exact_count_matches}/{len(self.validation_results)} ({exact_count_matches/len(self.validation_results)*100:.1f}%)")
        lines.append(f"Exact alphabetic name matches: {exact_name_matches}/{len(self.validation_results)} ({exact_name_matches/len(self.validation_results)*100:.1f}%)")
        lines.append(f"Full metadata (manifest + 5 artifacts): {full_metadata_matches}/{len(self.validation_results)} ({full_metadata_matches/len(self.validation_results)*100:.1f}%)")

        lines.append("\n" + "=" * 80)
        lines.append("## PERFECT MATCHES")
        lines.append("=" * 80)
        lines.append(f"\n{len(self.quality_tiers['perfect'])} folders with EXACT file count, EXACT name, and FULL metadata")

        for record in self.quality_tiers['perfect'][:20]:
            lines.append(f"  ✓ {record['local_path']}")
            lines.append(f"    Book ID: {record['book_id']}")
            lines.append(f"    Songs: {record['local_songs']}")
            lines.append("")

        if len(self.quality_tiers['perfect']) > 20:
            lines.append(f"  ... and {len(self.quality_tiers['perfect']) - 20} more")

        lines.append("\n" + "=" * 80)
        lines.append("## POOR MATCHES - INVESTIGATION NEEDED")
        lines.append("=" * 80)
        lines.append(f"\n{len(self.quality_tiers['poor'])} folders with different file counts and no/partial metadata")

        for record in self.quality_tiers['poor'][:30]:
            lines.append(f"  ⚠️  {record['local_path']}")
            lines.append(f"    S3 path: {record['s3_path']}")
            lines.append(f"    Songs: Local={record['local_songs']}, S3={record['s3_songs']}")
            lines.append(f"    Book ID: {record['book_id']}")
            lines.append(f"    Metadata: manifest={record['has_manifest']}, artifacts={record['artifacts_count']}/5")
            lines.append("")

        if len(self.quality_tiers['poor']) > 30:
            lines.append(f"  ... and {len(self.quality_tiers['poor']) - 30} more")

        lines.append("\n" + "=" * 80)
        lines.append("## WEAK MATCHES - FILE COUNT MISMATCHES")
        lines.append("=" * 80)
        lines.append(f"\n{len(self.quality_tiers['weak'])} folders with different file counts but full metadata")

        for record in self.quality_tiers['weak'][:20]:
            diff = record['s3_songs'] - record['local_songs']
            sign = "+" if diff > 0 else ""
            lines.append(f"  {record['local_path']}")
            lines.append(f"    Local: {record['local_songs']}, S3: {record['s3_songs']} ({sign}{diff})")
            lines.append("")

        if len(self.quality_tiers['weak']) > 20:
            lines.append(f"  ... and {len(self.quality_tiers['weak']) - 20} more")

        return "\n".join(lines)

def main():
    analyzer = MatchQualityAnalyzer()
    analyzer.load_validation_results()
    analyzer.analyze_match_quality()
    report = analyzer.generate_report()

    print("\n" + report)

    # Save report
    with open('data/analysis/match_quality_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n*** Report saved to data/analysis/match_quality_report.txt")

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

if __name__ == '__main__':
    main()
