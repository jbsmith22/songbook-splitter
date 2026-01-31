import csv
import os

# Read the duplicate CSV
duplicates = []
with open('duplicate_output_folders.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        duplicates.append(row)

print(f"Total duplicate cases: {len(duplicates)}")

# Categorize duplicates
identical_count = []  # Same PDF count
different_count = []  # Different PDF count

for dup in duplicates:
    count1 = int(dup['PDF Count 1'])
    count2 = int(dup['PDF Count 2'])
    
    if count1 == count2:
        identical_count.append(dup)
    else:
        different_count.append(dup)

print(f"\nIdentical PDF counts: {len(identical_count)}")
print(f"Different PDF counts: {len(different_count)}")

# Show some examples of identical counts
print("\n" + "=" * 80)
print("EXAMPLES OF IDENTICAL PDF COUNTS (likely true duplicates)")
print("=" * 80)

for dup in identical_count[:10]:
    print(f"\nInput: {dup['Input PDF']}")
    print(f"  Output 1: {dup['Output Folder 1']} ({dup['PDF Count 1']} PDFs)")
    print(f"  Output 2: {dup['Output Folder 2']} ({dup['PDF Count 2']} PDFs)")

# Show some examples of different counts
print("\n" + "=" * 80)
print("EXAMPLES OF DIFFERENT PDF COUNTS (need manual review)")
print("=" * 80)

for dup in different_count[:10]:
    print(f"\nInput: {dup['Input PDF']}")
    print(f"  Output 1: {dup['Output Folder 1']} ({dup['PDF Count 1']} PDFs)")
    print(f"  Output 2: {dup['Output Folder 2']} ({dup['PDF Count 2']} PDFs)")

# Save categorized results
with open('duplicates_identical_counts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Input PDF', 'Output Folder 1', 'PDF Count 1', 'Output Folder 2', 'PDF Count 2', 'Similarity', 'Action Needed'])
    writer.writeheader()
    writer.writerows(identical_count)

with open('duplicates_different_counts.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['Input PDF', 'Output Folder 1', 'PDF Count 1', 'Output Folder 2', 'PDF Count 2', 'Similarity', 'Action Needed'])
    writer.writeheader()
    writer.writerows(different_count)

print(f"\n\nResults saved to:")
print(f"  duplicates_identical_counts.csv ({len(identical_count)} cases)")
print(f"  duplicates_different_counts.csv ({len(different_count)} cases)")
