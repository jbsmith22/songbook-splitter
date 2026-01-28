"""
Check what pages are in each extracted PDF.
"""
import fitz

# Check Half A Mile Away
doc1 = fitz.open('test_output_v3/Billy Joel-Half A Mile Away.pdf')
print("Half A Mile Away PDF:")
print(f"  Total pages: {len(doc1)}")
print(f"  Expected: PDF pages 40-46 (7 pages)")
print()

# Check first and last page to see what they are
page0 = doc1[0]
page_last = doc1[-1]

# Try to extract text to see page numbers
text0 = page0.get_text()
text_last = page_last.get_text()

print(f"  First page text (first 200 chars): {text0[:200]}")
print(f"  Last page text (first 200 chars): {text_last[:200]}")
print()

# Check Until The Night
doc2 = fitz.open('test_output_v3/Billy Joel-Until The Night.pdf')
print("Until The Night PDF:")
print(f"  Total pages: {len(doc2)}")
print(f"  Expected: PDF pages 47-54 (8 pages)")
print()

page0_2 = doc2[0]
text0_2 = page0_2.get_text()
print(f"  First page text (first 200 chars): {text0_2[:200]}")

doc1.close()
doc2.close()
