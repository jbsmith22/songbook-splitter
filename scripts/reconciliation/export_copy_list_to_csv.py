"""
Export the list of files to copy to S3 as a CSV
"""
import json
import csv

# Load decisions
print("Loading decisions...")
with open('reconciliation_decisions_poor_folders_2026-02-02.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

decisions = data['decisions']

# Collect all files
files_to_copy = []

for folder_path, folder_data in decisions.items():
    file_decisions = folder_data.get('fileDecisions', {})

    for filename, file_info in file_decisions.items():
        if file_info['action'] == 'copy-to-s3':
            files_to_copy.append({
                'Folder (Local)': file_info['local_path'],
                'Folder (S3)': file_info['s3_path'],
                'Filename': filename,
                'Book ID': file_info.get('book_id', ''),
                'Action': 'copy-to-s3',
                'Status': file_info.get('status', 'local-only')
            })

# Sort by folder and filename
files_to_copy.sort(key=lambda x: (x['Folder (Local)'], x['Filename']))

# Write CSV
output_file = 'poor_folders_copy_list.csv'
print(f"Writing {len(files_to_copy)} files to {output_file}...")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    if files_to_copy:
        fieldnames = ['Folder (Local)', 'Folder (S3)', 'Filename', 'Book ID', 'Action', 'Status']
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(files_to_copy)

print(f"\nDone! Exported {len(files_to_copy)} files to {output_file}")
print(f"\nSummary:")
print(f"  Total files: {len(files_to_copy)}")
print(f"  Unique folders: {len(set(f['Folder (Local)'] for f in files_to_copy))}")
