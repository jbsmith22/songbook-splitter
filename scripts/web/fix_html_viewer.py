"""
Fix the HTML viewer to load external data file
"""
from pathlib import Path

html_file = 'web/match-quality-viewer-enhanced.html'
print(f"Reading {html_file}...")

# Read the HTML file
with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find and modify line 649 (the embedded data line)
# Replace it with a comment and add script tag to load external file
for i, line in enumerate(lines):
    if i == 648:  # Line 649 (0-indexed)
        if 'const matchDataEmbedded' in line:
            print(f"Found embedded data at line {i+1}")
            # Replace with comment and external load
            lines[i] = '// Data loaded from external file match-quality-data.js\n'
            print("Replaced with comment")
        break

# Find the <script> tag that starts the main script and add our external script before it
# Look for the line before the embedded data and add script tag there
for i in range(647, 650):
    if i < len(lines) and '<script>' in lines[i]:
        print(f"Found script tag at line {i+1}")
        # Insert external script load after this line
        lines.insert(i+1, '    <script src="match-quality-data.js"></script>\n')
        print("Added external script tag")
        break

# Write back
print(f"Writing updated {html_file}...")
with open(html_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nDone! HTML viewer now loads data from external file.")
print("Make sure match-quality-data.js is in the same directory as the HTML file.")
