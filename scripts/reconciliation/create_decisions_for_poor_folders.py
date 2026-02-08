"""
Create reconciliation decisions for POOR folders with S3=0 files
Copy all local files to S3 for these folders
"""
import json
from pathlib import Path

# Load match quality data
print("Loading match quality data...")
with open('data/analysis/match_quality_data.json', 'r', encoding='utf-8') as f:
    match_data = json.load(f)

# Get POOR tier folders
poor_folders = match_data['quality_tiers']['poor']
print(f"Found {len(poor_folders)} POOR folders")

# Create decisions
decisions = {}
total_files = 0
folders_with_zero_s3 = []

LOCAL_ROOT = Path('d:/Work/songbook-splitter/ProcessedSongs')

for folder_data in poor_folders:
    local_path = folder_data['local_path']
    s3_path = folder_data['s3_path']

    # Check file counts
    local_count = folder_data.get('local_songs', 0)
    s3_count = folder_data.get('s3_songs', 0)

    # Focus on folders with S3=0
    if s3_count == 0 and local_count > 0:
        folders_with_zero_s3.append(local_path)

        # Get all local files
        local_folder = LOCAL_ROOT / local_path
        if not local_folder.exists():
            print(f"  WARNING: Local folder doesn't exist: {local_folder}")
            continue

        # Get all PDF files
        pdf_files = sorted(local_folder.glob('*.pdf'))

        if not pdf_files:
            print(f"  WARNING: No PDF files in: {local_folder}")
            continue

        # Create file decisions
        file_decisions = {}
        book_id = folder_data.get('book_id', '')

        for pdf_file in pdf_files:
            file_decisions[pdf_file.name] = {
                'action': 'copy-to-s3',
                'status': 'local-only',
                'filepath': pdf_file.name,
                'local_path': local_path,
                's3_path': s3_path,
                'book_id': book_id
            }

        decisions[local_path] = {
            'fileDecisions': file_decisions
        }

        total_files += len(pdf_files)
        print(f"  {local_path}: {len(pdf_files)} files to copy to S3")

print(f"\n{'='*80}")
print(f"SUMMARY")
print(f"{'='*80}")
print(f"POOR folders with S3=0: {len(folders_with_zero_s3)}")
print(f"Folders with decisions: {len(decisions)}")
print(f"Total files to copy to S3: {total_files}")

# Create output file
output = {
    'timestamp': '2026-02-02',
    'source': 'Auto-generated from POOR folders with S3=0 files',
    'decisions': decisions
}

output_file = 'reconciliation_decisions_poor_folders_2026-02-02.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2)

print(f"\nDecisions saved to: {output_file}")
print(f"\nTo execute: py scripts/reconciliation/execute_decisions.py {output_file} --yes")
