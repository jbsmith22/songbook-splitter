"""
Analyze archived folder names and identify ones that need to be renamed
to follow the correct pattern: <artist>\<artist> - <songbook name>\
"""
import json
from pathlib import Path
from collections import defaultdict

archive_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs_Archive')

print('Analyzing archived folder structure...\n')

# Scan all folders
all_folders = []
for artist_dir in archive_root.iterdir():
    if not artist_dir.is_dir():
        continue

    for songbook_dir in artist_dir.iterdir():
        if not songbook_dir.is_dir():
            continue

        relative_path = songbook_dir.relative_to(archive_root).as_posix()
        all_folders.append({
            'artist_dir': artist_dir.name,
            'songbook_dir': songbook_dir.name,
            'full_path': relative_path
        })

print(f'Found {len(all_folders)} archived songbook folders\n')

# Check each folder against the naming pattern
issues = []

for folder in all_folders:
    artist = folder['artist_dir']
    songbook = folder['songbook_dir']

    # Check if songbook starts with artist name followed by " - "
    expected_prefix = f"{artist} - "

    if not songbook.startswith(expected_prefix):
        issues.append({
            'current_path': folder['full_path'],
            'artist_dir': artist,
            'songbook_dir': songbook,
            'issue': 'missing_artist_prefix',
            'expected_prefix': expected_prefix
        })

print(f'Found {len(issues)} folders with naming issues\n')

# Categorize issues
by_artist = defaultdict(list)
for issue in issues:
    by_artist[issue['artist_dir']].append(issue)

print(f'{"="*80}')
print('FOLDERS NEEDING RENAME')
print(f'{"="*80}\n')

for artist in sorted(by_artist.keys()):
    issue_list = by_artist[artist]
    print(f'{artist}/ ({len(issue_list)} folders)')
    for issue in issue_list[:5]:  # Show first 5
        print(f'  Current: {issue["songbook_dir"]}')
        print(f'  Should be: {issue["expected_prefix"]}...')
        print()
    if len(issue_list) > 5:
        print(f'  ... and {len(issue_list) - 5} more\n')

# Special analysis for _broadway Shows and _movie And Tv
print(f'\n{"="*80}')
print('SPECIAL CATEGORIES (_broadway Shows, _movie And Tv)')
print(f'{"="*80}\n')

special_categories = ['_broadway Shows', '_movie And Tv']
for category in special_categories:
    folders_in_category = [f for f in all_folders if f['artist_dir'] == category]
    if folders_in_category:
        print(f'{category}/ ({len(folders_in_category)} folders)')
        print('These should be reorganized by actual artist:')
        print('  - Various Artists compilations → Various Artists/')
        print('  - Named composers → <composer>/')
        print()

# Save issues to JSON for processing
with open('data/analysis/archive_naming_issues.json', 'w', encoding='utf-8') as f:
    json.dump({
        'total_folders': len(all_folders),
        'issues_count': len(issues),
        'issues': issues
    }, f, indent=2)

print(f'Full analysis saved to: data/analysis/archive_naming_issues.json')
