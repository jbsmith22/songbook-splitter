"""
Create a cleanup plan for S3 output bucket duplicates.
For each book in the CSV, identify the "best" S3 folder to keep.
"""
import boto3
import csv
from collections import defaultdict

def load_expected_books():
    """Load expected books from CSV."""
    expected = []
    
    with open('book_reconciliation_validated.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            expected.append({
                'artist': row['Artist'],
                'book_name': row['BookName'],
                'file_count': int(row['FileCount'])
            })
    
    return expected

def load_s3_structure():
    """Load S3 structure from analysis CSV."""
    s3_books = defaultdict(list)
    
    with open('s3_output_structure_analysis.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist = row['Artist']
            book = row['Book']
            song_count = int(row['SongCount'])
            
            key = f"{artist}|||{book}"
            s3_books[artist].append({
                'book': book,
                'song_count': song_count
            })
    
    return s3_books

def normalize_name(name):
    """Normalize a name for comparison."""
    # Remove common variations
    name = name.lower()
    name = name.replace('[', '(').replace(']', ')')
    name = name.replace('_', ' ')
    name = name.replace('  ', ' ')
    name = name.strip()
    return name

def find_matching_folders(expected_book, s3_books_for_artist):
    """Find all S3 folders that match an expected book."""
    expected_norm = normalize_name(expected_book['book_name'])
    
    matches = []
    for s3_book in s3_books_for_artist:
        s3_norm = normalize_name(s3_book['book'])
        
        # Check if they match (with or without artist prefix)
        if expected_norm in s3_norm or s3_norm in expected_norm:
            matches.append(s3_book)
    
    return matches

def choose_best_folder(matches, expected_count):
    """Choose the best folder to keep from matches."""
    if not matches:
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    # Prefer folder with song count closest to expected
    best = min(matches, key=lambda m: abs(m['song_count'] - expected_count))
    
    # If multiple have same count, prefer one without artist prefix
    same_count = [m for m in matches if m['song_count'] == best['song_count']]
    if len(same_count) > 1:
        # Prefer shorter name (likely without artist prefix)
        best = min(same_count, key=lambda m: len(m['book']))
    
    return best

def main():
    print("Creating S3 Cleanup Plan")
    print("="*80)
    
    # Load data
    expected_books = load_expected_books()
    s3_structure = load_s3_structure()
    
    print(f"Expected: {len(expected_books)} books")
    print(f"S3 has: {sum(len(books) for books in s3_structure.values())} book folders")
    
    # Create cleanup plan
    cleanup_plan = []
    
    for expected in expected_books:
        artist = expected['artist']
        book_name = expected['book_name']
        expected_count = expected['file_count']
        
        # Find matching S3 folders
        s3_books = s3_structure.get(artist, [])
        matches = find_matching_folders(expected, s3_books)
        
        if not matches:
            cleanup_plan.append({
                'artist': artist,
                'expected_book': book_name,
                'expected_count': expected_count,
                'status': 'MISSING',
                'keep_folder': '',
                'delete_folders': '',
                'notes': 'No matching folder found in S3'
            })
        elif len(matches) == 1:
            cleanup_plan.append({
                'artist': artist,
                'expected_book': book_name,
                'expected_count': expected_count,
                'status': 'OK',
                'keep_folder': matches[0]['book'],
                'delete_folders': '',
                'notes': f"Single folder, {matches[0]['song_count']} songs"
            })
        else:
            # Multiple matches - need to choose best
            best = choose_best_folder(matches, expected_count)
            others = [m for m in matches if m != best]
            
            cleanup_plan.append({
                'artist': artist,
                'expected_book': book_name,
                'expected_count': expected_count,
                'status': 'DUPLICATE',
                'keep_folder': best['book'],
                'delete_folders': ' | '.join([m['book'] for m in others]),
                'notes': f"Keep {best['song_count']} songs, delete {sum(m['song_count'] for m in others)} songs from {len(others)} folders"
            })
    
    # Save cleanup plan
    with open('s3_cleanup_plan.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'artist', 'expected_book', 'expected_count', 'status',
            'keep_folder', 'delete_folders', 'notes'
        ])
        writer.writeheader()
        writer.writerows(cleanup_plan)
    
    # Print summary
    print("\n" + "="*80)
    print("CLEANUP PLAN SUMMARY")
    print("="*80)
    
    ok_count = len([p for p in cleanup_plan if p['status'] == 'OK'])
    duplicate_count = len([p for p in cleanup_plan if p['status'] == 'DUPLICATE'])
    missing_count = len([p for p in cleanup_plan if p['status'] == 'MISSING'])
    
    print(f"OK (single folder):     {ok_count}")
    print(f"DUPLICATE (multiple):   {duplicate_count}")
    print(f"MISSING (no folder):    {missing_count}")
    
    # Calculate deletion stats
    total_folders_to_delete = 0
    total_songs_to_delete = 0
    
    for plan in cleanup_plan:
        if plan['status'] == 'DUPLICATE':
            delete_count = len(plan['delete_folders'].split(' | '))
            total_folders_to_delete += delete_count
            
            # Extract song count from notes
            if 'delete' in plan['notes']:
                import re
                match = re.search(r'delete (\d+) songs', plan['notes'])
                if match:
                    total_songs_to_delete += int(match.group(1))
    
    print(f"\nFolders to delete:      {total_folders_to_delete}")
    print(f"Songs to delete:        {total_songs_to_delete}")
    print(f"Songs to keep:          {16640 - total_songs_to_delete}")
    
    print("\n" + "="*80)
    print("Cleanup plan saved to: s3_cleanup_plan.csv")
    print("="*80)
    
    # Show some examples
    print("\nExample duplicates to clean up:")
    duplicates = [p for p in cleanup_plan if p['status'] == 'DUPLICATE'][:10]
    for dup in duplicates:
        print(f"\n{dup['artist']} - {dup['expected_book']}")
        print(f"  KEEP:   {dup['keep_folder']}")
        print(f"  DELETE: {dup['delete_folders']}")

if __name__ == '__main__':
    main()
