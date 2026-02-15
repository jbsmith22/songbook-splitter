#!/usr/bin/env python3
"""
Restore DynamoDB table from backup file.

Usage:
    python scripts/restore_dynamodb.py --backup-file data/dynamodb_backup_jsmith-pipeline-ledger_2026-02-14.json --table jsmith-pipeline-ledger [--dry-run]
"""

import argparse
import json
import sys
from decimal import Decimal
from typing import Any, Dict

import boto3
from botocore.exceptions import ClientError


def convert_dynamodb_json(obj: Any) -> Any:
    """
    Convert DynamoDB JSON format to Python native types.

    DynamoDB format uses type descriptors:
    - {"S": "value"} -> "value"
    - {"N": "123"} -> Decimal("123")
    - {"M": {...}} -> {...}
    - {"L": [...]} -> [...]
    - {"BOOL": true} -> True
    - {"NULL": true} -> None
    """
    if isinstance(obj, dict):
        # Check for DynamoDB type descriptors
        if len(obj) == 1:
            type_key = list(obj.keys())[0]
            value = obj[type_key]

            if type_key == 'S':  # String
                return value
            elif type_key == 'N':  # Number (as Decimal)
                return Decimal(value)
            elif type_key == 'M':  # Map
                return {k: convert_dynamodb_json(v) for k, v in value.items()}
            elif type_key == 'L':  # List
                return [convert_dynamodb_json(item) for item in value]
            elif type_key == 'BOOL':  # Boolean
                return value
            elif type_key == 'NULL':  # Null
                return None
            elif type_key == 'SS':  # String Set
                return set(value)
            elif type_key == 'NS':  # Number Set
                return {Decimal(n) for n in value}

        # Regular dict - convert all values
        return {k: convert_dynamodb_json(v) for k, v in obj.items()}

    elif isinstance(obj, list):
        return [convert_dynamodb_json(item) for item in obj]

    return obj


def restore_items(backup_file: str, table_name: str, dry_run: bool = False) -> None:
    """Restore items from backup file to DynamoDB table."""

    # Load backup
    print(f"Loading backup from: {backup_file}")
    with open(backup_file, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)

    items = backup_data.get('Items', [])
    total_items = len(items)
    print(f"Found {total_items} items in backup")

    if dry_run:
        print("\n[DRY RUN] Would restore the following items:")
        for i, item in enumerate(items[:5]):
            converted = convert_dynamodb_json(item)
            book_id = converted.get('book_id', 'unknown')
            artist = converted.get('artist', 'unknown')
            book_name = converted.get('book_name', 'unknown')
            status = converted.get('status', 'unknown')
            print(f"  {i+1}. {artist} / {book_name} ({book_id}) - {status}")
        if total_items > 5:
            print(f"  ... and {total_items - 5} more items")
        print(f"\n[DRY RUN] Would write {total_items} items to table: {table_name}")
        return

    # Initialize DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)

    # Verify table exists
    try:
        table.load()
        print(f"Target table: {table_name}")
        print(f"  Status: {table.table_status}")
        print(f"  Item count: {table.item_count}")
    except ClientError as e:
        print(f"Error: Table '{table_name}' does not exist or is not accessible")
        print(f"  {e}")
        sys.exit(1)

    # Restore items in batches of 25 (DynamoDB batch_write limit)
    print(f"\nRestoring {total_items} items...")
    success_count = 0
    error_count = 0

    for i in range(0, total_items, 25):
        batch = items[i:i+25]
        batch_num = i // 25 + 1
        total_batches = (total_items + 24) // 25

        try:
            with table.batch_writer() as writer:
                for item in batch:
                    # Convert DynamoDB JSON to Python types
                    converted_item = convert_dynamodb_json(item)
                    writer.put_item(Item=converted_item)
                    success_count += 1

            print(f"  Batch {batch_num}/{total_batches}: Restored {min(i+25, total_items)}/{total_items} items")

        except ClientError as e:
            print(f"  Batch {batch_num}/{total_batches}: ERROR - {e}")
            error_count += len(batch)

    # Summary
    print(f"\n{'='*60}")
    print(f"RESTORATION COMPLETE")
    print(f"{'='*60}")
    print(f"  Total items: {total_items}")
    print(f"  Successful: {success_count}")
    print(f"  Errors: {error_count}")

    if error_count > 0:
        print(f"\nWARNING: {error_count} items failed to restore")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Restore DynamoDB table from backup file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run to preview restoration
  python scripts/restore_dynamodb.py --backup-file data/backup.json --table my-table --dry-run

  # Restore to original table
  python scripts/restore_dynamodb.py --backup-file data/backup.json --table jsmith-pipeline-ledger

  # Restore to different table
  python scripts/restore_dynamodb.py --backup-file data/backup.json --table jsmith-pipeline-ledger-restored
        """
    )

    parser.add_argument(
        '--backup-file',
        required=True,
        help='Path to DynamoDB backup JSON file'
    )

    parser.add_argument(
        '--table',
        required=True,
        help='Target DynamoDB table name'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview restoration without writing to DynamoDB'
    )

    args = parser.parse_args()

    restore_items(args.backup_file, args.table, args.dry_run)


if __name__ == '__main__':
    main()
