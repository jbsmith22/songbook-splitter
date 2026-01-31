"""Check actual local folder count vs matching results."""
from pathlib import Path
import pandas as pd

processed_songs_path = Path('ProcessedSongs')

# Count all book folders
book_folders = []
for artist_folder in processed_songs_path.iterdir():
    if not artist_folder.is_dir():
        continue
    
    for book_folder in artist_folder.iterdir():
        if not book_folder.is_dir():
            continue
        
        book_folders.append(f'{artist_folder.name}/{book_folder.name}')

book_folders.sort()

print(f'ACTUAL LOCAL FOLDER COUNT: {len(book_folders)}')
print()

# Now check what the matching script found
df = pd.read_csv('s3_local_exact_matches_v2.csv')
print(f'MATCHING SCRIPT FOUND: {len(df)} books')
print()

if len(book_folders) != len(df):
    print(f'DISCREPANCY: {len(df) - len(book_folders)} extra books in matching results')
    print()
    
    # Find which ones are in the CSV but not in actual folders
    csv_books = set()
    for idx, row in df.iterrows():
        csv_books.add(f"{row['local_artist']}/{row['local_book']}")
    
    actual_books = set(book_folders)
    
    extra_in_csv = csv_books - actual_books
    missing_from_csv = actual_books - csv_books
    
    if extra_in_csv:
        print(f'EXTRA IN CSV ({len(extra_in_csv)}):')
        for book in sorted(extra_in_csv):
            print(f'  {book}')
        print()
    
    if missing_from_csv:
        print(f'MISSING FROM CSV ({len(missing_from_csv)}):')
        for book in sorted(missing_from_csv):
            print(f'  {book}')
else:
    print('✓ Counts match!')
