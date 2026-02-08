"""
Check FOUND_LOCAL folders for manifests and update mapping
"""
import csv
import json
from pathlib import Path

# Read the complete mapping
rows = []
with open('data/analysis/provenance_complete_mapping.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rows.append(row)

# Get FOUND_LOCAL entries
found_local = [r for r in rows if r['status'] == 'FOUND_LOCAL']

print(f'Checking {len(found_local)} FOUND_LOCAL folders for manifests/book_ids...\n')

# Check ProcessedSongs for manifests
active_root = Path(r'd:\Work\songbook-splitter\ProcessedSongs')

for local_row in found_local:
    local_folder = local_row['local_folder']
    folder_path = active_root / local_folder.replace('/', '\\')

    if folder_path.exists():
        # Look for manifest.json
        manifest_path = folder_path / 'manifest.json'
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                    book_id = manifest.get('book_id', 'NONE')
                    print(f'{local_folder}')
                    print(f'  Has manifest: YES')
                    print(f'  Book ID: {book_id}')

                    # Update the row
                    for row in rows:
                        if row['local_folder'] == local_folder and row['status'] == 'FOUND_LOCAL':
                            row['book_id'] = book_id
                            row['s3_folder'] = 'LOCAL_ONLY'
                            break
            except Exception as e:
                print(f'{local_folder}: Manifest error - {e}')
        else:
            print(f'{local_folder}')
            print(f'  Has manifest: NO')
            # Update to LOCAL_ONLY
            for row in rows:
                if row['local_folder'] == local_folder and row['status'] == 'FOUND_LOCAL':
                    row['s3_folder'] = 'LOCAL_ONLY'
                    row['book_id'] = 'NONE'
                    break

# Save updated mapping
with open('data/analysis/provenance_complete_mapping.csv', 'w', newline='', encoding='utf-8') as f:
    fieldnames = ['source_pdf', 'local_folder', 's3_folder', 'book_id', 'status']
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'\n{"="*80}')
print('FOUND_LOCAL UPDATE SUMMARY')
print(f'{"="*80}')
print(f'Total FOUND_LOCAL folders: {len(found_local)}')
print(f'With manifests: {sum(1 for r in rows if r["status"] == "FOUND_LOCAL" and r["book_id"] != "NONE")}')
print(f'Without manifests: {sum(1 for r in rows if r["status"] == "FOUND_LOCAL" and r["book_id"] == "NONE")}')
print(f'\nAll FOUND_LOCAL folders marked as LOCAL_ONLY for S3')
print('Updated mapping saved to: provenance_complete_mapping.csv')
