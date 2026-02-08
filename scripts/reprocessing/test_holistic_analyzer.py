"""
Test the holistic page analyzer locally on a specific book.

Usage:
    py scripts/reprocessing/test_holistic_analyzer.py "Beatles/Beatles - Abbey Road.pdf"
    py scripts/reprocessing/test_holistic_analyzer.py --list   # List available books
"""
import sys
import json
import argparse
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.holistic_page_analyzer import HolisticPageAnalyzer


def get_toc_for_book(pdf_path: Path) -> list:
    """
    Try to get TOC entries for a book.
    First check if we have a cached TOC from a previous run, otherwise use vision.
    """
    import boto3

    # Generate book_id
    import hashlib
    rel_path = str(pdf_path.relative_to(Path('SheetMusic'))).replace('\\', '/')
    book_id = 'v2-' + hashlib.md5(rel_path.encode()).hexdigest()[:16]

    # Try to get cached TOC from S3
    s3 = boto3.client('s3')
    try:
        obj = s3.get_object(Bucket='jsmith-output', Key=f'artifacts/{book_id}/toc_parse.json')
        data = json.loads(obj['Body'].read())
        print(f"Using cached TOC from S3 ({len(data['entries'])} entries)")
        return data['entries']
    except:
        pass

    # Fall back to using TOC parser
    print("No cached TOC found. Running TOC discovery...")

    try:
        from app.services.toc_parser import TOCParserService
        parser = TOCParserService()

        # First discover TOC pages
        from app.services.toc_discovery import TOCDiscoveryService
        discovery = TOCDiscoveryService()
        toc_pages = discovery.find_toc_pages(str(pdf_path))

        if toc_pages:
            print(f"  Found TOC on pages: {toc_pages}")
            entries = parser.extract_toc_entries(str(pdf_path), toc_pages)
            print(f"  Extracted {len(entries)} TOC entries")
            return [{'song_title': e.song_title, 'page_number': e.page_number, 'artist': e.artist}
                    for e in entries]
    except Exception as e:
        print(f"  TOC extraction failed: {e}")

    return []


def list_books():
    """List available books in SheetMusic folder."""
    sheetmusic = Path('SheetMusic')
    books = list(sheetmusic.glob('**/*.pdf'))

    print(f"Found {len(books)} books:\n")

    by_artist = {}
    for book in books:
        artist = book.parent.name
        if artist not in by_artist:
            by_artist[artist] = []
        by_artist[artist].append(book.name)

    for artist in sorted(by_artist.keys())[:30]:
        print(f"{artist}:")
        for book in by_artist[artist][:5]:
            print(f"  {book}")
        if len(by_artist[artist]) > 5:
            print(f"  ... and {len(by_artist[artist]) - 5} more")

    if len(by_artist) > 30:
        print(f"\n... and {len(by_artist) - 30} more artists")


def main():
    parser = argparse.ArgumentParser(description='Test holistic page analyzer')
    parser.add_argument('pdf_path', nargs='?', help='Relative path to PDF in SheetMusic folder')
    parser.add_argument('--list', action='store_true', help='List available books')
    parser.add_argument('--save', action='store_true', help='Save results to JSON file')

    args = parser.parse_args()

    if args.list:
        list_books()
        return

    if not args.pdf_path:
        print("Usage: py scripts/reprocessing/test_holistic_analyzer.py <pdf_path>")
        print("       py scripts/reprocessing/test_holistic_analyzer.py --list")
        return

    # Find the PDF
    sheetmusic = Path('SheetMusic')
    pdf_path = sheetmusic / args.pdf_path

    if not pdf_path.exists():
        print(f"Error: PDF not found: {pdf_path}")
        return

    print("=" * 70)
    print("HOLISTIC PAGE ANALYZER TEST")
    print("=" * 70)
    print(f"PDF: {pdf_path}")
    print()

    # Get TOC entries
    toc_entries = get_toc_for_book(pdf_path)
    if not toc_entries:
        print("Warning: No TOC entries found. Analysis may be limited.")
    else:
        print(f"\nTOC ({len(toc_entries)} songs):")
        for i, entry in enumerate(toc_entries[:10]):
            print(f"  {i+1}. {entry['song_title']} (page {entry['page_number']})")
        if len(toc_entries) > 10:
            print(f"  ... and {len(toc_entries) - 10} more")

    # Extract artist from path
    artist = pdf_path.parent.name

    # Generate book_id
    import hashlib
    rel_path = str(pdf_path.relative_to(sheetmusic)).replace('\\', '/')
    book_id = 'v2-' + hashlib.md5(rel_path.encode()).hexdigest()[:16]

    print(f"\nBook ID: {book_id}")
    print(f"Artist: {artist}")
    print()

    # Run analysis
    print("Running holistic analysis...")
    print("(This may take a few minutes for large books)")
    print()

    analyzer = HolisticPageAnalyzer()
    result = analyzer.analyze_book(
        pdf_path=str(pdf_path),
        book_id=book_id,
        source_pdf_uri=f's3://jsmith-input/{rel_path}',
        toc_entries=toc_entries,
        artist=artist
    )

    # Print results
    print()
    print("=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    print(f"Total pages: {result.total_pages}")
    print(f"TOC songs: {result.toc_song_count}")
    print(f"Detected song_start pages: {result.detected_song_count}")
    print(f"Matched songs: {result.matched_song_count}")
    print(f"Calculated offset: {result.calculated_offset}")
    print(f"Offset confidence: {result.offset_confidence:.2f}")

    if result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for w in result.warnings[:5]:
            print(f"  - {w}")
        if len(result.warnings) > 5:
            print(f"  ... and {len(result.warnings) - 5} more")

    print(f"\nSongs ({len(result.songs)}):")
    for i, song in enumerate(result.songs):
        method_badge = {
            'direct_match': '✓',
            'offset_fallback': '~',
            'toc_only': '?'
        }.get(song.match_method, '?')

        print(f"  {i+1}. [{method_badge}] {song.title}")
        print(f"       Pages {song.start_pdf_page}-{song.end_pdf_page} ({song.page_count} pages)")

    # Page type summary
    print(f"\nPage Types:")
    from collections import Counter
    type_counts = Counter(p.content_type for p in result.pages)
    for content_type, count in type_counts.most_common():
        print(f"  {content_type}: {count}")

    # Save results if requested
    if args.save:
        output_file = Path(f'test_analysis_{book_id}.json')
        result_dict = analyzer.to_dict(result)
        with open(output_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    # Summary
    print()
    print("=" * 70)
    if result.matched_song_count == result.toc_song_count:
        print("SUCCESS: All TOC songs matched!")
    else:
        missing = result.toc_song_count - result.matched_song_count
        print(f"PARTIAL: {missing} songs not matched")

    # Compare to expected
    if toc_entries:
        print(f"\nExpected vs Actual:")
        print(f"  TOC songs: {result.toc_song_count}")
        print(f"  Matched:   {result.matched_song_count}")
        print(f"  Match rate: {result.matched_song_count / result.toc_song_count * 100:.1f}%")


if __name__ == '__main__':
    main()
