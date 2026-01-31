import shutil
import os

# Folders to delete
folders_to_delete = [
    # 5 duplicates with same PDF count
    r'ProcessedSongs\America\America - Greatest Hits [Book]',
    r'ProcessedSongs\Kinks\Kinks - Guitar Legends [Tab]',
    r'ProcessedSongs\Night Ranger\Seven Wishes _jap Score_',
    r'ProcessedSongs\Who\Who - Quadrophenia (PVG)',
    r'ProcessedSongs\Wings\Wings - London Town (PVG Book)',
    
    # 1 wrong artist folder
    r'ProcessedSongs\Elo\Elton John - The Elton John Collection [Piano Solos]',
    
    # 3 smaller versions (keep the bigger ones)
    r'ProcessedSongs\Tom Waits\Tom Waits - Anthology',  # 7 PDFs, keeping Anthology with 29
    r'ProcessedSongs\Tom Waits\Tom Waits - Tom Waits Anthology',  # 24 PDFs, keeping Anthology with 29
    r'ProcessedSongs\Various Artists\Various Artists - Adult Contemporary Hits Of The Nineties',  # 10 PDFs, keeping the 30 PDF version
    r'ProcessedSongs\Vince Guaraldi\Vince Guaraldi - Peanuts Songbook',  # 8 PDFs, keeping the 28 PDF version
]

print("DELETING 9 EXTRA FOLDERS")
print("=" * 80)

deleted_count = 0
for folder in folders_to_delete:
    if os.path.exists(folder):
        pdf_count = len([f for f in os.listdir(folder) if f.lower().endswith('.pdf')])
        print(f"\n✓ Deleting: {folder}")
        print(f"  PDFs: {pdf_count}")
        shutil.rmtree(folder)
        deleted_count += 1
    else:
        print(f"\n✗ Not found: {folder}")

print("\n" + "=" * 80)
print(f"DELETED: {deleted_count} folders")
print(f"Expected remaining: 569 - {deleted_count} = {569 - deleted_count} folders")
