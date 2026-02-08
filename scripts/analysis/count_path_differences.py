"""Count folders with different local/S3 paths"""
import json

print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r') as f:
    data = json.load(f)

# Get all folders with different paths
different_paths = []
for tier_name, folders in data['quality_tiers'].items():
    for folder in folders:
        local_path = folder.get('local_path', '')
        s3_path = folder.get('s3_path', '')
        if local_path and s3_path and local_path != s3_path:
            different_paths.append({
                'tier': tier_name,
                'local': local_path,
                's3': s3_path
            })

print(f"\nTotal folders with different paths: {len(different_paths)}\n")

# Show first 20
print("First 20 examples:")
print("=" * 80)
for i, folder in enumerate(different_paths[:20], 1):
    print(f"{i}. [{folder['tier'].upper()}]")
    print(f"   Local: {folder['local']}")
    print(f"   S3:    {folder['s3']}")
    print()
