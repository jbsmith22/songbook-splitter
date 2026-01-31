import os
from pathlib import Path
import csv

# Count input PDFs
input_folder = r'SheetMusic'
input_pdfs = []

print("COUNTING INPUT PDFs")
print("=" * 80)

for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.lower().endswith('.pdf'):
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, input_folder)
            input_pdfs.append(rel_path)

print(f"Total input PDFs: {len(input_pdfs)}")

# Count output folders
output_folder = r'ProcessedSongs'
output_folders = []

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
            book_folder = os.path.join(parts[0], parts[1])
            if book_folder not in output_folders:
                output_folders.append(book_folder)

print(f"Total output folders: {len(output_folders)}")

# Create mapping from input PDF to expected output folder
# Input format: Artist/Book.pdf or Artist/subfolder/Book.pdf
# Output format: Artist/Book/

input_to_output = {}
for pdf in input_pdfs:
    parts = pdf.split(os.sep)
    if len(parts) >= 2:
        artist = parts[0]
        # Get the book name from the PDF filename (remove .pdf extension)
        book_pdf = parts[-1]
        book_name = book_pdf[:-4] if book_pdf.lower().endswith('.pdf') else book_pdf
        expected_output = f"{artist}/{book_name}"
        input_to_output[pdf] = expected_output

# Normalize output folders for comparison
normalized_output = {folder.replace('\\', '/'): folder for folder in output_folders}

# Find input PDFs without output folders
print("\n" + "=" * 80)
print("INPUT PDFs WITHOUT OUTPUT FOLDERS")
print("=" * 80)

missing_output = []
for pdf, expected_output in input_to_output.items():
    if expected_output not in normalized_output:
        missing_output.append((pdf, expected_output))
        if len(missing_output) <= 20:  # Show first 20
            print(f"  {pdf}")
            print(f"    Expected: {expected_output}")

if len(missing_output) > 20:
    print(f"  ... and {len(missing_output) - 20} more")

print(f"\nTotal: {len(missing_output)} input PDFs without output folders")

# Find output folders without input PDFs
print("\n" + "=" * 80)
print("OUTPUT FOLDERS WITHOUT INPUT PDFs")
print("=" * 80)

# Create reverse mapping: output folder to expected input PDF
output_to_input = {}
for folder in output_folders:
    parts = folder.split(os.sep)
    if len(parts) >= 2:
        artist = parts[0]
        book = parts[1]
        # Expected input could be Artist/Book.pdf
        expected_input = f"{artist}/{book}.pdf"
        output_to_input[folder] = expected_input

missing_input = []
for folder, expected_input in output_to_input.items():
    # Check if any input PDF matches this output folder
    found = False
    for pdf in input_pdfs:
        # Normalize paths for comparison
        pdf_normalized = pdf.replace('\\', '/')
        expected_normalized = expected_input.replace('\\', '/')
        
        # Check if the PDF matches the expected input
        if pdf_normalized == expected_normalized:
            found = True
            break
        
        # Also check if the PDF is in a subfolder but has the same book name
        pdf_parts = pdf_normalized.split('/')
        expected_parts = expected_normalized.split('/')
        if len(pdf_parts) >= 2 and len(expected_parts) >= 2:
            if pdf_parts[0] == expected_parts[0]:  # Same artist
                pdf_book = pdf_parts[-1][:-4] if pdf_parts[-1].endswith('.pdf') else pdf_parts[-1]
                expected_book = expected_parts[-1][:-4] if expected_parts[-1].endswith('.pdf') else expected_parts[-1]
                if pdf_book == expected_book:
                    found = True
                    break
    
    if not found:
        missing_input.append((folder, expected_input))
        if len(missing_input) <= 20:  # Show first 20
            print(f"  {folder}")
            print(f"    Expected input: {expected_input}")

if len(missing_input) > 20:
    print(f"  ... and {len(missing_input) - 20} more")

print(f"\nTotal: {len(missing_input)} output folders without input PDFs")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Input PDFs: {len(input_pdfs)}")
print(f"Output folders: {len(output_folders)}")
print(f"Difference: {len(output_folders) - len(input_pdfs)}")
print(f"\nInput PDFs without output: {len(missing_output)}")
print(f"Output folders without input: {len(missing_input)}")

# Save results to CSV
with open('input_output_comparison.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Type', 'Path', 'Expected'])
    
    for pdf, expected in missing_output:
        writer.writerow(['Missing Output', pdf, expected])
    
    for folder, expected in missing_input:
        writer.writerow(['Missing Input', folder, expected])

print(f"\nResults saved to: input_output_comparison.csv")
