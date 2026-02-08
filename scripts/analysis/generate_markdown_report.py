#!/usr/bin/env python3
"""Generate markdown report from V2 analysis."""
import json
from pathlib import Path

# Load V2 analysis
with open('data/analysis/v2_only_analysis.json') as f:
    data = json.load(f)

output = Path('data/analysis/V2_COMPREHENSIVE_REPORT.md')
with open(output, 'w', encoding='utf-8') as f:
    f.write('# V2 Pipeline Comprehensive Report\n')
    f.write('**Direct Observation Only - No Inferences**\n\n')
    f.write(f'Generated: 2026-02-06\n\n')

    # Summary
    f.write('## Summary\n\n')
    summary = data['summary']
    f.write(f'- **Total V2 Books:** {summary["total_books"]}\n')
    f.write(f'- **Books with verified_songs:** {summary["with_verified_songs"]} ({summary["with_verified_songs"]/summary["total_books"]*100:.0f}%)\n')
    f.write(f'- **Books with output_files:** {summary["with_output_files"]} ({summary["with_output_files"]/summary["total_books"]*100:.0f}%)\n')
    f.write(f'- **Books with local manifest:** {summary["with_local_manifest"]} ({summary["with_local_manifest"]/summary["total_books"]*100:.0f}%)\n')
    f.write(f'- **Exact matches (S3 = Local):** {summary["exact_matches"]} ({summary["exact_matches"]/summary["total_books"]*100:.0f}%)\n\n')

    # Issues
    mismatches = [b for b in data['books'] if b['local_manifest'] and b['output_files_count'] != b['local_pdfs_count']]
    no_local = [b for b in data['books'] if not b['local_manifest']]

    f.write('## Issues Found\n\n')
    f.write(f'### Books with Mismatches ({len(mismatches)})\n\n')
    if mismatches:
        f.write('| Book ID | S3 Output Files | Local PDFs | Local Folder |\n')
        f.write('|---------|-----------------|------------|--------------|\n')
        for b in mismatches:
            f.write(f'| {b["book_id"]} | {b["output_files_count"]} | {b["local_pdfs_count"]} | {b["local_manifest"]["folder"]} |\n')
    f.write('\n')

    f.write(f'### Books Without Local Manifest ({len(no_local)})\n\n')
    if no_local:
        f.write('| Book ID | Verified Songs | Output Files |\n')
        f.write('|---------|----------------|--------------|\\n')
        for b in no_local:
            f.write(f'| {b["book_id"]} | {b["verified_songs_count"]} | {b["output_files_count"]} |\n')
    f.write('\n')

    # Perfect matches
    perfect = [b for b in data['books'] if b['local_manifest'] and b['output_files_count'] == b['local_pdfs_count']]
    f.write(f'### Perfect Matches ({len(perfect)})\n\n')
    f.write('Books where S3 output_files count exactly matches local PDF count.\n\n')
    f.write('| Book ID | Count | Local Folder |\n')
    f.write('|---------|-------|--------------|\\n')
    for b in perfect[:20]:  # Show first 20
        f.write(f'| {b["book_id"]} | {b["output_files_count"]} | {b["local_manifest"]["folder"]} |\n')
    if len(perfect) > 20:
        f.write(f'\n*...and {len(perfect) - 20} more*\n')
    f.write('\n')

print(f'Markdown report created: {output}')
print(f'  - {len(perfect)} perfect matches')
print(f'  - {len(mismatches)} mismatches')
print(f'  - {len(no_local)} without local manifest')
