"""
Analyze what's in the output bucket and what you actually need.
"""

import boto3
from collections import defaultdict

OUTPUT_BUCKET = 'jsmith-output'


def analyze_output_bucket():
    """Analyze output bucket contents."""
    s3 = boto3.client('s3')
    
    print("=" * 80)
    print("S3 Output Bucket Analysis")
    print("=" * 80)
    
    print("\nListing all objects (this may take a minute)...")
    
    objects = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET):
        if 'Contents' in page:
            objects.extend(page['Contents'])
    
    print(f"Total objects: {len(objects)}")
    
    # Categorize objects
    categories = defaultdict(list)
    
    for obj in objects:
        key = obj['Key']
        
        if key.startswith('artifacts/'):
            # Processing artifacts
            if key.endswith('toc_discovery.json'):
                categories['artifacts_toc_discovery'].append(obj)
            elif key.endswith('toc_parse.json'):
                categories['artifacts_toc_parse'].append(obj)
            elif key.endswith('page_mapping.json'):
                categories['artifacts_page_mapping'].append(obj)
            elif key.endswith('verified_songs.json'):
                categories['artifacts_verified_songs'].append(obj)
            elif key.endswith('output_files.json'):
                categories['artifacts_output_files'].append(obj)
            else:
                categories['artifacts_other'].append(obj)
        
        elif key.endswith('manifest.json'):
            categories['manifests'].append(obj)
        
        elif key.endswith('.pdf'):
            categories['song_pdfs'].append(obj)
        
        elif key.startswith('s3:/'):
            categories['path_duplication_bug'].append(obj)
        
        elif key.startswith('output/'):
            categories['output_folder'].append(obj)
        
        else:
            categories['other'].append(obj)
    
    # Print summary
    print("\n" + "=" * 80)
    print("BUCKET CONTENTS BREAKDOWN")
    print("=" * 80)
    
    for category, items in sorted(categories.items()):
        total_size = sum(obj['Size'] for obj in items)
        size_mb = total_size / (1024 * 1024)
        print(f"\n{category}:")
        print(f"  Count: {len(items)}")
        print(f"  Size: {size_mb:.2f} MB")
        
        if len(items) <= 5:
            print(f"  Files:")
            for obj in items[:5]:
                print(f"    - {obj['Key']}")
    
    # Calculate totals
    total_size = sum(obj['Size'] for obj in objects)
    total_gb = total_size / (1024 * 1024 * 1024)
    
    print("\n" + "=" * 80)
    print("TOTAL STORAGE")
    print("=" * 80)
    print(f"  Total objects: {len(objects)}")
    print(f"  Total size: {total_gb:.2f} GB")
    print(f"  Monthly cost: ${total_gb * 0.023:.2f}")
    
    # Analysis
    print("\n" + "=" * 80)
    print("WHAT DO YOU ACTUALLY NEED?")
    print("=" * 80)
    
    print("\n1. SONG PDFs (Final Outputs)")
    print(f"   Count: {len(categories['song_pdfs'])}")
    print(f"   Size: {sum(obj['Size'] for obj in categories['song_pdfs']) / (1024**3):.2f} GB")
    print("   Status: ✓ KEEP - These are your final outputs")
    print("   Local: Already downloaded to ProcessedSongs/")
    
    print("\n2. MANIFESTS (Metadata)")
    print(f"   Count: {len(categories['manifests'])}")
    print(f"   Size: {sum(obj['Size'] for obj in categories['manifests']) / (1024**2):.2f} MB")
    print("   Status: ✓ KEEP - Contains processing metadata")
    print("   Local: Not downloaded (should you?)")
    
    print("\n3. ARTIFACTS (Processing Data)")
    artifact_count = sum(len(v) for k, v in categories.items() if k.startswith('artifacts_'))
    artifact_size = sum(sum(obj['Size'] for obj in v) for k, v in categories.items() if k.startswith('artifacts_'))
    print(f"   Count: {artifact_count}")
    print(f"   Size: {artifact_size / (1024**2):.2f} MB")
    print("   Status: ? OPTIONAL - Only needed for debugging/reprocessing")
    print("   Local: Not downloaded")
    print("   Breakdown:")
    for k, v in sorted(categories.items()):
        if k.startswith('artifacts_'):
            print(f"     - {k}: {len(v)} files")
    
    print("\n4. PATH DUPLICATION BUG")
    if categories['path_duplication_bug']:
        print(f"   Count: {len(categories['path_duplication_bug'])}")
        print(f"   Size: {sum(obj['Size'] for obj in categories['path_duplication_bug']) / (1024**2):.2f} MB")
        print("   Status: ✗ DELETE - These are duplicates/errors")
    else:
        print("   Count: 0 (no issues found)")
    
    print("\n5. OUTPUT FOLDER")
    if categories['output_folder']:
        print(f"   Count: {len(categories['output_folder'])}")
        print(f"   Size: {sum(obj['Size'] for obj in categories['output_folder']) / (1024**2):.2f} MB")
        print("   Status: ? INVESTIGATE - Unknown purpose")
    else:
        print("   Count: 0 (no issues found)")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    
    print("\nOption A: KEEP EVERYTHING (Safest)")
    print("  - Keep all song PDFs, manifests, and artifacts")
    print("  - Cost: Current (~${:.2f}/month)".format(total_gb * 0.023))
    print("  - Benefit: Can debug/reprocess anytime")
    
    print("\nOption B: KEEP OUTPUTS + MANIFESTS (Recommended)")
    print("  - Keep song PDFs and manifests")
    print("  - Delete artifacts (can regenerate if needed)")
    print("  - Cost: ~${:.2f}/month".format((sum(obj['Size'] for obj in categories['song_pdfs']) + sum(obj['Size'] for obj in categories['manifests'])) / (1024**3) * 0.023))
    print("  - Benefit: Saves space, keeps important data")
    
    print("\nOption C: KEEP ONLY OUTPUTS (Minimal)")
    print("  - Keep only song PDFs")
    print("  - Delete manifests and artifacts")
    print("  - Cost: ~${:.2f}/month".format(sum(obj['Size'] for obj in categories['song_pdfs']) / (1024**3) * 0.023))
    print("  - Benefit: Minimal storage, but loses metadata")
    
    print("\nOption D: SYNC TO LOCAL + DELETE (Most Aggressive)")
    print("  - Download everything to local")
    print("  - Delete entire output bucket")
    print("  - Cost: $0.00/month")
    print("  - Benefit: No cloud costs, but no cloud backup")
    
    print("\n" + "=" * 80)
    print("MY RECOMMENDATION")
    print("=" * 80)
    print("\nOption B: Keep outputs + manifests, delete artifacts")
    print("\nWhy:")
    print("  1. Song PDFs are your final product (already local)")
    print("  2. Manifests contain useful metadata (small, worth keeping)")
    print("  3. Artifacts are debug data (can regenerate if needed)")
    print("  4. Saves ~50% storage costs")
    print("  5. Keeps cloud backup of final outputs")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    analyze_output_bucket()
