"""
Analyze S3 output bucket structure and compare to expected naming conventions.
"""
import boto3
import csv
from collections import defaultdict
import re

def get_s3_structure():
    """Get all objects from S3 output bucket."""
    s3 = boto3.client('s3', region_name='us-east-1')
    
    print("Fetching S3 objects...")
    paginator = s3.get_paginator('list_objects_v2')
    
    all_objects = []
    for page in paginator.paginate(Bucket='jsmith-output'):
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    
    print(f"Found {len(all_objects)} total objects in S3")
    return all_objects

def categorize_objects(objects):
    """Categorize S3 objects by type."""
    categories = {
        'song_pdfs': [],
        'manifests': [],
        'artifacts': [],
        'other': []
    }
    
    for obj in objects:
        key = obj['Key']
        
        if key.startswith('artifacts/'):
            categories['artifacts'].append(key)
        elif key.endswith('manifest.json'):
            categories['manifests'].append(key)
        elif key.endswith('.pdf'):
            categories['song_pdfs'].append(key)
        else:
            categories['other'].append(key)
    
    return categories

def analyze_song_structure(song_pdfs):
    """Analyze the structure of song PDF paths."""
    structure_patterns = defaultdict(list)
    
    for pdf_path in song_pdfs:
        parts = pdf_path.split('/')
        
        if len(parts) == 3:
            # Artist/Book/Song.pdf
            artist, book, song = parts
            structure_patterns['Artist/Book/Song'].append(pdf_path)
        elif len(parts) == 4:
            # Artist/Book/Songs/Song.pdf or similar
            artist, book, subfolder, song = parts
            structure_patterns[f'Artist/Book/{subfolder}/Song'].append(pdf_path)
        else:
            structure_patterns[f'{len(parts)} parts'].append(pdf_path)
    
    return structure_patterns

def load_expected_books():
    """Load expected books from CSV."""
    expected = {}
    
    with open('book_reconciliation_validated.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row['Artist']
            book_name = row['BookName']
            
            if artist not in expected:
                expected[artist] = []
            expected[artist].append(book_name)
    
    return expected

def compare_structures(song_pdfs, expected_books):
    """Compare S3 structure to expected structure."""
    # Group S3 songs by artist and book
    s3_structure = defaultdict(lambda: defaultdict(list))
    
    for pdf_path in song_pdfs:
        parts = pdf_path.split('/')
        if len(parts) >= 3:
            artist = parts[0]
            book = parts[1]
            song = parts[-1]  # Last part is always the song
            s3_structure[artist][book].append(song)
    
    print("\n" + "="*80)
    print("STRUCTURE COMPARISON")
    print("="*80)
    
    # Check for naming convention issues
    issues = []
    
    for artist, books in s3_structure.items():
        for book, songs in books.items():
            # Check if book name has old conventions
            if '_' in book and ('[' in book or '(' in book):
                # Has both underscores and brackets - might be old naming
                issues.append({
                    'type': 'mixed_naming',
                    'artist': artist,
                    'book': book,
                    'song_count': len(songs)
                })
            
            # Check for duplicate book folders
            similar_books = [b for b in books.keys() if b.lower().replace(' ', '') == book.lower().replace(' ', '')]
            if len(similar_books) > 1:
                issues.append({
                    'type': 'duplicate_books',
                    'artist': artist,
                    'books': similar_books
                })
    
    return s3_structure, issues

def main():
    print("Analyzing S3 Output Bucket Structure")
    print("="*80)
    
    # Get all S3 objects
    objects = get_s3_structure()
    
    # Categorize objects
    categories = categorize_objects(objects)
    
    print("\n" + "="*80)
    print("OBJECT CATEGORIES")
    print("="*80)
    print(f"Song PDFs:  {len(categories['song_pdfs']):,}")
    print(f"Manifests:  {len(categories['manifests']):,}")
    print(f"Artifacts:  {len(categories['artifacts']):,}")
    print(f"Other:      {len(categories['other']):,}")
    
    # Analyze song structure
    structure_patterns = analyze_song_structure(categories['song_pdfs'])
    
    print("\n" + "="*80)
    print("SONG PDF STRUCTURE PATTERNS")
    print("="*80)
    for pattern, paths in sorted(structure_patterns.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{pattern}: {len(paths):,} files")
        if len(paths) <= 5:
            for path in paths[:5]:
                print(f"  - {path}")
    
    # Load expected books
    expected_books = load_expected_books()
    print(f"\nExpected: {len(expected_books)} artists, {sum(len(books) for books in expected_books.values())} books")
    
    # Compare structures
    s3_structure, issues = compare_structures(categories['song_pdfs'], expected_books)
    
    print(f"\nS3 has: {len(s3_structure)} artists, {sum(len(books) for books in s3_structure.values())} book folders")
    
    # Report issues
    if issues:
        print("\n" + "="*80)
        print("POTENTIAL ISSUES")
        print("="*80)
        
        mixed_naming = [i for i in issues if i['type'] == 'mixed_naming']
        if mixed_naming:
            print(f"\n{len(mixed_naming)} books with mixed naming conventions:")
            for issue in mixed_naming[:10]:
                print(f"  - {issue['artist']}/{issue['book']} ({issue['song_count']} songs)")
        
        duplicates = [i for i in issues if i['type'] == 'duplicate_books']
        if duplicates:
            print(f"\n{len(duplicates)} potential duplicate book folders:")
            for issue in duplicates[:10]:
                print(f"  - {issue['artist']}: {issue['books']}")
    
    # Sample some paths
    print("\n" + "="*80)
    print("SAMPLE PATHS (first 20 song PDFs)")
    print("="*80)
    for path in categories['song_pdfs'][:20]:
        print(f"  {path}")
    
    # Check for the "s3:/" issue mentioned in docs
    s3_prefix_paths = [p for p in categories['song_pdfs'] if p.startswith('s3:/')]
    if s3_prefix_paths:
        print("\n" + "="*80)
        print(f"WARNING: Found {len(s3_prefix_paths)} paths with 's3:/' prefix!")
        print("="*80)
        for path in s3_prefix_paths[:10]:
            print(f"  {path}")
    
    # Check for "output/" prefix
    output_prefix_paths = [p for p in categories['song_pdfs'] if p.startswith('output/')]
    if output_prefix_paths:
        print("\n" + "="*80)
        print(f"WARNING: Found {len(output_prefix_paths)} paths with 'output/' prefix!")
        print("="*80)
        for path in output_prefix_paths[:10]:
            print(f"  {path}")
    
    # Save detailed analysis
    with open('s3_output_structure_analysis.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Artist', 'Book', 'SongCount', 'SampleSong'])
        
        for artist in sorted(s3_structure.keys()):
            for book in sorted(s3_structure[artist].keys()):
                songs = s3_structure[artist][book]
                sample_song = songs[0] if songs else ''
                writer.writerow([artist, book, len(songs), sample_song])
    
    print("\n" + "="*80)
    print("Detailed analysis saved to: s3_output_structure_analysis.csv")
    print("="*80)

if __name__ == '__main__':
    main()
