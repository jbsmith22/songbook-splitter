#!/usr/bin/env python3
"""
Wait for current batch to finish, then process remaining books.
"""
import json
import boto3
import time
from pathlib import Path
from datetime import datetime

stepfunctions = boto3.client('stepfunctions')

def load_latest_batch():
    """Load the most recent batch file."""
    data_dir = Path('data')
    batch_files = list(data_dir.glob('batch_executions_*.json'))

    if not batch_files:
        return None

    latest = max(batch_files, key=lambda p: p.stem.split('_')[-1])
    with open(latest) as f:
        return json.load(f)

def check_batch_complete():
    """Check if the current batch is complete."""
    batch = load_latest_batch()
    if not batch:
        return True

    executions = batch['executions']
    running_count = 0

    for exec_info in executions:
        try:
            response = stepfunctions.describe_execution(
                executionArn=exec_info['execution_arn']
            )
            status = response['status']
            if status == 'RUNNING':
                running_count += 1
        except:
            pass

    return running_count == 0

def main():
    print("=" * 80)
    print("WAITING FOR CURRENT BATCH TO COMPLETE")
    print("=" * 80)

    # Wait for current batch to finish
    print("\nChecking current batch status...")

    while not check_batch_complete():
        batch = load_latest_batch()
        executions = batch['executions']

        running = 0
        succeeded = 0
        failed = 0

        for exec_info in executions:
            try:
                response = stepfunctions.describe_execution(
                    executionArn=exec_info['execution_arn']
                )
                status = response['status']
                if status == 'RUNNING':
                    running += 1
                elif status == 'SUCCEEDED':
                    succeeded += 1
                elif status in ['FAILED', 'TIMED_OUT', 'ABORTED']:
                    failed += 1
            except:
                pass

        completed = succeeded + failed
        total = len(executions)

        print(f"\rProgress: {completed}/{total} complete ({succeeded} succeeded, {failed} failed, {running} running)...", end='', flush=True)

        time.sleep(30)

    print("\n\nCurrent batch complete!")
    print("=" * 80)

    # Start next batch
    print("\nStarting next batch of 300 books...")
    import subprocess
    subprocess.run([
        "C:\\Program Files\\Python312\\python.exe",
        "scripts/batch_process_books.py",
        "300"
    ])

if __name__ == '__main__':
    main()
