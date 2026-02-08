#!/usr/bin/env python3
"""Quick status check for current batch."""
import json
import boto3
from pathlib import Path
from collections import Counter

stepfunctions = boto3.client('stepfunctions')

def load_latest_batch():
    """Load the most recent batch file."""
    data_dir = Path('data')
    batch_files = list(data_dir.glob('batch_executions_*.json'))

    if not batch_files:
        print("No batch files found!")
        return None

    latest = max(batch_files, key=lambda p: p.stem.split('_')[-1])
    print(f"Checking batch: {latest.name}\n")

    with open(latest) as f:
        return json.load(f)

batch = load_latest_batch()
if not batch:
    exit(1)

executions = batch['executions']
status_counts = Counter()

for exec_info in executions:
    try:
        response = stepfunctions.describe_execution(
            executionArn=exec_info['execution_arn']
        )
        status_counts[response['status']] += 1
    except:
        status_counts['ERROR'] += 1

print("CURRENT STATUS:")
print("=" * 60)
print(f"  RUNNING:    {status_counts.get('RUNNING', 0):3d}")
print(f"  SUCCEEDED:  {status_counts.get('SUCCEEDED', 0):3d}")
print(f"  FAILED:     {status_counts.get('FAILED', 0):3d}")
print(f"  TIMED_OUT:  {status_counts.get('TIMED_OUT', 0):3d}")
print(f"  ABORTED:    {status_counts.get('ABORTED', 0):3d}")
print("=" * 60)

completed = (status_counts.get('SUCCEEDED', 0) +
             status_counts.get('FAILED', 0) +
             status_counts.get('TIMED_OUT', 0) +
             status_counts.get('ABORTED', 0))
total = len(executions)
progress = (completed / total * 100) if total > 0 else 0

print(f"\nProgress: {completed}/{total} ({progress:.1f}% complete)")

if status_counts.get('RUNNING', 0) > 0:
    # Estimate time remaining (assuming 3 min per book)
    est_mins = status_counts.get('RUNNING', 0) * 3
    print(f"Estimated time remaining: ~{est_mins} minutes")
    print("\nRun with --watch to monitor continuously:")
    print("  python scripts/monitor_batch.py --watch")
else:
    print("\nAll executions complete!")
    print("\nTo process the next batch:")
    print("  python scripts/batch_process_books.py 300")
