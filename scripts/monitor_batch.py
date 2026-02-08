#!/usr/bin/env python3
"""
Monitor batch processing progress.
Checks status of all executions and provides summary.
"""
import json
import boto3
from pathlib import Path
from datetime import datetime
from collections import Counter
import time
import sys

stepfunctions = boto3.client('stepfunctions')

def load_latest_batch():
    """Load the most recent batch file."""
    data_dir = Path('data')
    batch_files = list(data_dir.glob('batch_executions_*.json'))

    if not batch_files:
        print("No batch files found!")
        return None

    # Sort by timestamp (in filename)
    latest = max(batch_files, key=lambda p: p.stem.split('_')[-1])
    print(f"Loading batch: {latest}")

    with open(latest) as f:
        return json.load(f)

def get_execution_status(execution_arn):
    """Get current status of an execution."""
    try:
        response = stepfunctions.describe_execution(executionArn=execution_arn)
        return {
            'status': response['status'],  # RUNNING, SUCCEEDED, FAILED, TIMED_OUT, ABORTED
            'start_date': response['startDate'].isoformat() if 'startDate' in response else None,
            'stop_date': response.get('stopDate', '').isoformat() if response.get('stopDate') else None
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'error': str(e)
        }

def monitor_batch(watch=False, interval=30):
    """Monitor batch processing status."""
    batch = load_latest_batch()
    if not batch:
        return

    executions = batch['executions']
    print(f"\nBatch submitted: {batch['submitted_at']}")
    print(f"Total executions: {len(executions)}")
    print("=" * 80)

    while True:
        print(f"\nChecking status at {datetime.now().strftime('%H:%M:%S')}...")

        statuses = []
        status_counts = Counter()

        for i, exec_info in enumerate(executions, 1):
            arn = exec_info['execution_arn']
            book_id = exec_info['book_id']

            status = get_execution_status(arn)
            statuses.append({
                'book_id': book_id,
                'artist': exec_info['artist'],
                'book_name': exec_info['book_name'],
                **status
            })
            status_counts[status['status']] += 1

            # Print progress for first check
            if not watch:
                status_symbol = {
                    'RUNNING': '⏳',
                    'SUCCEEDED': '✓',
                    'FAILED': '✗',
                    'TIMED_OUT': '⏱',
                    'ABORTED': '⊗',
                    'ERROR': '❌'
                }.get(status['status'], '?')

                print(f"  [{i:3d}] {status_symbol} {status['status']:12s} {exec_info['artist']} - {exec_info['book_name']}")

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY:")
        print(f"  SUCCEEDED:  {status_counts.get('SUCCEEDED', 0):3d}")
        print(f"  RUNNING:    {status_counts.get('RUNNING', 0):3d}")
        print(f"  FAILED:     {status_counts.get('FAILED', 0):3d}")
        print(f"  TIMED_OUT:  {status_counts.get('TIMED_OUT', 0):3d}")
        print(f"  ABORTED:    {status_counts.get('ABORTED', 0):3d}")
        print(f"  ERROR:      {status_counts.get('ERROR', 0):3d}")

        completed = status_counts.get('SUCCEEDED', 0) + status_counts.get('FAILED', 0) + \
                   status_counts.get('TIMED_OUT', 0) + status_counts.get('ABORTED', 0)
        total = len(executions)
        progress = (completed / total * 100) if total > 0 else 0

        print(f"\nProgress: {completed}/{total} ({progress:.1f}% complete)")
        print("=" * 80)

        # Check if all done
        if status_counts.get('RUNNING', 0) == 0 and completed == total:
            print("\n✓ All executions completed!")
            break

        if not watch:
            break

        # Wait before next check
        print(f"\nWaiting {interval}s before next check... (Ctrl+C to stop)")
        try:
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped by user")
            break

if __name__ == '__main__':
    # Check for watch mode
    watch = '--watch' in sys.argv or '-w' in sys.argv

    # Get interval
    interval = 30
    for arg in sys.argv[1:]:
        if arg.startswith('--interval='):
            interval = int(arg.split('=')[1])

    monitor_batch(watch=watch, interval=interval)
