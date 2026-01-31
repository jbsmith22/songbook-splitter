import os
import shutil

# Folders that don't exist in S3 and should be deleted
folders_to_delete = [
    r'ProcessedSongs\Elvis Presley\Elvis Presley - The Compleat _PVG Book_',
    r'ProcessedSongs\Mamas and the Papas\Mamas And The Papas - Songbook _PVG_',
    r'ProcessedSongs\Eric Clapton\Eric Clapton - The Cream Of Clapton',
    r'ProcessedSongs\_broadway Shows\Various Artists - 25th Annual Putnam County Spelling Bee',
    r'ProcessedSongs\_movie And Tv\Various Artists - Complete TV And Film'
]

print("DELETING EMPTY FOLDERS THAT DON'T EXIST IN S3")
print("=" * 80)

for folder in folders_to_delete:
    if os.path.exists(folder):
        # Check if folder is empty
        files = [f for f in os.listdir(folder) if f.endswith('.pdf')]
        if len(files) == 0:
            print(f"\n✓ Deleting: {folder}")
            shutil.rmtree(folder)
        else:
            print(f"\n✗ NOT EMPTY (has {len(files)} PDFs): {folder}")
    else:
        print(f"\n- Already gone: {folder}")

print("\n" + "=" * 80)
print("DONE")
