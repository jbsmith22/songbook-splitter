"""
Comprehensive verification of ALL data stores for the 16 reprocessed books:
1. S3 artifacts (page_analysis.json, output_files.json)
2. S3 output PDFs
3. Local manifest.json files
4. Local PDF files
5. DynamoDB processing-ledger records
"""
import json
import boto3
from pathlib import Path
from datetime import datetime

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('jsmith-processing-ledger')

OUTPUT_BUCKET = 'jsmith-output'
FINAL_DIR = Path('ProcessedSongs_Final')

books = [
    {'book_id': 'v2-e32e7feb95c5dd5b-2', 'name': 'Aerosmith - Greatest Hits _Songbook_'},
    {'book_id': 'v2-b1c5d9e0b2c00cfa-2', 'name': 'Allman Brothers - Best Of _PVG_'},
    {'book_id': 'v2-10c9b38769bc4333-2', 'name': 'Barry Manilow - Anthology'},
    {'book_id': 'v2-ce9d957468e199fe-2', 'name': 'Barry Manilow - Barry Manilow _PVG Book_'},
    {'book_id': 'v2-ee63e83296645419-2', 'name': 'Beatles - 100 Hits For All Keyboards'},
    {'book_id': 'v2-504918da8c736ac3-2', 'name': 'Beatles - Essential Songs'},
    {'book_id': 'v2-b35285e7019e260e-2', 'name': 'Beatles - Singles Collection _PVG_'},
    {'book_id': 'v2-419995ff8edb29d6-2', 'name': 'Billy Joel - Complete Vol 1'},
    {'book_id': 'v2-dde323032f955172-2', 'name': 'Billy Joel - Greatest Hits'},
    {'book_id': 'v2-9a5487d438dc0e6a-2', 'name': 'Billy Joel - Greatest Hits Vol I And II'},
    {'book_id': 'v2-e1714150fcf3f966-2', 'name': 'Billy Joel - My Lives'},
    {'book_id': 'v2-e3d88bf7f64722be-2', 'name': 'Billy Joel - Songs In The Attic'},
    {'book_id': 'v2-d5a9286f0899e26e-2', 'name': 'Bob Seger - The New Best Of Bob Seger'},
    {'book_id': 'v2-09a39b6d0883b0a5-2', 'name': 'Bruce Springsteen - Greatest Hits'},
    {'book_id': 'v2-170195b568600092-2', 'name': 'Burl Ives - Song Book'},
    {'book_id': 'v2-1602c5f5f8f2ed15-2', 'name': 'Cole Porter - The Very Best Of Cole Porter'},
]


def main():
    print("=" * 100)
    print("COMPREHENSIVE VERIFICATION OF ALL DATA STORES")
    print("=" * 100)
    print(f"Checking: S3 artifacts, S3 PDFs, Local manifests, Local PDFs, DynamoDB")
    print("=" * 100)

    all_issues = []

    for book in books:
        book_id = book['book_id']
        book_name = book['name']
        artist = book_name.split(' - ')[0]
        issues = []

        print(f"\n{'-' * 100}")
        print(f"{book_name} [{book_id}]")
        print("-" * 100)

        # ========================================
        # 1. S3 ARTIFACTS
        # ========================================
        print("\n[1] S3 ARTIFACTS:")
        try:
            # output_files.json
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
            output_files = json.loads(obj['Body'].read()).get('output_files', [])
            s3_song_count = len(output_files)
            print(f"    output_files.json: {s3_song_count} songs [OK]")

            # page_analysis.json
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
            page_data = json.loads(obj['Body'].read())
            page_songs = page_data.get('songs', [])
            print(f"    page_analysis.json: {len(page_songs)} songs [OK]")

            if len(page_songs) != s3_song_count:
                issues.append(f"S3 artifact mismatch: page_analysis={len(page_songs)}, output_files={s3_song_count}")
        except Exception as e:
            issues.append(f"S3 artifacts error: {e}")
            s3_song_count = 0
            output_files = []

        # ========================================
        # 2. S3 OUTPUT PDFs
        # ========================================
        print("\n[2] S3 OUTPUT PDFs:")
        s3_pdfs_ok = 0
        s3_pdfs_missing = []
        for of in output_files:
            uri = of.get('output_uri', '')
            if uri.startswith(f's3://{OUTPUT_BUCKET}/'):
                key = uri.replace(f's3://{OUTPUT_BUCKET}/', '')
                try:
                    s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
                    s3_pdfs_ok += 1
                except:
                    s3_pdfs_missing.append(of.get('song_title', 'Unknown'))

        if s3_pdfs_missing:
            issues.append(f"Missing S3 PDFs: {s3_pdfs_missing}")
            print(f"    {s3_pdfs_ok}/{s3_song_count} PDFs exist [ERROR - {len(s3_pdfs_missing)} missing]")
        else:
            print(f"    {s3_pdfs_ok}/{s3_song_count} PDFs verified [OK]")

        # ========================================
        # 3. LOCAL MANIFEST
        # ========================================
        print("\n[3] LOCAL MANIFEST:")
        local_book_dir = FINAL_DIR / artist / book_name
        manifest_path = local_book_dir / 'manifest.json'

        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)
            manifest_songs = manifest.get('songs', [])
            manifest_count = len(manifest_songs)
            manifest_book_id = manifest.get('book_id', '')

            print(f"    manifest.json exists: {manifest_count} songs")

            if manifest_book_id != book_id:
                issues.append(f"Manifest book_id mismatch: {manifest_book_id} vs {book_id}")
                print(f"    book_id: {manifest_book_id} [ERROR - should be {book_id}]")
            else:
                print(f"    book_id: {manifest_book_id} [OK]")

            if manifest_count != s3_song_count:
                issues.append(f"Manifest count mismatch: {manifest_count} vs S3 {s3_song_count}")
                print(f"    count: {manifest_count} [ERROR - S3 has {s3_song_count}]")
            else:
                print(f"    count matches S3 [OK]")
        else:
            issues.append("Local manifest.json not found")
            print(f"    manifest.json NOT FOUND [ERROR]")

        # ========================================
        # 4. LOCAL PDFs
        # ========================================
        print("\n[4] LOCAL PDFs:")
        if local_book_dir.exists():
            local_pdfs = [f for f in local_book_dir.iterdir() if f.suffix.lower() == '.pdf']
            local_count = len(local_pdfs)

            if local_count == s3_song_count:
                print(f"    {local_count} PDFs [OK - matches S3]")
            else:
                issues.append(f"Local PDF count mismatch: {local_count} vs S3 {s3_song_count}")
                print(f"    {local_count} PDFs [ERROR - S3 has {s3_song_count}]")
        else:
            issues.append(f"Local folder not found: {local_book_dir}")
            print(f"    Folder NOT FOUND [ERROR]")

        # ========================================
        # 5. DYNAMODB RECORD
        # ========================================
        print("\n[5] DYNAMODB RECORD:")
        try:
            response = table.get_item(Key={'book_id': book_id})
            if 'Item' in response:
                item = response['Item']
                db_status = item.get('status', 'unknown')
                db_songs = int(item.get('songs_extracted', 0))
                db_artist = item.get('artist', '')
                db_book = item.get('book_name', '')

                print(f"    Record exists: status={db_status}, songs={db_songs}")

                if db_status != 'success':
                    issues.append(f"DynamoDB status is '{db_status}', not 'success'")
                    print(f"    status: {db_status} [WARN - should be 'success']")

                if db_songs != s3_song_count:
                    issues.append(f"DynamoDB song count mismatch: {db_songs} vs S3 {s3_song_count}")
                    print(f"    songs_extracted: {db_songs} [ERROR - S3 has {s3_song_count}]")
                else:
                    print(f"    songs_extracted matches S3 [OK]")
            else:
                issues.append("DynamoDB record not found")
                print(f"    Record NOT FOUND [WARN - may need to create]")
        except Exception as e:
            issues.append(f"DynamoDB error: {e}")
            print(f"    Error: {e}")

        # ========================================
        # SUMMARY FOR THIS BOOK
        # ========================================
        if issues:
            print(f"\n[RESULT] {len(issues)} ISSUES:")
            for issue in issues:
                print(f"  - {issue}")
            all_issues.append({'book': book_name, 'book_id': book_id, 'issues': issues})
        else:
            print(f"\n[RESULT] ALL DATA STORES VERIFIED [OK]")

    # ========================================
    # FINAL SUMMARY
    # ========================================
    print("\n\n" + "=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    print(f"Books verified: 16")
    print(f"Books with issues: {len(all_issues)}")

    if all_issues:
        print("\n" + "-" * 100)
        print("ISSUES BY BOOK:")
        print("-" * 100)
        for item in all_issues:
            print(f"\n{item['book']}:")
            for issue in item['issues']:
                print(f"  - {issue}")
    else:
        print("\n" + "*" * 100)
        print("*** ALL DATA STORES VERIFIED - 100% CONSISTENCY ***")
        print("*" * 100)


if __name__ == '__main__':
    main()
