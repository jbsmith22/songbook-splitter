"""
Fix the script tag structure in HTML viewer
"""

html_file = 'web/match-quality-viewer-enhanced.html'
print(f"Reading {html_file}...")

with open(html_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Find the main script tag and fix the structure
# Current (wrong):
#   <script>
#       <script src="match-quality-data.js"></script>
#   // comment
#
# Should be:
#   <script src="match-quality-data.js"></script>
#   <script>
#   // comment

fixed = False
for i in range(len(lines)):
    if i == 647 and '<script>' in lines[i]:  # Line 648 (0-indexed 647)
        # This is the opening <script> tag
        if i + 1 < len(lines) and '<script src="match-quality-data.js"></script>' in lines[i + 1]:
            print(f"Found malformed structure at line {i+1}")
            # Swap the lines
            external_script = lines[i + 1]
            lines[i + 1] = lines[i]  # Move <script> down
            lines[i] = external_script  # Move external script up
            print("Fixed script tag order")
            fixed = True
            break

if not fixed:
    print("ERROR: Could not find the malformed structure")
    exit(1)

print(f"Writing fixed {html_file}...")
with open(html_file, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("\nDone! Script tags are now in correct order.")
