import os

# The 10 extra output folders
extras = [
    ('America', 'America - Greatest Hits [Book]'),
    ('Ben Folds', "Ben Folds - Rockin' The Suburbs [Book]"),
    ('Elo', 'Elton John - The Elton John Collection [Piano Solos]'),
    ('Kinks', 'Kinks - Guitar Legends [Tab]'),
    ('Night Ranger', 'Seven Wishes _jap Score_'),
    ('Tom Waits', 'Anthology'),
    ('Various Artists', 'Adult Contemporary Hits Of The Nineties'),
    ('Vince Guaraldi', 'Peanuts Songbook'),
    ('Who', 'Who - Quadrophenia (PVG)'),
    ('Wings', 'Wings - London Town (PVG Book)')
]

print("CHECKING THE 10 EXTRA OUTPUT FOLDERS")
print("=" * 80)

output_base = r'ProcessedSongs'

for artist, book in extras:
    folder_path = os.path.join(output_base, artist, book)
    
    print(f"\n{artist}/{book}")
    
    if os.path.exists(folder_path):
        pdfs = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
        print(f"  Exists: Yes ({len(pdfs)} PDFs)")
        
        # Check for similar folders in same artist
        artist_path = os.path.join(output_base, artist)
        if os.path.exists(artist_path):
            all_books = [d for d in os.listdir(artist_path) if os.path.isdir(os.path.join(artist_path, d))]
            
            # Find similar book names
            similar = []
            book_lower = book.lower().replace('[', '_').replace(']', '_').replace('(', '_').replace(')', '_')
            
            for other_book in all_books:
                if other_book != book:
                    other_lower = other_book.lower().replace('[', '_').replace(']', '_').replace('(', '_').replace(')', '_')
                    if book_lower == other_lower or book_lower in other_lower or other_lower in book_lower:
                        other_path = os.path.join(artist_path, other_book)
                        other_pdfs = [f for f in os.listdir(other_path) if f.lower().endswith('.pdf')]
                        similar.append((other_book, len(other_pdfs)))
            
            if similar:
                print(f"  Similar folders found:")
                for sim_book, sim_count in similar:
                    print(f"    - {sim_book} ({sim_count} PDFs)")
            else:
                print(f"  No similar folders found")
    else:
        print(f"  Exists: No")
