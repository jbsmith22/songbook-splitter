"""
Final Cleanup - Move last remaining non-essential files from root.
"""

import os
import shutil
from pathlib import Path

BASE_DIR = Path(r"d:\Work\songbook-splitter")

# Final cleanup moves
FINAL_MOVES = {
    # Comparison reports
    'docs/comparisons': [
        'Report.html',
        'Report.xml',
    ],

    # Analysis comparison files
    'data/comparisons': [
        's3-local-comparison-20260127-004047.txt',
        's3-local-comparison-20260127-004117.txt',
        's3_folders_not_in_local.txt',
    ],

    # Sample data
    'data/samples': [
        'random_sample_100.txt',
    ],

    # Test fixtures
    'tests/fixtures': [
        'test-james-taylor-fire-and-rain.pdf',
        'test_5_known_errors.txt',
    ],

    # Reorganization scripts to utilities
    'scripts/utilities': [
        'reorganize_project.py',
        'complete_reorganization.py',
        'final_cleanup.py',  # This script itself
    ],

    # Empty temp files to logs
    'logs/misc': [
        'temp-logs.txt',
    ],
}

moves_count = 0
errors_count = 0

def move_file(filename, target_dir):
    """Move a file to target directory."""
    global moves_count, errors_count

    source = BASE_DIR / filename
    if not source.exists():
        print(f"  SKIP (not found): {filename}")
        return

    target_path = BASE_DIR / target_dir / filename

    try:
        # Create target directory
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        shutil.move(str(source), str(target_path))
        print(f"  Moved: {filename} -> {target_dir}/")
        moves_count += 1
    except Exception as e:
        print(f"  ERROR: {filename} - {e}")
        errors_count += 1

def main():
    """Execute final cleanup."""
    print("=" * 70)
    print("FINAL CLEANUP - PHASE 3")
    print("=" * 70)

    for target_dir, files in FINAL_MOVES.items():
        print(f"\n{target_dir}:")
        for filename in files:
            move_file(filename, target_dir)

    # List final root contents
    print("\n" + "=" * 70)
    print("FINAL ROOT CONTENTS")
    print("=" * 70)

    root_files = []
    for item in BASE_DIR.iterdir():
        if item.is_file() and not item.name.startswith('.'):
            root_files.append(item.name)

    print(f"\nFiles in root: {len(root_files)}")
    for f in sorted(root_files):
        print(f"  - {f}")

    # Summary
    print("\n" + "=" * 70)
    print("FINAL CLEANUP COMPLETE")
    print("=" * 70)
    print(f"\nMoved: {moves_count} files")
    print(f"Errors: {errors_count} files")
    print(f"Remaining in root: {len(root_files)} files")

if __name__ == "__main__":
    main()
