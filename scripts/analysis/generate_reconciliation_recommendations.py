"""
Generate fresh reconciliation recommendations for the 248 remaining folders
"""
import json
import boto3
from pathlib import Path
from collections import defaultdict

# AWS setup
s3_client = boto3.client('s3')
bucket = 'jsmith-output'

# Paths
local_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

# Load current match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

all_folders = []
for tier_name, tier_folders in match_data['quality_tiers'].items():
    all_folders.extend(tier_folders)

print(f"Found {len(all_folders)} folders to analyze\n")

stats = defaultdict(int)
decisions = {}

for i, folder in enumerate(all_folders, 1):
    folder_key = folder.get('s3_path', '') or folder.get('local_path', '')
    local_path = folder.get('local_path', '')
    s3_path = folder.get('s3_path', '')
    artist = s3_path.split('/')[0] if s3_path and '/' in s3_path else ''
    tier = folder.get('tier', 'unknown')

    if i % 50 == 0:
        print(f"Analyzing {i}/{len(all_folders)}...")

    stats['total_folders'] += 1

    # Get file lists
    local_files = {}
    s3_files = {}

    # Scan local files
    local_folder = local_root / local_path if local_path else None
    if local_folder and local_folder.exists():
        for pdf_file in local_folder.glob('*.pdf'):
            local_files[pdf_file.name] = pdf_file.stat().st_size

    # Scan S3 files
    if s3_path:
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket, Prefix=f"{s3_path}/"):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if obj['Key'].endswith('.pdf'):
                            filename = obj['Key'].split('/')[-1]
                            s3_files[filename] = obj['Size']
        except Exception as e:
            stats['s3_scan_errors'] += 1

    # Analyze file differences
    file_decisions = {}

    all_filenames = set(local_files.keys()) | set(s3_files.keys())

    for filename in all_filenames:
        local_size = local_files.get(filename)
        s3_size = s3_files.get(filename)

        decision = {
            'filepath': filename,
            'local_path': local_path,
            's3_path': s3_path,
            'local_size': local_size,
            's3_size': s3_size
        }

        # Determine action
        if local_size and s3_size:
            # File exists in both
            if local_size == s3_size:
                decision['action'] = 'no-action'
                decision['reason'] = 'Files match'
                stats['files_match'] += 1
            elif local_size > s3_size:
                decision['action'] = 'copy-local-to-s3-overwrite'
                decision['reason'] = f'Local is larger ({local_size} > {s3_size})'
                stats['local_larger'] += 1
            else:
                decision['action'] = 'copy-s3-to-local-overwrite'
                decision['reason'] = f'S3 is larger ({s3_size} > {local_size})'
                stats['s3_larger'] += 1

        elif local_size and not s3_size:
            # Only in local
            decision['action'] = 'copy-local-to-s3'
            decision['reason'] = 'File only exists locally'
            stats['only_local'] += 1

        elif s3_size and not local_size:
            # Only in S3
            decision['action'] = 'copy-s3-to-local'
            decision['reason'] = 'File only exists in S3'
            stats['only_s3'] += 1

        else:
            # Shouldn't happen
            decision['action'] = 'error'
            decision['reason'] = 'File exists in neither location'
            stats['errors'] += 1

        file_decisions[filename] = decision

    # Store folder decision
    decisions[folder_key] = {
        'local_path': local_path,
        's3_path': s3_path,
        'artist': artist,
        'tier': tier,
        'file_count_local': len(local_files),
        'file_count_s3': len(s3_files),
        'fileDecisions': file_decisions
    }

    stats['total_file_decisions'] += len(file_decisions)

# Save recommendations
output_data = {
    'generated_at': '2026-02-02',
    'folder_count': len(decisions),
    'file_decision_count': stats['total_file_decisions'],
    'decisions': decisions
}

output_file = 'reconciliation_decisions_2026-02-02_fresh_generated.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

# Print summary
print(f"\n{'='*70}")
print("RECONCILIATION RECOMMENDATIONS GENERATED")
print(f"{'='*70}")
print(f"Folders analyzed:           {stats['total_folders']}")
print(f"Total file decisions:       {stats['total_file_decisions']}")
print()
print(f"File actions:")
print(f"  Files match (no action):  {stats['files_match']}")
print(f"  Copy local to S3:         {stats['only_local']}")
print(f"  Copy S3 to local:         {stats['only_s3']}")
print(f"  Local larger (to S3):     {stats['local_larger']}")
print(f"  S3 larger (to local):     {stats['s3_larger']}")
print(f"  Errors:                   {stats['errors']}")
print()
print(f"S3 scan errors:             {stats['s3_scan_errors']}")

print(f"\n{'='*70}")
print("OUTPUT")
print(f"{'='*70}")
print(f"Recommendations saved to: {output_file}")
print(f"\nYou can review these recommendations and then apply them.")
print("\nNext steps:")
print("  1. Review the recommendations")
print("  2. Update the HTML viewer with this data")
print("  3. Make any manual adjustments needed")
print("  4. Execute the decisions")

print("\nRecommendations generated!")
