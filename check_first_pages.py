import fitz
from PIL import Image
import io
import os

# Check first page of each PDF
pdf_files = [
    "test_output_aws/Billy Joel-Big Shot.pdf",
    "test_output_aws/Billy Joel-My Life.pdf",
    "test_output_aws/Billy Joel-Honesty.pdf"
]

for pdf_file in pdf_files:
    if os.path.exists(pdf_file):
        print(f"\n{'='*60}")
        print(f"Checking: {pdf_file}")
        print('='*60)
        
        doc = fitz.open(pdf_file)
        print(f"Total pages: {len(doc)}")
        
        # Get first page
        page = doc[0]
        
        # Try to extract text
        text = page.get_text("text")
        print(f"\nText on first page (first 300 chars):")
        print(text[:300] if text else "[No text found]")
        
        # Save first page as image
        pix = page.get_pixmap(dpi=150)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        
        output_name = os.path.basename(pdf_file).replace('.pdf', '_page1.png')
        img.save(f"test_output_aws/{output_name}")
        print(f"Saved first page image: test_output_aws/{output_name}")
        
        doc.close()
