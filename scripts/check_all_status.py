#!/usr/bin/env python3
"""Check status of all executions."""
import json
import boto3
from collections import Counter
from datetime import datetime

sf = boto3.client('stepfunctions')

# Load batch 2
with open('data/batch_executions_1770449379.json') as f:
    b2 = json.load(f)

print("Checking all 300 books from Batch 2...")
print("(This will take a minute...)\n")

statuses = []
c = Counter()

for i, exec_info in enumerate(b2['executions'], 1):
    if i % 50 == 0:
        print(f"  Checked {i}/300...")
    try:
        status = sf.describe_execution(executionArn=exec_info['execution_arn'])
        statuses.append(status)
        c[status['status']] += 1
    except Exception as e:
        print(f"  Error checking {exec_info['book_id']}: {e}")

print("\nBatch 2 Status (all 300):")
print(f"  RUNNING: {c.get('RUNNING', 0)}")
print(f"  SUCCEEDED: {c.get('SUCCEEDED', 0)}")
print(f"  FAILED: {c.get('FAILED', 0)}")
print(f"  TIMED_OUT: {c.get('TIMED_OUT', 0)}")
print(f"  ABORTED: {c.get('ABORTED', 0)}")
print(f"\nTotal: {sum(c.values())}/300")

if statuses:
    print("\n--- Sample Timing Info ---")
    first = statuses[0]
    print(f"First execution:")
    print(f"  Start: {first['startDate']}")
    if 'stopDate' in first:
        print(f"  Stop: {first['stopDate']}")
        duration = (first['stopDate'] - first['startDate']).total_seconds() / 60
        print(f"  Duration: {duration:.1f} minutes")

    last_completed = [s for s in statuses if 'stopDate' in s]
    if last_completed:
        last = max(last_completed, key=lambda x: x['stopDate'])
        print(f"\nLast completed execution:")
        print(f"  Stop: {last['stopDate']}")
        duration = (last['stopDate'] - last['startDate']).total_seconds() / 60
        print(f"  Duration: {duration:.1f} minutes")
