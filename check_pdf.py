import fitz
from PIL import Image
import io

doc = fitz.open("test-billy-joel.pdf")
print(f"Total pages: {len(doc)}")
print()

# Check pages around where "Big Shot" should be (TOC says page 10)
# Try PDF indices 8, 9, 10, 11, 12
for pdf_idx in [8, 9, 10, 11, 12]:
    if pdf_idx < len(doc):
        page = doc[pdf_idx]
        
        # Render page as image and save
        pix = page.get_pixmap(dpi=72)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        img.save(f"page_{pdf_idx}.png")
        print(f"Saved page_{pdf_idx}.png")

doc.close()
