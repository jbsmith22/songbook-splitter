"""Check why 11 folders are missing from matching results."""
from pathlib import Path

missing_folders = [
    ('Crosby Stills And Nash', 'Crosby Stills Nash And Young - The Guitar Collection'),
    ('Dire Straits', 'Dire Straits - Mark Knopfler Guitar Styles Vol 1 _Guitar Book_'),
    ('Elvis Presley', 'Elvis Presley - The Compleat _PVG Book_'),
    ('Eric Clapton', 'Eric Clapton - The Cream Of Clapton'),
    ('Mamas and the Papas', 'Mamas And The Papas - Songbook _PVG_'),
    ('Night Ranger', 'Night Ranger - Seven Wishes _Jap Score_'),
    ('Robbie Robertson', 'Robbie Robertson - Songbook _Guitar Tab_'),
    ('Various Artists', 'Various Artists - Ultimate 80s Songs'),
    ('_broadway Shows', 'Various Artists - 25th Annual Putnam County Spelling Bee'),
    ('_broadway Shows', 'Various Artists - Little Shop Of Horrors Script'),
    ('_movie And Tv', 'Various Artists - Complete TV And Film'),
]

print('CHECKING MISSING FOLDERS')
print('='*80)

for artist, book in missing_folders:
    path = Path('ProcessedSongs') / artist / book
    
    if not path.exists():
        print(f'✗ NOT FOUND: {artist}/{book}')
        continue
    
    # Count PDF files
    pdf_files = list(path.glob('*.pdf'))
    
    print(f'\n{artist}/{book}')
    print(f'  Path exists: ✓')
    print(f'  PDF files: {len(pdf_files)}')
    
    if len(pdf_files) == 0:
        print(f'  ⚠️  NO PDF FILES - This is why it was skipped!')
    else:
        print(f'  ✓ Has PDF files - Should have been included')
        # Show first few files
        for pdf in pdf_files[:3]:
            print(f'    - {pdf.name}')

print('\n' + '='*80)
print('SUMMARY: Folders with 0 PDF files are skipped by the matching algorithm')
print('='*80)
