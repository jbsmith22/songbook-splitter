"""
Check the pages around "Until The Night" to see what the vision detected.
"""
import json

with open("page_analysis.json", "r") as f:
    data = json.load(f)

print("Pages 40-50 (around Half A Mile Away and Until The Night):")
print("=" * 80)
for page in data[40:51]:
    marker = "🎵" if page["is_song_start"] == "YES" else "  "
    print(f"{marker} PDF {page['pdf_index']:3d} | Printed: {page['printed_page']:>4s} | Start: {page['is_song_start']:3s} | Title: {page['song_title']}")

print()
print("According to TOC:")
print("  Half A Mile Away: page 52")
print("  Until The Night: page 60")
print("  52nd Street: page 68")
