"""
Fix folder names in _broadway Shows and _movie And Tv categories
to ensure they follow the pattern: Various Artists - <title>
or <composer> - <title>
"""
import json
import shutil
import boto3
from pathlib import Path
from collections import defaultdict

archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
BUCKET = 'jsmith-output'
TABLE = dynamodb.Table('jsmith-processing-ledger')

print('Analyzing category folder names...\n')

# Categories to check
categories = ['_broadway Shows', '_movie And Tv']

# Known composer patterns (case-insensitive)
composer_patterns = [
    'john williams', 'lerner and loewe', 'rogers and hammerstein',
    'steven sondheim', 'lambert and morrison', 'kasha and hirschorn',
    'randy newman', 'budget books'
]

folders_to_rename = []

for category in categories:
    category_path = archive_root / category
    if not category_path.exists():
        continue

    print(f'Checking {category}/...')
    for folder in sorted(category_path.iterdir()):
        if not folder.is_dir():
            continue

        folder_name = folder.name

        # Check if it already has a proper prefix
        has_artist_prefix = ' - ' in folder_name

        if not has_artist_prefix:
            # Needs "Various Artists - " prefix
            new_name = f"Various Artists - {folder_name}"
            folders_to_rename.append({
                'category': category,
                'old_name': folder_name,
                'new_name': new_name,
                'old_path': f"{category}/{folder_name}",
                'new_path': f"{category}/{new_name}"
            })
            print(f'  RENAME: {folder_name}')
            print(f'       -> {new_name}')

print(f'\nFound {len(folders_to_rename)} folders to rename\n')

if len(folders_to_rename) == 0:
    print('All folders already have correct naming!')
    exit(0)

# Save rename plan
with open('data/analysis/category_folder_renames.json', 'w', encoding='utf-8') as f:
    json.dump(folders_to_rename, f, indent=2)

print(f'Rename plan saved to: data/analysis/category_folder_renames.json')
print('Run with --execute flag to perform renames')
