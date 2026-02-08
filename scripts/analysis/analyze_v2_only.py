#!/usr/bin/env python3
"""
Analyze ONLY V2 pipeline data - direct observation.
Focus on the 126 V2 books and their artifacts/outputs.
"""
import json
from pathlib import Path
from collections import defaultdict

# Load the collected data
DATA_DIR = Path('data/analysis/comprehensive_report')

def load_data():
    """Load all collected data."""
    with open(DATA_DIR / 'v2_book_artifacts.json') as f:
        v2_artifacts = json.load(f)

    with open(DATA_DIR / 'local_manifests.json') as f:
        local_manifests = json.load(f)

    with open(DATA_DIR / 'local_pdfs.json') as f:
        local_pdfs = json.load(f)

    return v2_artifacts, local_manifests, local_pdfs

def analyze_v2_books(v2_artifacts, local_manifests, local_pdfs):
    """Analyze each V2 book's artifacts and compare with local data."""

    # Index local data by folder
    local_by_folder = defaultdict(lambda: {'pdfs': [], 'manifest': None})

    for pdf in local_pdfs:
        folder = str(Path(pdf['relative_path']).parent)
        local_by_folder[folder]['pdfs'].append(pdf)

    for manifest in local_manifests:
        folder = manifest['folder']
        local_by_folder[folder]['manifest'] = manifest['content']

    # Analyze each V2 book
    results = []

    for book_id, artifacts in sorted(v2_artifacts.items()):
        book_data = {
            'book_id': book_id,
            'artifacts': {}
        }

        # Extract key data from artifacts
        if 'verified_songs.json' in artifacts:
            verified = artifacts['verified_songs.json']
            book_data['verified_songs_count'] = len(verified.get('verified_songs', []))
        else:
            book_data['verified_songs_count'] = 0

        if 'output_files.json' in artifacts:
            output_files = artifacts['output_files.json']
            book_data['output_files_count'] = len(output_files.get('output_files', []))
        else:
            book_data['output_files_count'] = 0

        if 'page_analysis.json' in artifacts:
            page_analysis = artifacts['page_analysis.json']
            pages = page_analysis.get('pages', [])
            book_data['total_pages'] = len(pages)
            book_data['page_analysis_errors'] = sum(1 for p in pages if p.get('content_type') == 'error')
            book_data['page_analysis_error_rate'] = (
                book_data['page_analysis_errors'] / book_data['total_pages'] * 100
                if book_data['total_pages'] > 0 else 0
            )
        else:
            book_data['total_pages'] = 0
            book_data['page_analysis_errors'] = 0
            book_data['page_analysis_error_rate'] = 0

        if 'toc_parse.json' in artifacts:
            toc = artifacts['toc_parse.json']
            book_data['toc_songs_count'] = len(toc.get('songs', []))
        else:
            book_data['toc_songs_count'] = 0

        # Try to match with local data
        book_data['local_manifest'] = None
        book_data['local_pdfs_count'] = 0

        for folder, local_data in local_by_folder.items():
            if local_data['manifest'] and local_data['manifest'].get('book_id') == book_id:
                book_data['local_manifest'] = {
                    'folder': folder,
                    'total_songs': local_data['manifest'].get('total_entries', 0),
                    'unique_songs': local_data['manifest'].get('unique_songs', 0)
                }
                book_data['local_pdfs_count'] = len(local_data['pdfs'])
                break

        results.append(book_data)

    return results

def generate_report(results):
    """Generate comprehensive V2 report."""

    print("=" * 100)
    print("V2 PIPELINE ANALYSIS - DIRECT OBSERVATION ONLY")
    print("=" * 100)
    print()

    # Summary statistics
    total_books = len(results)
    with_verified_songs = sum(1 for r in results if r['verified_songs_count'] > 0)
    with_output_files = sum(1 for r in results if r['output_files_count'] > 0)
    with_local_manifest = sum(1 for r in results if r['local_manifest'] is not None)

    print(f"Total V2 Books: {total_books}")
    print(f"Books with verified_songs: {with_verified_songs}")
    print(f"Books with output_files: {with_output_files}")
    print(f"Books with local manifest: {with_local_manifest}")
    print()

    # Count matches
    exact_matches = sum(1 for r in results
                       if r['local_manifest']
                       and r['output_files_count'] == r['local_pdfs_count'])

    print(f"Books where output_files == local_pdfs: {exact_matches}")
    print()

    # Save detailed JSON report
    output_file = Path('data/analysis/v2_only_analysis.json')
    with open(output_file, 'w') as f:
        json.dump({
            'summary': {
                'total_books': total_books,
                'with_verified_songs': with_verified_songs,
                'with_output_files': with_output_files,
                'with_local_manifest': with_local_manifest,
                'exact_matches': exact_matches
            },
            'books': results
        }, f, indent=2)

    print(f"Detailed JSON report saved to: {output_file}")
    print()

    # Show some examples
    print("=" * 100)
    print("SAMPLE BOOKS (first 5):")
    print("=" * 100)

    for i, book in enumerate(results[:5], 1):
        print(f"\n{i}. {book['book_id']}")
        print(f"   Verified: {book['verified_songs_count']} | Output files: {book['output_files_count']} | Local PDFs: {book['local_pdfs_count']}")
        if book['local_manifest']:
            print(f"   Local folder: {book['local_manifest']['folder']}")
            match = "MATCH" if book['output_files_count'] == book['local_pdfs_count'] else "MISMATCH"
            print(f"   Status: {match}")
        else:
            print(f"   Status: NO LOCAL MANIFEST")

def main():
    print("Loading data...")
    v2_artifacts, local_manifests, local_pdfs = load_data()

    print("Analyzing V2 books...")
    results = analyze_v2_books(v2_artifacts, local_manifests, local_pdfs)

    print("Generating report...\n")
    generate_report(results)

if __name__ == '__main__':
    main()
