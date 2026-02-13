#!/usr/bin/env python3
"""
Fix Various Artists song filenames to use the actual performing artist.
Updates verified_songs.json, output_files.json, renames local + S3 files.
"""

import json
import sys
from pathlib import Path

import boto3

sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'

S3_ARTIFACTS_BUCKET = 'jsmith-artifacts'
S3_OUTPUT_BUCKET = 'jsmith-output'

INVALID_CHARS = '?"<>|*'

# Artist mappings by book: { book_name: { song_title_upper: artist_name } }
ARTIST_DATA = {
    "Classic Rock 73 Songs": {
        "ALONE": "Heart",
        "BABY, I LOVE YOUR WAY": "Peter Frampton",
        "AUTHORITY SONG": "John Mellencamp",
        "BABA O'RILEY": "The Who",
        "BACK IN THE U.S.S.R.": "The Beatles",
        "BADGE": "Cream",
        "BALLROOM BLITZ": "Sweet",
        "BETH": "Kiss",
        "BROWN EYED GIRL": "Van Morrison",
        "BLAZE OF GLORY": "Jon Bon Jovi",
        "BURNING LOVE": "Elvis Presley",
        "CALL ME THE BREEZE": "Lynyrd Skynyrd",
        "COME SAIL AWAY": "Styx",
        "COME TOGETHER": "The Beatles",
        "DON'T DO ME LIKE THAT": "Tom Petty & The Heartbreakers",
        "DAY TRIPPER": "The Beatles",
        "DON'T FEAR THE REAPER": "Blue Oyster Cult",
        "DON'T LOOK BACK IN ANGER": "Oasis",
        "DON'T STAND SO CLOSE TO ME": "The Police",
        "DON'T STOP": "Fleetwood Mac",
        "DREAM ON": "Aerosmith",
        "DREAMER": "Supertramp",
        "DRIVE MY CAR": "The Beatles",
        "EVERY BREATH YOU TAKE": "The Police",
        "EYE IN THE SKY": "Alan Parsons Project",
        "GIVE A LITTLE BIT": "Supertramp",
        "FAITHFULLY": "Journey",
        "FOOLS GOLD": "The Stone Roses",
        "FREE BIRD": "Lynyrd Skynyrd",
        "GLORIA": "Them",
        "GOODBYE YELLOW BRICK ROAD": "Elton John",
        "GREEN-EYED LADY": "Sugarloaf",
        "HEART AND SOUL": "Huey Lewis & The News",
        "HEAT OF THE MOMENT": "Asia",
        "HEAVEN": "Bryan Adams",
        "I FEEL FINE": "The Beatles",
        "IF YOU LEAVE ME NOW": "Chicago",
        "I WANT TO KNOW WHAT LOVE IS": "Foreigner",
        "IN THE SUMMERTIME": "Mungo Jerry",
        "LIKE A ROLLING STONE": "Bob Dylan",
        "IT'S ONLY LOVE": "Bryan Adams",
        "THE JOKER": "Steve Miller Band",
        "THE LOVECATS": "The Cure",
        "MATTHEW AND SON": "Cat Stevens",
        "OLIVER'S ARMY": "Elvis Costello & The Attractions",
        "PAPERBACK WRITER": "The Beatles",
        "PENNY LANE": "The Beatles",
        "RENEGADE": "Styx",
        "PICTURES OF LILY": "The Who",
        "PINK HOUSES": "John Mellencamp",
        "RADAR LOVE": "Golden Earring",
        "RHIANNON": "Fleetwood Mac",
        "RIDERS ON THE STORM": "The Doors",
        "ROCK 'N' ROLL STAR": "Oasis",
        "SHOW ME THE WAY": "Peter Frampton",
        "ROXANNE": "The Police",
        "RUNNING ON FAITH": "Eric Clapton",
        "SHAKEDOWN": "Bob Seger",
        "(SHE'S) SOME KIND OF WONDERFUL": "Grand Funk Railroad",
        "SOMETHING IN THE AIR": "Thunderclap Newman",
        "SUMMER OF '69": "Bryan Adams",
        "THROWING IT ALL AWAY": "Genesis",
        "SWEET EMOTION": "Aerosmith",
        "TAKIN' CARE OF BUSINESS": "Bachman-Turner Overdrive",
        "THESE EYES": "The Guess Who",
        "TIME FOR ME TO FLY": "Reo Speedwagon",
        "TWO OUT OF THREE AIN'T BAD": "Meat Loaf",
        "WALK OF LIFE": "Dire Straits",
        "THE WEIGHT": "The Band",
        "YOU REALLY GOT ME": "The Kinks",
        "YOU'RE THE DEVIL IN DISGUISE": "Elvis Presley",
    },
}


def safe_filename(title, artist):
    """Build a safe filename from title and artist."""
    safe = title
    for ch in '/\\:' + INVALID_CHARS:
        safe = safe.replace(ch, '-' if ch in '/\\:' else '')
    return f'{artist} - {safe}.pdf'


def find_s3_file(s3, bucket, prefix, search_term):
    """Find an S3 file by partial name match."""
    paginator = s3.get_paginator('list_objects_v2')
    search_lower = search_term.lower()
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get('Contents', []):
            if search_lower in obj['Key'].lower():
                return obj['Key']
    return None


def process_book(book_name, artist_map, s3, dry_run):
    """Process a single Various Artists book."""
    book_dir = ARTIFACTS_DIR / 'Various Artists' / book_name
    of_path = book_dir / 'output_files.json'
    vs_path = book_dir / 'verified_songs.json'

    if not of_path.exists():
        print(f'  SKIP: {book_name} - no output_files.json')
        return 0

    with open(of_path) as f:
        of_data = json.load(f)
    with open(vs_path) as f:
        vs_data = json.load(f)

    output_dir = OUTPUT_DIR / 'Various Artists' / book_name
    prefix = f'v3/Various Artists/{book_name}/'
    fixes = 0

    for i, entry in enumerate(of_data.get('output_files', [])):
        title = entry['song_title']
        old_artist = entry.get('artist', 'Various Artists')

        # Look up new artist (case-insensitive match)
        new_artist = artist_map.get(title.upper())
        if not new_artist or new_artist == old_artist:
            continue

        old_filename = safe_filename(title, old_artist)
        new_filename = safe_filename(title, new_artist)
        old_s3_key = f'{prefix}{old_filename}'
        new_s3_key = f'{prefix}{new_filename}'
        new_uri = f's3://{S3_OUTPUT_BUCKET}/{new_s3_key}'

        print(f'  [{i}] "{title}": {old_artist} -> {new_artist}')
        print(f'       {old_filename} -> {new_filename}')

        if not dry_run:
            # Update metadata
            entry['artist'] = new_artist
            entry['output_uri'] = new_uri
            if i < len(vs_data.get('verified_songs', [])):
                vs_data['verified_songs'][i]['artist'] = new_artist

            # Rename S3 file
            try:
                s3.copy_object(
                    Bucket=S3_OUTPUT_BUCKET,
                    Key=new_s3_key,
                    CopySource={'Bucket': S3_OUTPUT_BUCKET, 'Key': old_s3_key},
                )
                s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=old_s3_key)
                print(f'       S3: OK')
            except Exception as e:
                print(f'       S3 direct failed, searching...')
                # Search for file with song title
                found = find_s3_file(s3, S3_OUTPUT_BUCKET, prefix, title[:20])
                if found and found != new_s3_key:
                    s3.copy_object(
                        Bucket=S3_OUTPUT_BUCKET,
                        Key=new_s3_key,
                        CopySource={'Bucket': S3_OUTPUT_BUCKET, 'Key': found},
                    )
                    s3.delete_object(Bucket=S3_OUTPUT_BUCKET, Key=found)
                    print(f'       S3: found as "{found.split("/")[-1]}", renamed')
                elif found:
                    print(f'       S3: already correct')
                else:
                    print(f'       S3: NOT FOUND')

            # Rename local file
            old_local = output_dir / old_filename
            new_local = output_dir / new_filename
            if old_local.exists():
                old_local.rename(new_local)
                entry['file_size_bytes'] = new_local.stat().st_size
                print(f'       Local: OK')
            elif new_local.exists():
                print(f'       Local: already correct')
            else:
                print(f'       Local: NOT FOUND')

        fixes += 1

    if fixes > 0 and not dry_run:
        with open(of_path, 'w', encoding='utf-8') as f:
            json.dump(of_data, f, indent=2, ensure_ascii=False)
        with open(vs_path, 'w', encoding='utf-8') as f:
            json.dump(vs_data, f, indent=2, ensure_ascii=False)
        for name in ['output_files.json', 'verified_songs.json']:
            s3.upload_file(
                str(book_dir / name),
                S3_ARTIFACTS_BUCKET,
                f'v3/Various Artists/{book_name}/{name}',
            )
        print(f'  Artifacts uploaded')

    return fixes


def main():
    dry_run = '--dry-run' in sys.argv
    mode = 'DRY RUN' if dry_run else 'LIVE'

    print(f'FIX VARIOUS ARTISTS PERFORMING ARTISTS ({mode})')
    print('=' * 70)

    s3 = boto3.client('s3', region_name='us-east-1')
    total = 0

    for book_name, artist_map in sorted(ARTIST_DATA.items()):
        print(f'\n{book_name}:')
        fixes = process_book(book_name, artist_map, s3, dry_run)
        total += fixes
        print(f'  {fixes} songs updated')

    print(f'\n{"=" * 70}')
    print(f'Total artist fixes: {total}')
    print(f'{"=" * 70}')


if __name__ == '__main__':
    main()
