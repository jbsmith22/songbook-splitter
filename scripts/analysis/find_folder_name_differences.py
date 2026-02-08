"""
Find folders where local and S3 names differ and generate rename decisions
"""
import json
from pathlib import Path
from collections import defaultdict

print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    match_data = json.load(f)

all_folders = []
for tier_name, tier_folders in match_data['quality_tiers'].items():
    all_folders.extend(tier_folders)

print(f"Analyzing {len(all_folders)} folders for naming differences...\n")

naming_differences = []
stats = defaultdict(int)

for folder in all_folders:
    local_path = folder.get('local_path', '')
    s3_path = folder.get('s3_path', '')
    tier = folder.get('tier', '')

    if not local_path or not s3_path:
        continue

    # Normalize for comparison (remove common variations)
    local_normalized = local_path.replace('_', ' ').replace('[', '').replace(']', '').lower()
    s3_normalized = s3_path.replace('_', ' ').replace('[', '').replace(']', '').lower()

    # If they're different (even after normalization), record it
    if local_path != s3_path:
        stats['total_differences'] += 1

        # Categorize the difference
        difference_type = []

        if local_path.lower() != s3_path.lower():
            difference_type.append('case_different')
            stats['case_different'] += 1

        if '[' in local_path or '[' in s3_path:
            if local_path.replace('[', '_').replace(']', '_') == s3_path or \
               s3_path.replace('[', '_').replace(']', '_') == local_path:
                difference_type.append('bracket_style')
                stats['bracket_style'] += 1

        if '_' in local_path or '_' in s3_path:
            if local_path.replace('_', ' ') == s3_path or \
               s3_path.replace('_', ' ') == local_path:
                difference_type.append('underscore_vs_space')
                stats['underscore_vs_space'] += 1

        if not difference_type:
            difference_type.append('other')
            stats['other_differences'] += 1

        naming_differences.append({
            'local_path': local_path,
            's3_path': s3_path,
            'tier': tier,
            'difference_types': difference_type,
            'local_artist': local_path.split('/')[0] if '/' in local_path else '',
            's3_artist': s3_path.split('/')[0] if '/' in s3_path else '',
            'local_album': '/'.join(local_path.split('/')[1:]) if '/' in local_path else local_path,
            's3_album': '/'.join(s3_path.split('/')[1:]) if '/' in s3_path else s3_path,
        })

# Sort by tier (PERFECT first) then by artist
tier_order = {'perfect': 0, 'excellent': 1, 'good': 2, 'fair': 3, 'weak': 4, 'poor': 5}
naming_differences.sort(key=lambda x: (tier_order.get(x['tier'], 999), x['local_path']))

# Save full data
output_data = {
    'total_folders': len(all_folders),
    'folders_with_differences': len(naming_differences),
    'statistics': dict(stats),
    'differences': naming_differences
}

output_file = 'data/analysis/folder_naming_differences.json'
with open(output_file, 'w') as f:
    json.dump(output_data, f, indent=2)

# Print summary
print(f"{'='*70}")
print("FOLDER NAMING DIFFERENCES FOUND")
print(f"{'='*70}")
print(f"Total folders analyzed:       {len(all_folders)}")
print(f"Folders with differences:     {len(naming_differences)}")
print()
print("Difference types:")
print(f"  Case differences:           {stats['case_different']}")
print(f"  Bracket style [vs _]:       {stats['bracket_style']}")
print(f"  Underscore vs space:        {stats['underscore_vs_space']}")
print(f"  Other differences:          {stats['other_differences']}")

# Show examples
if naming_differences:
    print(f"\n{'='*70}")
    print("EXAMPLES (first 10)")
    print(f"{'='*70}")

    for i, diff in enumerate(naming_differences[:10], 1):
        print(f"\n{i}. {diff['tier'].upper()}")
        print(f"   Local: {diff['local_path']}")
        print(f"   S3:    {diff['s3_path']}")
        print(f"   Types: {', '.join(diff['difference_types'])}")

print(f"\n{'='*70}")
print("OUTPUT")
print(f"{'='*70}")
print(f"Full data saved to: {output_file}")
print()
print("Next steps:")
print("  1. Review the differences in the JSON file")
print("  2. Create rename decisions for folders you want to standardize")
print("  3. Execute the renames to keep consistent naming")
