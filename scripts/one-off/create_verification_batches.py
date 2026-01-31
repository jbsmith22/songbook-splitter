#!/usr/bin/env python3
"""
Create batches of PDFs for verification, grouped by artist.
Each batch will be 1,000-2,000 PDFs, keeping artists together.
"""

from pathlib import Path
from collections import defaultdict
import json

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
MIN_BATCH_SIZE = 1000
MAX_BATCH_SIZE = 2000

def get_all_pdfs_by_artist():
    """Get all PDFs grouped by artist."""
    pdfs_by_artist = defaultdict(list)
    
    for artist_dir in PROCESSED_SONGS_PATH.iterdir():
        if not artist_dir.is_dir():
            continue
        
        artist_name = artist_dir.name
        
        # Find all PDFs for this artist
        for pdf_file in artist_dir.rglob("*.pdf"):
            pdfs_by_artist[artist_name].append(pdf_file)
    
    return pdfs_by_artist

def create_batches(pdfs_by_artist):
    """Create batches of 1,000-2,000 PDFs, keeping artists together."""
    batches = []
    current_batch = []
    current_size = 0
    
    # Sort artists by number of PDFs (largest first) for better packing
    sorted_artists = sorted(pdfs_by_artist.items(), key=lambda x: len(x[1]), reverse=True)
    
    for artist, pdfs in sorted_artists:
        artist_size = len(pdfs)
        
        # If this artist alone exceeds MAX_BATCH_SIZE, put it in its own batch(es)
        if artist_size > MAX_BATCH_SIZE:
            # Split large artist into multiple batches
            for i in range(0, artist_size, MAX_BATCH_SIZE):
                chunk = pdfs[i:i + MAX_BATCH_SIZE]
                batches.append({
                    'artists': [artist],
                    'pdfs': chunk,
                    'size': len(chunk)
                })
            continue
        
        # If adding this artist would exceed MAX_BATCH_SIZE, start new batch
        if current_size + artist_size > MAX_BATCH_SIZE and current_size >= MIN_BATCH_SIZE:
            batches.append({
                'artists': list(set(pdf.parts[-3] for pdf in current_batch)),
                'pdfs': current_batch,
                'size': current_size
            })
            current_batch = []
            current_size = 0
        
        # Add artist to current batch
        current_batch.extend(pdfs)
        current_size += artist_size
    
    # Add final batch if not empty
    if current_batch:
        batches.append({
            'artists': list(set(pdf.parts[-3] for pdf in current_batch)),
            'pdfs': current_batch,
            'size': current_size
        })
    
    return batches

def create_batch_files(batches):
    """Create batch scripts and file lists."""
    
    # Create batches directory
    batches_dir = Path("verification_batches")
    batches_dir.mkdir(exist_ok=True)
    
    print(f"Creating {len(batches)} batches...")
    print("=" * 80)
    
    for i, batch in enumerate(batches, 1):
        batch_num = i
        
        # Create file list
        file_list_path = batches_dir / f"batch{batch_num}_files.txt"
        with open(file_list_path, 'w') as f:
            for pdf in batch['pdfs']:
                f.write(f"{pdf}\n")
        
        # Create PowerShell batch script
        batch_script_path = batches_dir / f"batch{batch_num}.ps1"
        script_content = f"""# Batch {batch_num} - {batch['size']} PDFs
# Artists: {', '.join(batch['artists'][:5])}{'...' if len(batch['artists']) > 5 else ''}

Write-Host "=" * 80
Write-Host "Starting Batch {batch_num}"
Write-Host "PDFs: {batch['size']}"
Write-Host "Artists: {len(batch['artists'])}"
Write-Host "=" * 80

# Change to parent directory where the Python scripts are
Set-Location ..

# Run verification
py run_verification_with_output.py verification_batches/batch{batch_num}_files.txt

# Generate review page
py generate_review_page.py

# Rename output files to include batch number
Move-Item -Force verification_results/bedrock_results.json verification_results/batch{batch_num}_results.json
Move-Item -Force verification_results/review_page.html verification_results/batch{batch_num}_review.html

Write-Host ""
Write-Host "Batch {batch_num} complete!"
Write-Host "Review at: verification_results/batch{batch_num}_review.html"
Write-Host ""
"""
        
        with open(batch_script_path, 'w') as f:
            f.write(script_content)
        
        print(f"Batch {batch_num}:")
        print(f"  PDFs: {batch['size']}")
        print(f"  Artists: {len(batch['artists'])}")
        print(f"  Top artists: {', '.join(batch['artists'][:3])}")
        print(f"  Script: {batch_script_path}")
        print()
    
    # Create master run-all script
    master_script_path = batches_dir / "run_all_batches.ps1"
    master_content = f"""# Run all verification batches sequentially
# Total batches: {len(batches)}

$batches = @(
"""
    
    for i in range(1, len(batches) + 1):
        master_content += f'    "batch{i}.ps1"' + (',\n' if i < len(batches) else '\n')
    
    master_content += """)

foreach ($batch in $batches) {
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "Running $batch"
    Write-Host "=" * 80
    Write-Host ""
    
    & ".\\$batch"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error running $batch - stopping"
        exit 1
    }
}

Write-Host ""
Write-Host "=" * 80
Write-Host "All batches complete!"
Write-Host "=" * 80
Write-Host ""
Write-Host "Review pages:"
"""
    
    for i in range(1, len(batches) + 1):
        master_content += f'Write-Host "  Batch {i}: verification_results/batch{i}_review.html"\n'
    
    with open(master_script_path, 'w') as f:
        f.write(master_content)
    
    print("=" * 80)
    print(f"Created master script: {master_script_path}")
    print()
    print("To run all batches:")
    print(f"  cd verification_batches")
    print(f"  .\\run_all_batches.ps1")
    print()
    print("Or run individual batches:")
    for i in range(1, min(4, len(batches) + 1)):
        print(f"  .\\batch{i}.ps1")
    
    # Create summary JSON
    summary = {
        'total_batches': len(batches),
        'total_pdfs': sum(b['size'] for b in batches),
        'batches': [
            {
                'batch_num': i,
                'size': b['size'],
                'artists': b['artists']
            }
            for i, b in enumerate(batches, 1)
        ]
    }
    
    summary_path = batches_dir / "batch_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nBatch summary saved to: {summary_path}")

if __name__ == "__main__":
    print("Scanning ProcessedSongs directory...")
    pdfs_by_artist = get_all_pdfs_by_artist()
    
    total_pdfs = sum(len(pdfs) for pdfs in pdfs_by_artist.values())
    print(f"Found {total_pdfs} PDFs across {len(pdfs_by_artist)} artists")
    print()
    
    print("Creating batches...")
    batches = create_batches(pdfs_by_artist)
    
    print()
    create_batch_files(batches)
