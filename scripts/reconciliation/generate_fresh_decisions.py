"""
Generate fresh reconciliation decisions based on current match quality data
Focuses on EXCELLENT and GOOD folders to convert them to PERFECT
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict
import re

# S3 setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Load current match quality data
print("Loading current match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

def normalize_filename(filename, artist):
    """Normalize filename to use proper artist name"""
    # Remove common prefixes like "Unknown Artist", "The Image Does Not", etc.
    patterns_to_remove = [
        r'^Unknown Artist\s*-\s*',
        r'^The Image Does Not.*?-\s*',
        r'^Written [Aa]nd Music [Bb]y.*?-\s*',
        r'^\(.*?\)\s*-\s*',
        r'^Traditional.*?-\s*',
    ]

    cleaned = filename
    for pattern in patterns_to_remove:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # If it doesn't start with the artist name, prepend it
    if not cleaned.lower().startswith(artist.lower()):
        # Extract just the song title (everything after the first " - ")
        if ' - ' in cleaned:
            song_title = cleaned.split(' - ', 1)[1]
            cleaned = f"{artist} - {song_title}"

    return cleaned

# Generate decisions for EXCELLENT and GOOD folders
decisions = {}
stats = defaultdict(int)

target_tiers = ['excellent', 'good']
print(f"\nGenerating decisions for {target_tiers} tiers...")

for tier_name in target_tiers:
    folders = match_data['quality_tiers'].get(tier_name, [])
    print(f"\nProcessing {len(folders)} {tier_name.upper()} folders...")

    for folder in folders:
        local_path = folder.get('local_path', '')
        s3_path = folder.get('s3_path', '')
        artist = folder.get('manifest_content', {}).get('artist', '').split('/')[0]

        fc = folder.get('file_comparison', {})
        local_only = fc.get('local_only_files', [])
        s3_only = fc.get('s3_only_files', [])
        size_mismatches = fc.get('size_mismatches', [])

        file_decisions = {}

        # Handle S3-only files (need to copy to local)
        for f in s3_only:
            filename = f['filename'] if isinstance(f, dict) else f
            file_decisions[filename] = {
                'action': 'copy-s3-to-local',
                'filepath': filename,
                'local_path': local_path,
                's3_path': s3_path,
                'reason': 'File exists in S3 but not locally'
            }
            stats['s3_to_local_copies'] += 1

        # Handle local-only files (need to copy to S3)
        for f in local_only:
            filename = f['filename'] if isinstance(f, dict) else f
            file_decisions[filename] = {
                'action': 'copy-local-to-s3',
                'filepath': filename,
                'local_path': local_path,
                's3_path': s3_path,
                'reason': 'File exists locally but not in S3'
            }
            stats['local_to_s3_copies'] += 1

        # Handle size mismatches (prefer local version, copy to S3)
        for mismatch in size_mismatches:
            filename = mismatch['filename'] if isinstance(mismatch, dict) else mismatch
            file_decisions[filename] = {
                'action': 'copy-local-to-s3-overwrite',
                'filepath': filename,
                'local_path': local_path,
                's3_path': s3_path,
                'local_size': mismatch.get('local_size'),
                's3_size': mismatch.get('s3_size'),
                'reason': 'Size mismatch - using local version'
            }
            stats['size_mismatch_fixes'] += 1

        # Only add to decisions if there are file operations
        if file_decisions:
            decisions[local_path] = {
                'local_path': local_path,
                's3_path': s3_path,
                'artist': artist,
                'tier': tier_name,
                'fileDecisions': file_decisions
            }

# Save decisions
output_file = 'reconciliation_decisions_2026-02-02_fresh.json'
output = {
    'decisions': decisions,
    'metadata': {
        'source': 'match_quality_data.json',
        'target_tiers': target_tiers,
        'total_folders': len(decisions),
        'total_operations': sum(len(d['fileDecisions']) for d in decisions.values()),
        'generated': '2026-02-02'
    },
    'stats': dict(stats)
}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"\n{'='*80}")
print("DECISION GENERATION SUMMARY")
print(f"{'='*80}")
print(f"Folders with decisions: {len(decisions)}")
print(f"Total operations: {output['metadata']['total_operations']}")
print(f"\nOperation breakdown:")
print(f"  S3->Local copies:     {stats['s3_to_local_copies']}")
print(f"  Local->S3 copies:     {stats['local_to_s3_copies']}")
print(f"  Size mismatch fixes:  {stats['size_mismatch_fixes']}")
print(f"\nDecisions saved to: {output_file}")
print("\nNext step: Execute these decisions with execute_fresh_decisions.py")
