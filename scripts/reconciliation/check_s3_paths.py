"""
Check actual S3 paths for folders that failed to rename
"""
import boto3
import json

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

# Load decisions to get the folders that need checking
with open('reconciliation_decisions_2026-02-01.json', 'r', encoding='utf-8') as f:
    root = json.load(f)

all_decisions = root['decisions']

# Check a few problem folders
problem_folders = [
    "Adele/19 [pvg Book]",
    "Billy Joel/Greatest Hits Vol Iii",
    "Billy Joel/Rock Score",
]

print("Checking S3 paths...\n")

for folder in problem_folders:
    prefix = f"output/{folder}"
    print(f"Looking for: {prefix}")

    # Try listing with this prefix
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=prefix,
            MaxKeys=5
        )

        if 'Contents' in response:
            print(f"  Found {response['KeyCount']} objects:")
            for obj in response['Contents'][:3]:
                print(f"    - {obj['Key']}")
        else:
            print(f"  No objects found")

            # Try searching for similar paths
            print(f"  Searching parent folder...")
            parent = '/'.join(folder.split('/')[:-1])
            parent_prefix = f"output/{parent}/"

            response = s3.list_objects_v2(
                Bucket=S3_BUCKET,
                Prefix=parent_prefix,
                Delimiter='/'
            )

            if 'CommonPrefixes' in response:
                print(f"  Found subfolders in {parent}:")
                for prefix_obj in response['CommonPrefixes']:
                    subfolder = prefix_obj['Prefix'].replace(parent_prefix, '').rstrip('/')
                    print(f"    - {subfolder}")

    except Exception as e:
        print(f"  ERROR: {e}")

    print()
