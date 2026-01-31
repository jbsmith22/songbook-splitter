#!/usr/bin/env python3
"""
Generate a random sample of PDFs for verification testing.
"""

import random
from pathlib import Path

def get_all_pdfs(base_path: Path):
    """Get all PDF files recursively."""
    return list(base_path.glob("**/*.pdf"))

def generate_sample(base_path: Path, sample_size: int, output_file: Path):
    """Generate random sample of PDFs."""
    
    print(f"Scanning {base_path} for PDFs...")
    all_pdfs = get_all_pdfs(base_path)
    
    print(f"Found {len(all_pdfs)} total PDFs")
    
    if len(all_pdfs) < sample_size:
        print(f"Warning: Only {len(all_pdfs)} PDFs available, using all of them")
        sample_size = len(all_pdfs)
    
    # Random sample
    sample = random.sample(all_pdfs, sample_size)
    
    # Convert to relative paths
    relative_paths = []
    for pdf in sample:
        try:
            rel_path = pdf.relative_to(base_path)
            relative_paths.append(str(rel_path).replace('\\', '/'))
        except ValueError:
            print(f"Warning: Could not get relative path for {pdf}")
    
    # Sort for readability
    relative_paths.sort()
    
    # Write to file
    with open(output_file, 'w') as f:
        for path in relative_paths:
            f.write(path + '\n')
    
    print(f"\n✓ Generated sample of {len(relative_paths)} PDFs")
    print(f"✓ Saved to: {output_file}")
    print(f"\nTo run verification:")
    print(f"  py run_verification_with_output.py {output_file}")
    
    # Show some examples
    print(f"\nSample includes:")
    for i, path in enumerate(relative_paths[:5], 1):
        print(f"  {i}. {path}")
    if len(relative_paths) > 5:
        print(f"  ... and {len(relative_paths) - 5} more")


if __name__ == "__main__":
    import sys
    
    base_path = Path("c:/Work/AWSMusic/ProcessedSongs")
    
    if len(sys.argv) > 1:
        sample_size = int(sys.argv[1])
    else:
        sample_size = 100
    
    output_file = Path(f"random_sample_{sample_size}.txt")
    
    if not base_path.exists():
        print(f"Error: {base_path} not found")
        sys.exit(1)
    
    # Set random seed for reproducibility (optional)
    random.seed(42)
    
    generate_sample(base_path, sample_size, output_file)
