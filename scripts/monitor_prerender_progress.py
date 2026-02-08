#!/usr/bin/env python3
"""
Monitor the progress of source songbook pre-rendering.
"""
import re
import time
import json
from pathlib import Path
from datetime import datetime, timedelta

# Paths
OUTPUT_FILE = Path("C:/Users/jbsmi/AppData/Local/Temp/claude/d--Work-songbook-splitter/tasks/bc338d6.output")
RESULTS_FILE = Path("prerender_results.json")

def parse_progress_line(line):
    """Parse a progress line from tqdm output."""
    # Example: "Rendering source PDFs:  1%|▏         | 5/562 [02:30<4:20:15, 28.05s/it, success=5, fail=0, pages=456]"

    match = re.search(r'(\d+)/(\d+) \[(.+?)<(.+?), (.+?)s/it, success=(\d+), fail=(\d+), pages=(\d+)\]', line)
    if match:
        completed = int(match.group(1))
        total = int(match.group(2))
        elapsed = match.group(3)
        remaining = match.group(4)
        speed = float(match.group(5))
        success = int(match.group(6))
        fail = int(match.group(7))
        pages = int(match.group(8))

        return {
            'completed': completed,
            'total': total,
            'elapsed': elapsed,
            'remaining': remaining,
            'speed': speed,
            'success': success,
            'fail': fail,
            'pages': pages,
            'percent': (completed / total * 100) if total > 0 else 0
        }
    return None

def get_latest_progress():
    """Get the latest progress from the output file."""
    if not OUTPUT_FILE.exists():
        return None

    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Find the last progress line
        for line in reversed(lines):
            if 'Rendering source PDFs:' in line:
                progress = parse_progress_line(line)
                if progress:
                    return progress

        return None
    except Exception as e:
        print(f"Error reading progress: {e}")
        return None

def format_time(time_str):
    """Format time string for display."""
    # time_str like "4:20:15" or "02:30"
    parts = time_str.split(':')
    if len(parts) == 3:
        h, m, s = parts
        return f"{int(h)}h {int(m)}m {int(s)}s"
    elif len(parts) == 2:
        m, s = parts
        return f"{int(m)}m {int(s)}s"
    return time_str

def display_progress(progress, show_header=True):
    """Display progress in a formatted way."""
    if show_header:
        print("\n" + "=" * 80)
        print("SOURCE SONGBOOK EXTRACTION PROGRESS")
        print("=" * 80)

    print(f"\n  Status: RUNNING")
    print(f"  Progress: {progress['completed']}/{progress['total']} books ({progress['percent']:.1f}%)")
    print(f"  Success: {progress['success']} | Failures: {progress['fail']}")
    print(f"  Pages extracted: {progress['pages']:,}")
    print(f"  Speed: {progress['speed']:.2f} seconds/book")
    print(f"  Time elapsed: {format_time(progress['elapsed'])}")
    print(f"  Time remaining: {format_time(progress['remaining'])}")
    print(f"  Avg pages/book: {progress['pages'] / progress['completed']:.1f}" if progress['completed'] > 0 else "")

    # Progress bar (ASCII-safe for Windows)
    bar_width = 50
    filled = int(bar_width * progress['percent'] / 100)
    bar = '#' * filled + '-' * (bar_width - filled)
    print(f"\n  [{bar}] {progress['percent']:.1f}%")

def check_if_complete():
    """Check if extraction is complete."""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, 'r') as f:
                results = json.load(f)

            # Check if this is the final results file
            if results.get('total_books', 0) >= 500:  # Large run
                return True, results
        except:
            pass

    return False, None

def monitor_once():
    """Run one monitoring check."""
    # Check if complete
    is_complete, results = check_if_complete()

    if is_complete:
        print("\n" + "=" * 80)
        print("EXTRACTION COMPLETE!")
        print("=" * 80)
        print(f"\n  Total books: {results['total_books']}")
        print(f"  Successes: {results['successes']}")
        print(f"  Failures: {results['failures']}")
        print(f"  Total pages: {results['total_pages_rendered']:,}")
        print(f"  Total time: {results['total_time_seconds']:.1f}s ({results['total_time_seconds']/60:.1f} minutes)")
        if results['total_pages_rendered'] > 0:
            print(f"  Avg time/page: {results['total_time_seconds']/results['total_pages_rendered']:.3f}s")
        print(f"\n  Results saved to: {RESULTS_FILE}")
        print(f"  Cache location: S:/SlowImageCache/pdf_verification_v2/")
        return True

    # Get current progress
    progress = get_latest_progress()

    if progress:
        display_progress(progress)
    else:
        print("\n  Waiting for progress data...")

    return False

def monitor_continuous(interval=30):
    """Monitor progress continuously."""
    print("Starting continuous monitoring (Ctrl+C to stop)...")
    print(f"Update interval: {interval} seconds")

    try:
        first = True
        while True:
            complete = monitor_once()
            if complete:
                break

            if not first:
                print(f"\n  Next update in {interval} seconds...")
            first = False

            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        # Continuous monitoring
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        monitor_continuous(interval)
    else:
        # One-time check
        monitor_once()
