"""
Render page 3 to see what's there.
"""
import fitz
from PIL import Image
import io

doc = fitz.open("test-billy-joel.pdf")

page = doc[3]
pix = page.get_pixmap(dpi=150)
img_bytes = pix.tobytes("png")
img = Image.open(io.BytesIO(img_bytes))
img.save("page_3_check.png")

print(f"Saved page 3 to page_3_check.png")

doc.close()
