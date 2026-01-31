import fitz
from PIL import Image
import io

doc = fitz.open("test-billy-joel.pdf")
print(f"Total pages in source PDF: {len(doc)}")
print()

# Check pages around where songs should be according to TOC
checks = [
    ("Big Shot", 10, 9),  # TOC says 10, mapper says PDF index 9
    ("My Life", 25, 24),  # TOC says 25, mapper says PDF index 24
    ("Honesty", 19, 18),  # TOC says 19, mapper says PDF index 18
]

for song_title, toc_page, pdf_index in checks:
    print(f"\n{'='*60}")
    print(f"Song: {song_title}")
    print(f"TOC says page: {toc_page}")
    print(f"Mapper calculated PDF index: {pdf_index}")
    print('='*60)
    
    if pdf_index < len(doc):
        page = doc[pdf_index]
        
        # Save as image
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        
        filename = f"source_page_{pdf_index}_{song_title.replace(' ', '_')}.png"
        img.save(filename)
        print(f"Saved: {filename}")
    else:
        print(f"PDF index {pdf_index} is out of bounds (PDF has {len(doc)} pages)")

doc.close()
