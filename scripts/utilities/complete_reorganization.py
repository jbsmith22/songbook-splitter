"""
Complete Project Reorganization - Phase 2
Moves remaining files from root to organized structure.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(r"d:\Work\songbook-splitter")

# Essential files that MUST stay in root
ESSENTIAL_ROOT_FILES = {
    '.gitignore',
    'README.md',
    'START_HERE.md',
    'Dockerfile',
    'requirements.txt',
    'PROJECT_CHECKPOINT_2026-01-31.md',  # Latest checkpoint
    'PROJECT_CONTEXT.md',
    'OPERATOR_RUNBOOK.md',
    'REORGANIZATION_REPORT.md',
    'complete_reorganization.py',  # This script
    'reorganize_project.py',  # Previous script
}

# Protected directories - don't move these
PROTECTED_DIRS = {
    'app', 'lambda', 'ecs', 'infra', 'tests',
    'build', 'data', 'docs', 'logs', 'scripts', 'web',
    '.git', '.kiro', '.claude', '.pytest_cache', '.vscode',
    'SheetMusic', 'ProcessedSongs', 'SheetMusicIndividualSheets',
    'output', 'toc_cache', 'verification_batches',
    'temp_anthology_output', 'temp_anthology_pages',
    '__pycache__'
}

# Categorization rules for remaining files
FILE_RULES = {
    # Execution and state files
    'data/execution': {
        'patterns': [
            '*-execution*.json',
            'anthology-execution*.json',
            'billy-joel-execution*.json',
            'execution-result-*.json',
            'current_state_machine*.json',
            'demo_feedback*.json',
        ]
    },

    # Database backups
    'data/backups': {
        'patterns': [
            'dynamodb_backup_*.json',
            '*.backup',
            'backup_*.json',
        ]
    },

    # Analysis and reports
    'data/analysis': {
        'patterns': [
            'complete_page_lineage.json',
            'page_gap_analysis.json',
            'page_mapping_*.json',
            'complete-inventory-report.txt',
            'book_reconciliation.xlsx',
        ]
    },

    # Summary and status documents
    'docs/summaries': {
        'patterns': [
            '*-summary*.md',
            'inventory-summary.md',
            '11-books-downloaded-summary.md',
        ]
    },

    # Updates and changes
    'docs/updates': {
        'patterns': [
            '*_UPDATE*.md',
            'CONCURRENCY_UPDATE.md',
        ]
    },

    # Comparison and mismatch documents
    'docs/analysis': {
        'patterns': [
            'LOCAL_VS_*.md',
            '*_MISMATCHES.md',
            '*_COMPARISON*.md',
        ]
    },

    # Build and deployment artifacts
    'build': {
        'patterns': [
            'lambda-deployment.zip',
            '*.whl',
            '*.egg',
        ]
    },

    # Numbered files (like "50")
    'data/misc': {
        'patterns': [
            '50',
            '*.tmp',
        ]
    },
}

# Track moves
moves_log = []
errors_log = []
skipped_log = []

def matches_any_pattern(filename, patterns):
    """Check if filename matches any of the glob patterns."""
    import fnmatch
    for pattern in patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True
    return False

def should_keep_in_root(name):
    """Check if file/dir should stay in root."""
    return name in ESSENTIAL_ROOT_FILES or name in PROTECTED_DIRS

def move_file(source, target_dir):
    """Move a file to target directory."""
    target_path = BASE_DIR / target_dir / source.name

    # Skip if already in target
    if source.parent == (BASE_DIR / target_dir):
        return None

    # Skip if file should stay in root
    if should_keep_in_root(source.name):
        skipped_log.append((source.name, 'Essential root file'))
        return None

    try:
        # Create target directory if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if target already exists
        if target_path.exists():
            # If identical, just delete source
            if source.stat().st_size == target_path.stat().st_size:
                source.unlink()
                moves_log.append((source.name, target_dir, 'deleted duplicate'))
                return target_path
            else:
                # Rename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_name = f"{source.stem}_{timestamp}{source.suffix}"
                target_path = target_path.parent / new_name

        # Move the file
        shutil.move(str(source), str(target_path))
        moves_log.append((source.name, target_dir, 'moved'))
        return target_path
    except Exception as e:
        errors_log.append((source.name, target_dir, str(e)))
        return None

def find_and_move_by_rules():
    """Find and move files based on categorization rules."""
    print("\nMoving remaining files by rules...")

    for target_dir, config in FILE_RULES.items():
        patterns = config['patterns']
        print(f"\n{target_dir}:")
        moved_count = 0

        # Find all matching files in root
        for item in BASE_DIR.iterdir():
            if item.is_file():
                if matches_any_pattern(item.name, patterns):
                    result = move_file(item, target_dir)
                    if result:
                        print(f"  Moved: {item.name}")
                        moved_count += 1

        if moved_count == 0:
            print(f"  (no files matched)")

def move_remaining_json_files():
    """Move any remaining JSON files to data/misc."""
    print("\ndata/misc (remaining JSON files):")
    moved_count = 0

    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == '.json':
            if not should_keep_in_root(item.name):
                result = move_file(item, 'data/misc')
                if result:
                    print(f"  Moved: {item.name}")
                    moved_count += 1

    if moved_count == 0:
        print(f"  (no files)")

def move_remaining_md_files():
    """Move any remaining MD files to docs/archive."""
    print("\ndocs/archive (remaining markdown files):")
    moved_count = 0

    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == '.md':
            if not should_keep_in_root(item.name):
                result = move_file(item, 'docs/archive')
                if result:
                    print(f"  Moved: {item.name}")
                    moved_count += 1

    if moved_count == 0:
        print(f"  (no files)")

def list_remaining_root_files():
    """List what's left in root."""
    print("\n" + "=" * 70)
    print("FILES REMAINING IN ROOT")
    print("=" * 70)

    root_files = []
    root_dirs = []

    for item in BASE_DIR.iterdir():
        if item.name.startswith('.'):
            continue
        if item.is_file():
            root_files.append(item.name)
        elif item.is_dir() and item.name not in PROTECTED_DIRS:
            root_dirs.append(item.name)

    print(f"\nFiles in root: {len(root_files)}")
    if root_files:
        for f in sorted(root_files):
            size = (BASE_DIR / f).stat().st_size
            print(f"  - {f} ({size:,} bytes)")

    print(f"\nDirectories in root: {len(root_dirs)}")
    if root_dirs:
        for d in sorted(root_dirs):
            print(f"  - {d}/")

def generate_completion_report():
    """Generate completion report."""
    report_path = BASE_DIR / 'REORGANIZATION_PHASE2_REPORT.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Project Reorganization - Phase 2 Completion\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Files Moved**: {len([m for m in moves_log if m[2] == 'moved'])}\n")
        f.write(f"- **Duplicates Deleted**: {len([m for m in moves_log if m[2] == 'deleted duplicate'])}\n")
        f.write(f"- **Files Skipped**: {len(skipped_log)}\n")
        f.write(f"- **Errors**: {len(errors_log)}\n\n")

        if moves_log:
            f.write(f"## Moved/Deleted Files ({len(moves_log)})\n\n")

            # Group by target directory
            by_target = {}
            for item, target, action in moves_log:
                if target not in by_target:
                    by_target[target] = []
                by_target[target].append((item, action))

            for target in sorted(by_target.keys()):
                f.write(f"### {target}/ ({len(by_target[target])} items)\n\n")
                for item, action in sorted(by_target[target]):
                    f.write(f"- {item} ({action})\n")
                f.write("\n")

        if skipped_log:
            f.write(f"## Skipped Files ({len(skipped_log)})\n\n")
            for item, reason in skipped_log:
                f.write(f"- {item}: {reason}\n")
            f.write("\n")

        if errors_log:
            f.write(f"## Errors ({len(errors_log)})\n\n")
            for item, target, error in errors_log:
                f.write(f"- **{item}** -> {target}: {error}\n")

    return report_path

def main():
    """Main completion process."""
    print("=" * 70)
    print("PROJECT REORGANIZATION - PHASE 2 COMPLETION")
    print("=" * 70)
    print(f"\nBase directory: {BASE_DIR}")
    print(f"\nEssential root files: {', '.join(sorted(ESSENTIAL_ROOT_FILES))}")

    # Move files by rules
    find_and_move_by_rules()

    # Move remaining JSON files
    move_remaining_json_files()

    # Move remaining MD files
    move_remaining_md_files()

    # List what's left
    list_remaining_root_files()

    # Generate report
    report_path = generate_completion_report()

    # Summary
    print("\n" + "=" * 70)
    print("PHASE 2 COMPLETION SUMMARY")
    print("=" * 70)
    print(f"\nMoved: {len([m for m in moves_log if m[2] == 'moved'])} files")
    print(f"Deleted duplicates: {len([m for m in moves_log if m[2] == 'deleted duplicate'])} files")
    print(f"Skipped: {len(skipped_log)} files")
    if errors_log:
        print(f"Errors: {len(errors_log)} files")
    print(f"\nReport: {report_path.name}")

if __name__ == "__main__":
    main()
