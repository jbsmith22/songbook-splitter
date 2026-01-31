import os

# Check the 3 that should have matched
cases = [
    {
        'output': r'ProcessedSongs\Tom Waits\Anthology',
        'input_options': [
            r'SheetMusic\Tom Waits\Tom Waits - Anthology.pdf',
            r'SheetMusic\Tom Waits\Tom Waits - Tom Waits Anthology.pdf'
        ]
    },
    {
        'output': r'ProcessedSongs\Various Artists\Adult Contemporary Hits Of The Nineties',
        'input_options': [
            r'SheetMusic\Various Artists\Various Artists - Adult Contemporary Hits Of The Nineties.pdf'
        ]
    },
    {
        'output': r'ProcessedSongs\Vince Guaraldi\Peanuts Songbook',
        'input_options': [
            r'SheetMusic\Vince Guaraldi\Vince Guaraldi - Peanuts Songbook.pdf'
        ]
    }
]

print("CHECKING MATCHING FAILURES")
print("=" * 80)

for case in cases:
    output = case['output']
    print(f"\nOutput: {output}")
    print(f"  Exists: {os.path.exists(output)}")
    
    if os.path.exists(output):
        pdfs = [f for f in os.listdir(output) if f.lower().endswith('.pdf')]
        print(f"  PDFs: {len(pdfs)}")
    
    print(f"  Input options:")
    for inp in case['input_options']:
        exists = os.path.exists(inp)
        print(f"    {inp}")
        print(f"      Exists: {exists}")
        
        if exists:
            # Get normalized keys
            parts = inp.split(os.sep)
            if len(parts) >= 3:
                artist = parts[1]
                book_pdf = parts[-1]
                book_name = book_pdf[:-4] if book_pdf.lower().endswith('.pdf') else book_pdf
                normalized = f"{artist.lower()}/{book_name.lower()}"
                print(f"      Normalized: {normalized}")
    
    # Get output normalized key
    parts = output.split(os.sep)
    if len(parts) >= 3:
        artist = parts[1]
        book = parts[2]
        normalized = f"{artist.lower()}/{book.lower()}"
        print(f"  Output normalized: {normalized}")
