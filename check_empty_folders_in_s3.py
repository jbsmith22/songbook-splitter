"""Check if the 11 empty local folders exist in S3."""
import boto3

empty_folders = [
    ('Crosby Stills And Nash', 'Crosby Stills Nash And Young - The Guitar Collection'),
    ('Dire Straits', 'Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_'),
    ('Elvis Presley', 'Elvis Presley - The Compleat _PVG Book_'),
    ('Eric Clapton', 'Eric Clapton - The Cream Of Clapton'),
    ('Mamas and the Papas', 'Mamas And The Papas - Songbook _PVG_'),
    ('Night Ranger', 'Night Ranger - Seven Wishes _Jap Score_'),
    ('Robbie Robertson', 'Robbie Robertson - Songbook _Guitar Tab_'),
    ('Various Artists', 'Various Artists - Ultimate 80s Songs'),
    ('_broadway Shows', 'Various Artists - 25th Annual Putnam County Spelling Bee'),
    ('_broadway Shows', 'Various Artists - Little Shop Of Horrors Script'),
    ('_movie And Tv', 'Various Artists - Complete TV And Film'),
]

s3 = boto3.client('s3', region_name='us-east-1')

print('CHECKING EMPTY FOLDERS IN S3')
print('='*80)

# First, get all S3 folders
print('Fetching all S3 folders...')
s3_folders = {}
paginator = s3.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket='jsmith-output'):
    if 'Contents' not in page:
        continue
    
    for obj in page['Contents']:
        key = obj['Key']
        
        if not key.endswith('.pdf'):
            continue
        
        if key.startswith('artifacts/') or key.startswith('s3:/'):
            continue
        
        parts = key.split('/')
        if len(parts) >= 3:
            artist = parts[0]
            book = parts[1]
            folder_key = f"{artist}|||{book}"
            
            if folder_key not in s3_folders:
                s3_folders[folder_key] = []
            s3_folders[folder_key].append(key)

print(f'Found {len(s3_folders)} unique S3 folders\n')

# Check each empty folder
for local_artist, local_book in empty_folders:
    print(f'{local_artist} / {local_book}')
    
    # Look for exact match
    exact_key = f"{local_artist}|||{local_book}"
    if exact_key in s3_folders:
        print(f'  ✓ FOUND EXACT MATCH in S3')
        print(f'    Files: {len(s3_folders[exact_key])}')
        for file in s3_folders[exact_key][:3]:
            print(f'      - {file}')
        if len(s3_folders[exact_key]) > 3:
            print(f'      ... and {len(s3_folders[exact_key]) - 3} more')
    else:
        # Look for similar matches
        found_similar = False
        for s3_key, files in s3_folders.items():
            s3_artist, s3_book = s3_key.split('|||')
            
            # Check if artist matches (case-insensitive)
            if s3_artist.lower() == local_artist.lower():
                if not found_similar:
                    print(f'  ✗ No exact match, but found other {local_artist} folders:')
                    found_similar = True
                print(f'    - {s3_book} ({len(files)} files)')
        
        if not found_similar:
            print(f'  ✗ NOT FOUND in S3 (no folders for {local_artist})')
    
    print()

# Special check for Mamas and Papas variations
print('='*80)
print('SPECIAL CHECK: All "Mamas" folders in S3')
print('='*80)
for s3_key, files in s3_folders.items():
    s3_artist, s3_book = s3_key.split('|||')
    if 'mamas' in s3_artist.lower():
        print(f'{s3_artist} / {s3_book} ({len(files)} files)')
