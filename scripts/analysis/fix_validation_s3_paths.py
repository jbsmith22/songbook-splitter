"""
Fix S3 paths in final_validation_data.json to match corrected manifest paths
"""
import json

# Load validation data
print("Loading validation data...")
with open('data/analysis/final_validation_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

matched = data['matched']
print(f"Found {len(matched)} matched folders")

# Fix S3 paths to match local paths (remove normalization)
fixed_count = 0
for match in matched:
    local_path = match['local_path']
    s3_path = match['s3_path']

    # S3 path should match local path exactly (both use underscores, etc.)
    if s3_path != local_path:
        match['s3_path'] = local_path
        fixed_count += 1
        print(f"  Fixed: {local_path}")
        print(f"    Old S3: {s3_path}")
        print(f"    New S3: {local_path}")

print(f"\n{'='*80}")
print(f"Fixed {fixed_count} S3 paths")
print(f"{'='*80}")

# Save updated validation data
print("\nSaving updated validation data...")
with open('data/analysis/final_validation_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)

print("Done! Re-run match quality analysis to see updated results.")
