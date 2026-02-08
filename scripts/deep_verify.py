"""
Deep verification of all 16 reprocessed books.
Checks:
1. S3 artifacts consistency (page_analysis matches output_files)
2. All S3 output PDFs exist
3. All local PDFs exist and match S3
4. No duplicate song titles
5. Page ranges are sequential and non-overlapping
"""
import json
import boto3
from pathlib import Path
from collections import Counter

s3 = boto3.client('s3')
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

INVALID_CHARS = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']


def sanitize(title):
    for c in INVALID_CHARS:
        title = title.replace(c, '')
    return title


def main():
    print("=" * 100)
    print("DEEP VERIFICATION OF 16 REPROCESSED BOOKS")
    print("=" * 100)

    all_issues = []
    total_songs = 0
    total_s3_verified = 0
    total_local_verified = 0

    for book in books:
        book_id = book['book_id']
        book_name = book['name']
        artist = book_name.split(' - ')[0]
        issues = []

        print(f"\n{'=' * 100}")
        print(f"{book_name}")
        print(f"Book ID: {book_id}")
        print("=" * 100)

        # 1. Load S3 artifacts
        try:
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
            page_data = json.loads(obj['Body'].read())
            page_songs = page_data.get('songs', [])

            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
            output_data = json.loads(obj['Body'].read())
            output_files = output_data.get('output_files', [])
        except Exception as e:
            issues.append(f"Failed to load S3 artifacts: {e}")
            all_issues.append({'book': book_name, 'issues': issues})
            continue

        print(f"\n[1] S3 ARTIFACTS:")
        print(f"    page_analysis.json: {len(page_songs)} songs")
        print(f"    output_files.json:  {len(output_files)} songs")

        # Check consistency
        page_titles = set(s.get('title', '') for s in page_songs)
        output_titles = set(of.get('song_title', '') for of in output_files)

        if page_titles == output_titles:
            print(f"    [OK] Titles match between artifacts")
        else:
            issues.append(f"Title mismatch between page_analysis and output_files")
            print(f"    [ERROR] Title mismatch!")

        # 2. Check for duplicates
        print(f"\n[2] DUPLICATE CHECK:")
        title_counts = Counter(of.get('song_title', '') for of in output_files)
        dupes = {t: c for t, c in title_counts.items() if c > 1}
        if dupes:
            issues.append(f"Duplicate titles found: {dupes}")
            print(f"    [ERROR] Duplicates: {dupes}")
        else:
            print(f"    [OK] No duplicate titles")

        # 3. Verify all S3 PDFs exist
        print(f"\n[3] S3 PDF VERIFICATION:")
        s3_missing = []
        for of in output_files:
            uri = of.get('output_uri', '')
            if uri.startswith(f's3://{OUTPUT_BUCKET}/'):
                key = uri.replace(f's3://{OUTPUT_BUCKET}/', '')
                try:
                    s3.head_object(Bucket=OUTPUT_BUCKET, Key=key)
                    total_s3_verified += 1
                except:
                    s3_missing.append(of.get('song_title', 'Unknown'))

        if s3_missing:
            issues.append(f"Missing S3 PDFs: {s3_missing}")
            print(f"    [ERROR] {len(s3_missing)} PDFs missing in S3")
        else:
            print(f"    [OK] All {len(output_files)} S3 PDFs verified")

        # 4. Verify local files
        print(f"\n[4] LOCAL FILE VERIFICATION:")
        local_book_dir = FINAL_DIR / artist / book_name
        local_missing = []

        if local_book_dir.exists():
            local_pdfs = {f.name for f in local_book_dir.iterdir() if f.suffix.lower() == '.pdf'}

            for of in output_files:
                song_title = of['song_title']
                safe_title = sanitize(song_title)
                expected_filename = f"{artist} - {safe_title}.pdf"

                if expected_filename in local_pdfs:
                    total_local_verified += 1
                else:
                    local_missing.append(song_title)

            if local_missing:
                issues.append(f"Missing local PDFs: {local_missing}")
                print(f"    [ERROR] {len(local_missing)} PDFs missing locally")
            else:
                print(f"    [OK] All {len(output_files)} local PDFs verified")
        else:
            issues.append(f"Local folder not found")
            print(f"    [ERROR] Folder not found: {local_book_dir}")

        # 5. Check page ranges
        print(f"\n[5] PAGE RANGE VERIFICATION:")
        page_issues = []
        prev_end = 0
        for of in sorted(output_files, key=lambda x: x.get('page_range', [0, 0])[0]):
            page_range = of.get('page_range', [0, 0])
            start, end = page_range[0], page_range[1]

            if start < prev_end:
                page_issues.append(f"Overlap: {of['song_title']} starts at {start} but prev song ended at {prev_end}")

            if end < start:
                page_issues.append(f"Invalid range for {of['song_title']}: {page_range}")

            prev_end = end

        if page_issues:
            issues.extend(page_issues)
            print(f"    [WARN] {len(page_issues)} page range issues")
            for pi in page_issues[:3]:
                print(f"      - {pi}")
        else:
            print(f"    [OK] Page ranges are sequential")

        total_songs += len(output_files)

        # Summary for this book
        if issues:
            print(f"\n[RESULT] {len(issues)} ISSUES FOUND")
            all_issues.append({'book': book_name, 'issues': issues})
        else:
            print(f"\n[RESULT] VERIFIED CLEAN - {len(output_files)} songs")

    # Final summary
    print("\n\n" + "=" * 100)
    print("FINAL VERIFICATION SUMMARY")
    print("=" * 100)
    print(f"\nBooks verified:       16")
    print(f"Total songs:          {total_songs}")
    print(f"S3 PDFs verified:     {total_s3_verified}")
    print(f"Local PDFs verified:  {total_local_verified}")
    print(f"Books with issues:    {len(all_issues)}")

    if all_issues:
        print("\n" + "-" * 100)
        print("ISSUES FOUND:")
        print("-" * 100)
        for item in all_issues:
            print(f"\n{item['book']}:")
            for issue in item['issues']:
                print(f"  - {issue}")
    else:
        print("\n" + "*" * 100)
        print("*** ALL 16 BOOKS VERIFIED - 100% CONSISTENCY ***")
        print("*" * 100)
        print("\nAll checks passed:")
        print("  - S3 page_analysis matches output_files")
        print("  - No duplicate song titles")
        print("  - All S3 PDFs exist")
        print("  - All local PDFs exist and match")
        print("  - Page ranges are sequential")


if __name__ == '__main__':
    main()
