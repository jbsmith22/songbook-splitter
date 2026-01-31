"""
Verify that extracted PDFs contain the correct song titles on their first pages.
"""
import fitz
import os
from pathlib import Path

# Expected song titles
songs = {
    "Big_Shot.pdf": "Big Shot",
    "Half_A_Mile_Away.pdf": "Half A Mile Away",
    "Honesty.pdf": "Honesty",
    "My_Life.pdf": "My Life",
    "Rosalinda's_Eyes.pdf": "Rosalinda's Eyes",
    "Stiletto.pdf": "Stiletto",
    "Zanzibar.pdf": "Zanzibar"
}

output_dir = Path("test_output_aws_new")

print("Verifying extracted PDFs...")
print("=" * 60)

for filename, expected_title in songs.items():
    pdf_path = output_dir / filename
    
    if not pdf_path.exists():
        print(f"❌ {filename}: FILE NOT FOUND")
        continue
    
    try:
        doc = fitz.open(pdf_path)
        first_page = doc[0]
        
        # Extract text from top 30% of first page
        page_rect = first_page.rect
        title_rect = fitz.Rect(
            page_rect.x0,
            page_rect.y0,
            page_rect.x1,
            page_rect.y0 + page_rect.height * 0.3
        )
        
        text = first_page.get_text("text", clip=title_rect)
        
        # Normalize for comparison
        text_normalized = text.lower().replace('\n', ' ').strip()
        expected_normalized = expected_title.lower()
        
        # Check if title appears in text
        if expected_normalized in text_normalized:
            print(f"✅ {filename}: CORRECT - Found '{expected_title}'")
        else:
            print(f"❌ {filename}: WRONG")
            print(f"   Expected: '{expected_title}'")
            print(f"   Found text: {text[:200]}")
        
        print(f"   Pages: {len(doc)}")
        doc.close()
        
    except Exception as e:
        print(f"❌ {filename}: ERROR - {e}")

print("=" * 60)
