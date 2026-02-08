"""
Update S3 manifests for reprocessed books with correct song data.
"""
import json
import boto3
from datetime import datetime

s3 = boto3.client('s3')
OUTPUT_BUCKET = 'jsmith-output'

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
    print("=" * 80)
    print("UPDATING S3 MANIFESTS")
    print("=" * 80)

    for book in books:
        book_id = book['book_id']
        book_name = book['name']
        artist = book_name.split(' - ')[0]

        print(f"\n{book_name}:")

        try:
            # Get current manifest
            manifest_key = f'output/{book_id}/manifest.json'
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=manifest_key)
            manifest = json.loads(obj['Body'].read())

            # Get output_files for song data
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/output_files.json')
            output_data = json.loads(obj['Body'].read())
            output_files = output_data.get('output_files', [])

            # Get page_analysis for additional data
            obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
            page_data = json.loads(obj['Body'].read())

            # Update manifest with song data
            manifest['songs'] = [
                {
                    'title': of.get('song_title'),
                    'page_range': of.get('page_range'),
                    'output_uri': of.get('output_uri'),
                    'file_size_bytes': of.get('file_size_bytes')
                }
                for of in output_files
            ]
            manifest['songs_extracted'] = len(output_files)
            manifest['total_pages'] = page_data.get('total_pages', 0)
            manifest['updated_timestamp'] = datetime.now().isoformat()

            # Also update output section
            manifest['output'] = {
                'songs_extracted': len(output_files),
                'output_files': [of.get('output_uri') for of in output_files]
            }

            # Write back to S3
            s3.put_object(
                Bucket=OUTPUT_BUCKET,
                Key=manifest_key,
                Body=json.dumps(manifest, indent=2),
                ContentType='application/json'
            )

            print(f"  Updated: {len(output_files)} songs")

        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 80)
    print("S3 MANIFESTS UPDATED")
    print("=" * 80)


if __name__ == '__main__':
    main()
