"""
Fix page_analysis.json to add viewer-compatible field aliases.

The manual_split_editor expects:
- total_pdf_pages (alias for total_pages)
- page_offset.calculated_offset and page_offset.is_consistent
- songs[].actual_pdf_start (alias for start_pdf_page)
- songs[].actual_pdf_end (alias for end_pdf_page)
- songs[].toc_printed_page (alias for toc_page)
- songs[].verified
"""
import json
import boto3

OUTPUT_BUCKET = 'jsmith-output'
s3 = boto3.client('s3')


def fix_page_analysis(book_id: str):
    """Add viewer-compatible fields to page_analysis.json."""
    print(f"Fixing {book_id}...")

    # Download current page_analysis.json
    try:
        obj = s3.get_object(Bucket=OUTPUT_BUCKET, Key=f'artifacts/{book_id}/page_analysis.json')
        pa = json.loads(obj['Body'].read())
    except Exception as e:
        print(f"  ERROR: Could not load page_analysis.json: {e}")
        return False

    # Check if already has viewer fields
    if 'total_pdf_pages' in pa and pa.get('songs') and 'actual_pdf_start' in pa['songs'][0]:
        print(f"  Already has viewer fields")
        return True

    # Add total_pdf_pages alias
    if 'total_pdf_pages' not in pa:
        pa['total_pdf_pages'] = pa.get('total_pages', 0)

    # Add page_offset structure
    if 'page_offset' not in pa:
        pa['page_offset'] = {
            'calculated_offset': pa.get('calculated_offset', 0),
            'is_consistent': pa.get('offset_confidence', 0) > 0.8
        }

    # Add viewer fields to each song
    for song in pa.get('songs', []):
        if 'actual_pdf_start' not in song:
            song['actual_pdf_start'] = song.get('start_pdf_page')
        if 'actual_pdf_end' not in song:
            song['actual_pdf_end'] = song.get('end_pdf_page')
        if 'toc_printed_page' not in song:
            song['toc_printed_page'] = song.get('toc_page')
        if 'verified' not in song:
            song['verified'] = song.get('match_method') in ('direct_match', 'detected_only')

    # Upload fixed version
    s3.put_object(
        Bucket=OUTPUT_BUCKET,
        Key=f'artifacts/{book_id}/page_analysis.json',
        Body=json.dumps(pa, indent=2)
    )

    print(f"  Fixed {len(pa.get('songs', []))} songs")
    return True


def main():
    book_ids = [
        'v2-dc4c90d5e3d7da00-2',  # Beatles
        'v2-891cfa3eccc19933-2',  # Billy Joel
        'v2-6790e3106cc63c95-2',  # Elton John
        'v2-c2a89cc21678f463-2',  # Queen
    ]

    for book_id in book_ids:
        fix_page_analysis(book_id)

    print("\nDone! Refresh the viewer to see the fixes.")


if __name__ == '__main__':
    main()
