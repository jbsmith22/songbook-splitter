"""
Backup helper utility for creating timestamped backups before file modifications
"""
import shutil
from datetime import datetime
from pathlib import Path


def create_backup(file_path, backup_suffix='backup'):
    """
    Create a timestamped backup of a file

    Args:
        file_path: Path to the file to backup (string or Path object)
        backup_suffix: Optional suffix to add before timestamp (default: 'backup')

    Returns:
        Path to the backup file

    Example:
        backup_path = create_backup('data/important.json')
        # Creates: data/important.json.backup_20260131_235959
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Cannot backup non-existent file: {file_path}")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = file_path.parent / f"{file_path.name}.{backup_suffix}_{timestamp}"

    shutil.copy2(file_path, backup_path)
    print(f"OK Backup created: {backup_path}")

    return backup_path


def cleanup_old_backups(file_path, keep_count=10, backup_pattern='*.backup_*'):
    """
    Remove old backup files, keeping only the most recent N backups

    Args:
        file_path: Original file path (backups will be searched in same directory)
        keep_count: Number of most recent backups to keep (default: 10)
        backup_pattern: Glob pattern to match backup files (default: '*.backup_*')
    """
    file_path = Path(file_path)
    backup_dir = file_path.parent

    # Find all backup files matching the pattern
    backup_files = list(backup_dir.glob(f"{file_path.name}.{backup_pattern}"))

    # Sort by modification time (newest first)
    backup_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    # Delete old backups beyond keep_count
    deleted_count = 0
    for old_backup in backup_files[keep_count:]:
        old_backup.unlink()
        deleted_count += 1

    if deleted_count > 0:
        print(f"OK Cleaned up {deleted_count} old backup(s), kept {min(len(backup_files), keep_count)} most recent")


if __name__ == '__main__':
    # Example usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: python backup_helper.py <file_path> [keep_count]")
        sys.exit(1)

    file_path = sys.argv[1]
    keep_count = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    try:
        backup_path = create_backup(file_path)
        cleanup_old_backups(file_path, keep_count)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
