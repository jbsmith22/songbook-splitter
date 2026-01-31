"""
Sync Original Structure to Match My Organization
Run this script in C:\Work\AWSMusic to reorganize to match D:\Work\songbook-splitter
"""

import os
import shutil
from pathlib import Path

# Base directory - UPDATE THIS to point to the original location
BASE_DIR = Path(r"C:\Work\AWSMusic")

def move_with_mkdir(source, target):
    """Move file/directory, creating parent directories as needed."""
    source_path = BASE_DIR / source
    target_path = BASE_DIR / target

    if not source_path.exists():
        print(f"  SKIP (not found): {source}")
        return False

    # Create parent directory
    target_path.parent.mkdir(parents=True, exist_ok=True)

    # Move
    try:
        shutil.move(str(source_path), str(target_path))
        print(f"  Moved: {source} -> {target}")
        return True
    except Exception as e:
        print(f"  ERROR: {source} -> {target}: {e}")
        return False

def main():
    """Execute reorganization to match the new structure."""
    print("=" * 70)
    print("REORGANIZATION: Match D:\\Work\\songbook-splitter Structure")
    print("=" * 70)
    print(f"\nBase directory: {BASE_DIR}")
    print()

    if not BASE_DIR.exists():
        print(f"ERROR: Directory {BASE_DIR} does not exist!")
        print("Please update BASE_DIR in the script to point to your original location.")
        return

    input("Press Enter to continue with reorganization (Ctrl+C to cancel)...")

    moves_count = 0

    # 1. Move working directories from data/ to root
    print("\n1. Moving working directories from data/ to root:")
    working_dirs = [
        ('data/ProcessedSongs', 'ProcessedSongs'),
        ('data/SheetMusic', 'SheetMusic'),
        ('data/SheetMusicIndividualSheets', 'SheetMusicIndividualSheets'),
        ('data/output', 'output'),
        ('data/temp_anthology_output', 'temp_anthology_output'),
        ('data/temp_anthology_pages', 'temp_anthology_pages'),
        ('data/toc_cache', 'toc_cache'),
        ('data/verification_batches', 'verification_batches'),
    ]

    for source, target in working_dirs:
        if move_with_mkdir(source, target):
            moves_count += 1

    # 2. Move build artifacts to build/ directory
    print("\n2. Moving build artifacts to build/ directory:")
    build_artifacts = [
        ('lambda-deployment.zip', 'build/lambda-deployment.zip'),
        ('lambda-package', 'build/lambda-package'),
    ]

    for source, target in build_artifacts:
        if move_with_mkdir(source, target):
            moves_count += 1

    # 3. Move verification_results to web/verification/
    print("\n3. Moving verification results to web/verification/:")
    verification_moves = [
        ('data/verification_results', 'web/verification/verification_results'),
    ]

    for source, target in verification_moves:
        if move_with_mkdir(source, target):
            moves_count += 1

    # 4. Create data/downloads if it doesn't exist
    print("\n4. Creating additional subdirectories:")
    additional_dirs = [
        'data/downloads',
    ]

    for dir_path in additional_dirs:
        full_path = BASE_DIR / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")

    # 5. Ensure all subdirectory structure exists
    print("\n5. Ensuring all subdirectory structure exists:")

    all_dirs = [
        # data subdirectories
        'data/analysis',
        'data/backups',
        'data/comparisons',
        'data/downloads',
        'data/execution',
        'data/inventories',
        'data/misc',
        'data/processing',
        'data/reconciliation',
        'data/samples',

        # docs subdirectories
        'docs/analysis',
        'docs/archive',
        'docs/comparisons',
        'docs/deployment',
        'docs/design',
        'docs/issues-resolved',
        'docs/operations',
        'docs/plans',
        'docs/project-status',
        'docs/s3',
        'docs/summaries',
        'docs/updates',

        # scripts subdirectories
        'scripts/aws',
        'scripts/aws/downloading',
        'scripts/aws/monitoring',
        'scripts/aws/processing',
        'scripts/s3',
        'scripts/analysis',
        'scripts/local',
        'scripts/testing',
        'scripts/utilities',
        'scripts/one-off',

        # logs subdirectories
        'logs/processing',
        'logs/reorganization',
        'logs/testing',
        'logs/misc',

        # web subdirectories
        'web/s3-browser',
        'web/verification',
        'web/viewers',

        # tests
        'tests/fixtures',

        # build
        'build',
    ]

    for dir_path in all_dirs:
        full_path = BASE_DIR / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")

    # Summary
    print("\n" + "=" * 70)
    print("REORGANIZATION COMPLETE")
    print("=" * 70)
    print(f"\nMajor moves completed: {moves_count}")
    print()
    print("Your structure now matches D:\\Work\\songbook-splitter:")
    print("  - Working directories moved from data/ to root")
    print("  - Build artifacts moved to build/")
    print("  - Verification results moved to web/verification/")
    print("  - All subdirectory structure created")
    print()
    print("Next steps:")
    print("  1. Verify the reorganization with a folder comparison tool")
    print("  2. Run 'git status' to see the changes")
    print("  3. If satisfied, commit: 'git add -A && git commit -m \"Reorganize to match structure\"'")

if __name__ == "__main__":
    main()
