"""
Project Reorganization Script
Reorganizes the songbook-splitter project directory into a clean structure.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime

# Base directory
BASE_DIR = Path(r"d:\Work\songbook-splitter")

# Core directories to NOT move
PROTECTED_DIRS = {
    'app', 'lambda', 'ecs', 'infra', 'tests',
    '.git', '.kiro', 'SheetMusic', 'ProcessedSongs',
    'SheetMusicIndividualSheets', 'output', 'toc_cache',
    '__pycache__', '.pytest_cache', 'verification_batches'
}

# Files to keep in root
KEEP_IN_ROOT = {
    '.gitignore', 'README.md', 'START_HERE.md', 'Dockerfile',
    'requirements.txt', 'PROJECT_CHECKPOINT_2026-01-31.md',
    'PROJECT_CONTEXT.md', 'OPERATOR_RUNBOOK.md',
    'reorganize_project.py'  # This script itself
}

# Reorganization mapping
REORGANIZATION = {
    # Documentation
    'docs/project-status': [
        'PROJECT_CHECKPOINT_*.md',
        'PROJECT_STATUS_*.md',
        'CURRENT_STATUS_*.md',
        'SESSION_SUMMARY.md',
        'INVENTORY_STATUS.md',
    ],
    'docs/operations': [
        'OPERATOR_RUNBOOK.md',
        'DEPLOYMENT_COMPLETE.md',
        'AUTO_SPLIT_GUIDE.md',
        'BATCH_PROCESSING_README.md',
        'BULK_SPLIT_OPERATIONS_GUIDE.md',
        'BOOK_REVIEW_README.md',
        'VERIFICATION_REVIEW_GUIDE.md',
        'READ_ME_FIRST.md',
        'READY_TO_TEST.md',
    ],
    'docs/analysis': [
        '*_ANALYSIS.md',
        '*_SUMMARY.md',
        'AWS_PIPELINE_SUCCESS.md',
        'AWS_PIPELINE_TEST_RESULTS.md',
        'PIPELINE_SUCCESS.md',
        'ROOT_CAUSE_ANALYSIS.md',
        'CORRECTED_*.md',
        'MATCH_REVIEW_SUMMARY.md',
    ],
    'docs/deployment': [
        'DEPLOYMENT_*.md',
        'COMPLETE_PIPELINE_DEPLOYMENT.md',
    ],
    'docs/issues-resolved': [
        'CURRENT_ISSUES.md',
        '*_FIX*.md',
        '*_RESOLVED.md',
        '*_COMPLETE.md',
        'ALGORITHM_FIX_APPLIED.md',
        'ARTIST_NAME_FIX.md',
        'CASE_MISMATCH_FIX_COMPLETE.md',
        'DYNAMODB_SYNC_COMPLETE.md',
        'EMPTY_FOLDERS_RESOLVED.md',
        'EXACT_MATCH_COMPLETE.md',
        'NORMALIZATION_VERIFICATION_COMPLETE.md',
        'S3_INPUT_BUCKET_CLEANUP_COMPLETE.md',
    ],
    'docs/design': [
        'PDF_SPLIT_VERIFICATION_DESIGN.md',
        'PNG_PRERENDER_IMPLEMENTATION.md',
        'AWS_VERIFICATION_PLAN.md',
        'BATCH_VERIFICATION_WORKFLOW.md',
        'CORRECT_ALGORITHM.md',
    ],
    'docs/s3': [
        'S3_*.md',
    ],
    'docs/plans': [
        'DEPLOYMENT_PLAN.md',
        'REMAINING_*_PLAN.md',
        '*_PLAN.md',
    ],

    # Scripts - AWS operations
    'scripts/aws': [
        'deploy*.ps1',
        'cleanup.ps1',
        'register-*.ps1',
    ],
    'scripts/aws/monitoring': [
        'monitor-*.ps1',
    ],
    'scripts/aws/processing': [
        'process-*.ps1',
        'reprocess-*.ps1',
        'retry-*.ps1',
    ],
    'scripts/aws/downloading': [
        'download-*.ps1',
    ],

    # Scripts - S3 management
    'scripts/s3': [
        'build_s3_*.py',
        'consolidate_*.py',
        'execute_consolidation.py',
        'fix_bread_structure.py',
        'render_s3_*.py',
        's3_*.py',
        'compare-s3-*.ps1',
        'reorganize-s3-*.ps1',
        'rename-in-s3-*.ps1',
    ],

    # Scripts - Analysis
    'scripts/analysis': [
        'build-*-inventory*.ps1',
        'check-*.ps1',
        'find-*.ps1',
        'identify-*.ps1',
        'generate-*.ps1',
        'gather-*.ps1',
        'estimate-*.ps1',
        'problem-books-report.ps1',
        'reverse-inventory*.ps1',
        'strict-1to1-inventory.ps1',
        'analyze_*.py',
        'compare_*.py',
        'find_*.py',
        'identify_*.py',
        'reconcile_*.py',
        'validate_*.py',
        'verify_*.py',
    ],

    # Scripts - Local operations
    'scripts/local': [
        'reorganize-local-*.ps1',
        'fix-artist-names-*.ps1',
        'restore-*.ps1',
    ],

    # Scripts - Testing
    'scripts/testing': [
        'test_*.py',
        'check_ollama_performance.ps1',
        'start_review_server.ps1',
    ],

    # Scripts - Utilities
    'scripts/utilities': [
        'git-checkpoint-commit.ps1',
        'kill-old-batch-scripts.ps1',
        'start_s3_browser.ps1',
        'get-missing-files-csv.ps1',
    ],

    # Scripts - One-off/experimental (catch-all for remaining scripts)
    'scripts/one-off': [],  # Will catch remaining .py and .ps1 files

    # Logs
    'logs/processing': [
        'process-*.log',
        'download-*.log',
        'master-process-*.log',
    ],
    'logs/reorganization': [
        'reorganize-*.log',
        'rename-*.log',
        'fresh-comparison-*.log',
    ],
    'logs/testing': [
        'test_*.log',
        '*-test.log',
        'prerender.log',
        'pdf_verification.log',
    ],

    # Data - Inventories
    'data/inventories': [
        '*-inventory*.csv',
        'book-inventory*.csv',
        'accurate-book-inventory.csv',
        's3_complete_inventory.csv',
    ],

    # Data - Reconciliation
    'data/reconciliation': [
        'book_reconciliation*.csv',
        '*reconciliation*.csv',
        'input_output_comparison*.csv',
        'path_mapping.csv',
    ],

    # Data - Processing tracking
    'data/processing': [
        'current-book-status.csv',
        'book-processing-report.csv',
        'dynamodb_*.csv',
        '*-executions*.csv',
        'failed-*.csv',
        'remaining-*.csv',
        'ready_for_aws_processing*.csv',
        'reprocess-*.csv',
    ],

    # Data - Analysis results
    'data/analysis': [
        'best_matches_analysis.csv',
        'case_mismatches.csv',
        'duplicate*.csv',
        'matches_*.csv',
        'missing-*.csv',
        'not-duplicates-*.csv',
        'normalization_plan*.csv',
        's3_consolidate_plan.csv',
    ],

    # Data - Downloads
    'data/downloads': [
        'books-ready-to-download.csv',
        'files-to-download.csv',
        'books-with-*.csv',
        'found-*.csv',
        'processed-books-with-pdfs.csv',
    ],

    # Web - S3 browser
    'web/s3-browser': [
        's3_bucket_browser*.html',
        's3_tree_view.html',
        'test_bulk_buttons.html',
        'test_buttons.html',
    ],

    # Web - Verification
    'web/verification': [
        'verification_*.html',
        '*_review*.html',
    ],

    # Web - Viewers
    'web/viewers': [
        '*_lineage_viewer.html',
        '*_viewer.html',
    ],

    # Build artifacts
    'build': [
        'lambda-package',  # Directory
    ],
}

# Track moves
moves_log = []
errors_log = []

def matches_pattern(filename, pattern):
    """Check if filename matches a glob-style pattern."""
    import fnmatch
    return fnmatch.fnmatch(filename, pattern)

def should_keep_in_root(name):
    """Check if file/dir should stay in root."""
    return name in KEEP_IN_ROOT or name in PROTECTED_DIRS

def create_directories():
    """Create all target directories."""
    print("Creating directory structure...")
    for target_dir in REORGANIZATION.keys():
        dir_path = BASE_DIR / target_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {target_dir}")

def move_item(source, target_dir):
    """Move a file or directory to target directory."""
    target_path = BASE_DIR / target_dir / source.name

    # Skip if already in target
    if source.parent == (BASE_DIR / target_dir):
        return None

    try:
        # Check if target already exists
        if target_path.exists():
            print(f"  SKIP (exists): {source.name} -> {target_dir}")
            return None

        # Move the item
        shutil.move(str(source), str(target_path))
        moves_log.append((source.name, target_dir))
        return target_path
    except Exception as e:
        errors_log.append((source.name, target_dir, str(e)))
        print(f"  ERROR: {source.name} -> {target_dir}: {e}")
        return None

def reorganize_files():
    """Perform the reorganization."""
    print("\nReorganizing files...")

    moved_items = set()

    # Process each category
    for target_dir, patterns in REORGANIZATION.items():
        print(f"\n{target_dir}:")

        # Special handling for directories (like lambda-package)
        if 'lambda-package' in patterns:
            lambda_pkg = BASE_DIR / 'lambda-package'
            if lambda_pkg.exists() and lambda_pkg.is_dir():
                target_path = BASE_DIR / target_dir / 'lambda-package'
                if not target_path.exists():
                    shutil.move(str(lambda_pkg), str(target_path))
                    moves_log.append(('lambda-package/', target_dir))
                    print(f"  Moved: lambda-package/ -> {target_dir}")
                    moved_items.add('lambda-package')
            continue

        # Process patterns
        for pattern in patterns:
            # Find matching items in root
            for item in BASE_DIR.iterdir():
                if item.is_file() and not should_keep_in_root(item.name):
                    if matches_pattern(item.name, pattern) and item.name not in moved_items:
                        result = move_item(item, target_dir)
                        if result:
                            print(f"  Moved: {item.name}")
                            moved_items.add(item.name)

    # Move remaining scripts to one-off
    print("\nscripts/one-off (remaining scripts):")
    for item in BASE_DIR.iterdir():
        if item.is_file() and not should_keep_in_root(item.name):
            if (item.suffix in ['.py', '.ps1'] and
                item.name not in moved_items and
                item.name != 'reorganize_project.py'):
                result = move_item(item, 'scripts/one-off')
                if result:
                    print(f"  Moved: {item.name}")
                    moved_items.add(item.name)

    # Move remaining HTML files
    print("\nweb/s3-browser (remaining HTML):")
    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == '.html' and item.name not in moved_items:
            result = move_item(item, 'web/s3-browser')
            if result:
                print(f"  Moved: {item.name}")
                moved_items.add(item.name)

    # Move remaining CSV files
    print("\ndata/analysis (remaining CSV):")
    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == '.csv' and item.name not in moved_items:
            result = move_item(item, 'data/analysis')
            if result:
                print(f"  Moved: {item.name}")
                moved_items.add(item.name)

    # Move remaining log files
    print("\nlogs/processing (remaining logs):")
    for item in BASE_DIR.iterdir():
        if item.is_file() and item.suffix == '.log' and item.name not in moved_items:
            result = move_item(item, 'logs/processing')
            if result:
                print(f"  Moved: {item.name}")
                moved_items.add(item.name)

    # Move verification_results directory
    verification_dir = BASE_DIR / 'verification_results'
    if verification_dir.exists() and verification_dir.is_dir():
        target_path = BASE_DIR / 'web' / 'verification' / 'verification_results'
        if not target_path.exists():
            shutil.move(str(verification_dir), str(target_path))
            print(f"\nMoved directory: verification_results/ -> web/verification/")
            moves_log.append(('verification_results/', 'web/verification'))

def generate_report():
    """Generate reorganization report."""
    report_path = BASE_DIR / 'REORGANIZATION_REPORT.md'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(f"# Project Reorganization Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Summary\n\n")
        f.write(f"- **Files/Directories Moved**: {len(moves_log)}\n")
        f.write(f"- **Errors**: {len(errors_log)}\n\n")

        if moves_log:
            f.write(f"## Moved Items ({len(moves_log)})\n\n")

            # Group by target directory
            by_target = {}
            for item, target in moves_log:
                if target not in by_target:
                    by_target[target] = []
                by_target[target].append(item)

            for target in sorted(by_target.keys()):
                f.write(f"### {target}/ ({len(by_target[target])} items)\n\n")
                for item in sorted(by_target[target]):
                    f.write(f"- {item}\n")
                f.write("\n")

        if errors_log:
            f.write(f"## Errors ({len(errors_log)})\n\n")
            for item, target, error in errors_log:
                f.write(f"- **{item}** -> {target}: {error}\n")

    print(f"\n✅ Report generated: REORGANIZATION_REPORT.md")
    return report_path

def main():
    """Main reorganization process."""
    print("=" * 70)
    print("PROJECT REORGANIZATION")
    print("=" * 70)
    print(f"\nBase directory: {BASE_DIR}")
    print(f"\nProtected directories: {', '.join(sorted(PROTECTED_DIRS))}")
    print(f"Files kept in root: {', '.join(sorted(KEEP_IN_ROOT))}")

    # Step 1: Create directories
    create_directories()

    # Step 2: Reorganize files
    reorganize_files()

    # Step 3: Generate report
    report_path = generate_report()

    # Summary
    print("\n" + "=" * 70)
    print("REORGANIZATION COMPLETE")
    print("=" * 70)
    print(f"\n✅ Moved: {len(moves_log)} items")
    if errors_log:
        print(f"⚠️  Errors: {len(errors_log)} items")
    print(f"\n📄 Full report: {report_path.name}")
    print("\nNew structure:")
    print("  docs/          - All documentation")
    print("  scripts/       - All scripts (organized by purpose)")
    print("  logs/          - All log files")
    print("  data/          - All CSV and data files")
    print("  web/           - All HTML interfaces")
    print("  build/         - Build artifacts (lambda-package)")

if __name__ == "__main__":
    main()
