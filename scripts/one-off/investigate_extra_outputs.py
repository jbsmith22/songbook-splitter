import os

# The 15 output folders without input PDFs
extra_outputs = [
    r'ProcessedSongs\_broadway Shows\Various Artists - High School Musical [score]',
    r'ProcessedSongs\_broadway Shows\Various Artists - Little Shop Of Horrors (original)',
    r'ProcessedSongs\_broadway Shows\Various Artists - Wicked [pvg]',
    r'ProcessedSongs\_broadway Shows\Various Artists - Wicked [score]',
    r"ProcessedSongs\_broadway Shows\Various Artists - You're A Good Man Charlie Brown [revival] [score]",
    r'ProcessedSongs\America\America - Greatest Hits [Book]',
    r"ProcessedSongs\Ben Folds\Ben Folds - Rockin' The Suburbs [Book]",
    r'ProcessedSongs\Elo\Elton John - The Elton John Collection [Piano Solos]',
    r'ProcessedSongs\Kinks\Kinks - Guitar Legends [Tab]',
    r'ProcessedSongs\Night Ranger\Seven Wishes _jap Score_',
    r'ProcessedSongs\Tom Waits\Anthology',
    r'ProcessedSongs\Various Artists\Adult Contemporary Hits Of The Nineties',
    r'ProcessedSongs\Vince Guaraldi\Peanuts Songbook',
    r'ProcessedSongs\Who\Who - Quadrophenia (PVG)',
    r'ProcessedSongs\Wings\Wings - London Town (PVG Book)'
]

print("INVESTIGATING EXTRA OUTPUT FOLDERS")
print("=" * 80)

for folder in extra_outputs:
    if os.path.exists(folder):
        # Count PDFs in this folder
        pdf_count = len([f for f in os.listdir(folder) if f.lower().endswith('.pdf')])
        print(f"\n{folder}")
        print(f"  PDFs: {pdf_count}")
        
        # Show first 3 PDFs
        pdfs = [f for f in os.listdir(folder) if f.lower().endswith('.pdf')][:3]
        for pdf in pdfs:
            print(f"    - {pdf}")
        if len(pdfs) > 3:
            print(f"    ... and {len(pdfs) - 3} more")
    else:
        print(f"\n{folder}")
        print(f"  DOES NOT EXIST")

print("\n" + "=" * 80)
print("CHECKING INPUT FOLDER FOR SIMILAR NAMES")
print("=" * 80)

# Check if there are similar input PDFs
input_folder = r'SheetMusic'

# For each extra output, try to find similar input PDFs
for folder in extra_outputs:
    parts = folder.split(os.sep)
    if len(parts) >= 3:
        artist = parts[1]
        book = parts[2]
        
        print(f"\n{artist}/{book}")
        
        # Check if artist folder exists in input
        artist_input = os.path.join(input_folder, artist)
        if os.path.exists(artist_input):
            # List all PDFs in artist folder
            pdfs = []
            for root, dirs, files in os.walk(artist_input):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdfs.append(file)
            
            if pdfs:
                print(f"  Input PDFs in {artist}:")
                for pdf in pdfs[:5]:
                    print(f"    - {pdf}")
                if len(pdfs) > 5:
                    print(f"    ... and {len(pdfs) - 5} more")
            else:
                print(f"  No PDFs in input folder")
        else:
            print(f"  Artist folder does not exist in input")
