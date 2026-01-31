import os
from pathlib import Path
import csv
from difflib import SequenceMatcher

# Count input PDFs
input_folder = r'SheetMusic'
input_pdfs = {}  # normalized_path -> actual_path

print("COUNTING INPUT PDFs")
print("=" * 80)

for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.lower().endswith('.pdf'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, input_folder)
            
            # Create normalized key: Artist/BookName (case-insensitive, no extension)
            parts = rel_path.split(os.sep)
            if len(parts) >= 2:
                artist = parts[0]
                book_pdf = parts[-1]
                book_name = book_pdf[:-4] if book_pdf.lower().endswith('.pdf') else book_pdf
                
                # Normalize: lowercase, remove extra spaces
                normalized_key = f"{artist.lower()}/{book_name.lower()}".strip()
                input_pdfs[normalized_key] = rel_path

print(f"Total input PDFs: {len(input_pdfs)}")

# Count output folders
output_folder = r'ProcessedSongs'
output_folders = {}  # normalized_path -> actual_path

print("\nCOUNTING OUTPUT FOLDERS")
print("=" * 80)

for root, dirs, files in os.walk(output_folder):
    # Check if this folder has any PDF files
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    if pdf_files:
        # Get the book folder (2 levels deep: Artist/Book)
        rel_path = os.path.relpath(root, output_folder)
        parts = rel_path.split(os.sep)
        if len(parts) >= 2:
            artist = parts[0]
            book = parts[1]
            book_folder = f"{artist}/{book}"
            
            # Normalize: lowercase
            normalized_key = book_folder.lower().strip()
            if normalized_key not in output_folders:
                output_folders[normalized_key] = book_folder

print(f"Total output folders: {len(output_folders)}")

# Find exact matches
print("\n" + "=" * 80)
print("FINDING MATCHES")
print("=" * 80)

matched_input = set()
matched_output = set()

for input_key, input_path in input_pdfs.items():
    if input_key in output_folders:
        matched_input.add(input_key)
        matched_output.add(input_key)

print(f"Exact matches: {len(matched_input)}")

# Find unmatched input PDFs
unmatched_input = {k: v for k, v in input_pdfs.items() if k not in matched_input}
print(f"Unmatched input PDFs: {len(unmatched_input)}")

# Find unmatched output folders
unmatched_output = {k: v for k, v in output_folders.items() if k not in matched_output}
print(f"Unmatched output folders: {len(unmatched_output)}")

# Try to match unmatched items by similarity
print("\n" + "=" * 80)
print("FUZZY MATCHING UNMATCHED ITEMS")
print("=" * 80)

fuzzy_matches = []
remaining_input = set(unmatched_input.keys())
remaining_output = set(unmatched_output.keys())

for input_key in list(remaining_input):
    best_match = None
    best_score = 0
    
    for output_key in remaining_output:
        # Calculate similarity
        score = SequenceMatcher(None, input_key, output_key).ratio()
        if score > best_score:
            best_score = score
            best_match = output_key
    
    if best_score > 0.8:  # 80% similarity threshold
        fuzzy_matches.append((input_key, best_match, best_score))
        remaining_input.discard(input_key)
        remaining_output.discard(best_match)

print(f"Fuzzy matches found: {len(fuzzy_matches)}")

# Show fuzzy matches
if fuzzy_matches:
    print("\nFuzzy matches (showing first 20):")
    for i, (inp, out, score) in enumerate(fuzzy_matches[:20]):
        print(f"  {input_pdfs[inp]}")
        print(f"    -> {output_folders[out]}")
        print(f"    Similarity: {score*100:.1f}%")

# Final unmatched items
print("\n" + "=" * 80)
print("TRULY UNMATCHED INPUT PDFs (no output folder)")
print("=" * 80)

truly_unmatched_input = sorted(remaining_input)
for i, key in enumerate(truly_unmatched_input[:20]):
    print(f"  {input_pdfs[key]}")

if len(truly_unmatched_input) > 20:
    print(f"  ... and {len(truly_unmatched_input) - 20} more")

print(f"\nTotal: {len(truly_unmatched_input)}")

print("\n" + "=" * 80)
print("TRULY UNMATCHED OUTPUT FOLDERS (no input PDF)")
print("=" * 80)

truly_unmatched_output = sorted(remaining_output)
for i, key in enumerate(truly_unmatched_output[:20]):
    print(f"  {output_folders[key]}")

if len(truly_unmatched_output) > 20:
    print(f"  ... and {len(truly_unmatched_output) - 20} more")

print(f"\nTotal: {len(truly_unmatched_output)}")

# Summary
print("\n" + "=" * 80)
print("FINAL SUMMARY")
print("=" * 80)
print(f"Input PDFs: {len(input_pdfs)}")
print(f"Output folders: {len(output_folders)}")
print(f"Difference: {len(output_folders) - len(input_pdfs)}")
print()
print(f"Exact matches: {len(matched_input)}")
print(f"Fuzzy matches: {len(fuzzy_matches)}")
print(f"Total matched: {len(matched_input) + len(fuzzy_matches)}")
print()
print(f"Input PDFs without output: {len(truly_unmatched_input)}")
print(f"Output folders without input: {len(truly_unmatched_output)}")

# Save results to CSV
with open('input_output_comparison_smart.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Type', 'Input Path', 'Output Path', 'Similarity'])
    
    # Exact matches
    for key in sorted(matched_input):
        writer.writerow(['Exact Match', input_pdfs[key], output_folders[key], '100%'])
    
    # Fuzzy matches
    for inp, out, score in sorted(fuzzy_matches, key=lambda x: -x[2]):
        writer.writerow(['Fuzzy Match', input_pdfs[inp], output_folders[out], f'{score*100:.1f}%'])
    
    # Unmatched input
    for key in sorted(truly_unmatched_input):
        writer.writerow(['No Output', input_pdfs[key], '', ''])
    
    # Unmatched output
    for key in sorted(truly_unmatched_output):
        writer.writerow(['No Input', '', output_folders[key], ''])

print(f"\nResults saved to: input_output_comparison_smart.csv")
