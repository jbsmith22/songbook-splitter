"""
Clean up v2 pipeline run - stop executions and delete artifacts.

Usage:
    py scripts/reprocessing/cleanup_v2_run.py --dry-run    # See what would be deleted
    py scripts/reprocessing/cleanup_v2_run.py --stop       # Stop running executions
    py scripts/reprocessing/cleanup_v2_run.py --delete     # Delete all v2 artifacts
    py scripts/reprocessing/cleanup_v2_run.py --all        # Do both
"""
import json
import boto3
import argparse
from datetime import datetime

# Configuration
OUTPUT_BUCKET = 'jsmith-output'
STATE_MACHINE_ARN = 'arn:aws:states:us-east-1:227027150061:stateMachine:jsmith-sheetmusic-splitter-pipeline'

s3 = boto3.client('s3')
sfn = boto3.client('stepfunctions')


def get_running_v2_executions():
    """Get list of running v2 executions."""
    running = []
    paginator = sfn.get_paginator('list_executions')

    for page in paginator.paginate(
        stateMachineArn=STATE_MACHINE_ARN,
        statusFilter='RUNNING'
    ):
        for ex in page.get('executions', []):
            if ex['name'].startswith('v2-'):
                running.append(ex)

    return running


def stop_executions(executions, dry_run=False):
    """Stop running executions."""
    print(f"\nStopping {len(executions)} running v2 executions...")

    stopped = 0
    errors = []

    for ex in executions:
        if dry_run:
            print(f"  Would stop: {ex['name']}")
            stopped += 1
        else:
            try:
                sfn.stop_execution(
                    executionArn=ex['executionArn'],
                    cause='Cleanup - resetting v2 pipeline run'
                )
                print(f"  Stopped: {ex['name']}")
                stopped += 1
            except Exception as e:
                errors.append(f"{ex['name']}: {e}")

    print(f"\n  Stopped: {stopped}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"    {err}")

    return stopped


def get_v2_artifact_folders():
    """Get list of v2 artifact folder prefixes."""
    folders = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix='artifacts/v2-', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])

    return folders


def delete_v2_artifacts(folders, dry_run=False):
    """Delete all v2 artifact folders."""
    print(f"\nDeleting {len(folders)} v2 artifact folders...")

    deleted_folders = 0
    deleted_objects = 0
    errors = []

    for folder in folders:
        if dry_run:
            # Count objects that would be deleted
            response = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=folder)
            count = len(response.get('Contents', []))
            print(f"  Would delete: {folder} ({count} objects)")
            deleted_folders += 1
            deleted_objects += count
        else:
            try:
                # List and delete all objects in folder
                paginator = s3.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=folder):
                    if 'Contents' not in page:
                        continue
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    if objects_to_delete:
                        s3.delete_objects(Bucket=OUTPUT_BUCKET, Delete={'Objects': objects_to_delete})
                        deleted_objects += len(objects_to_delete)

                deleted_folders += 1
                if deleted_folders % 20 == 0:
                    print(f"  Deleted {deleted_folders}/{len(folders)} folders...")

            except Exception as e:
                errors.append(f"{folder}: {e}")

    print(f"\n  Deleted folders: {deleted_folders}")
    print(f"  Deleted objects: {deleted_objects}")
    if errors:
        print(f"  Errors: {len(errors)}")
        for err in errors[:5]:
            print(f"    {err}")

    return deleted_folders, deleted_objects


def get_v2_split_folders():
    """Get list of v2 split output folders (songs/v2-*)."""
    folders = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix='songs/v2-', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            folders.append(prefix['Prefix'])

    return folders


def delete_v2_splits(folders, dry_run=False):
    """Delete all v2 split output folders."""
    print(f"\nDeleting {len(folders)} v2 split folders...")

    deleted_folders = 0
    deleted_objects = 0
    errors = []

    for folder in folders:
        if dry_run:
            response = s3.list_objects_v2(Bucket=OUTPUT_BUCKET, Prefix=folder)
            count = len(response.get('Contents', []))
            print(f"  Would delete: {folder} ({count} objects)")
            deleted_folders += 1
            deleted_objects += count
        else:
            try:
                paginator = s3.get_paginator('list_objects_v2')
                for page in paginator.paginate(Bucket=OUTPUT_BUCKET, Prefix=folder):
                    if 'Contents' not in page:
                        continue
                    objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                    if objects_to_delete:
                        s3.delete_objects(Bucket=OUTPUT_BUCKET, Delete={'Objects': objects_to_delete})
                        deleted_objects += len(objects_to_delete)

                deleted_folders += 1
                if deleted_folders % 20 == 0:
                    print(f"  Deleted {deleted_folders}/{len(folders)} folders...")

            except Exception as e:
                errors.append(f"{folder}: {e}")

    print(f"\n  Deleted folders: {deleted_folders}")
    print(f"  Deleted objects: {deleted_objects}")
    if errors:
        print(f"  Errors: {len(errors)}")

    return deleted_folders, deleted_objects


def main():
    parser = argparse.ArgumentParser(description='Clean up v2 pipeline run')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    parser.add_argument('--stop', action='store_true', help='Stop running executions')
    parser.add_argument('--delete', action='store_true', help='Delete v2 artifacts')
    parser.add_argument('--all', action='store_true', help='Do both stop and delete')

    args = parser.parse_args()

    if not (args.stop or args.delete or args.all or args.dry_run):
        print("*** Must specify --stop, --delete, --all, or --dry-run ***")
        return

    print("=" * 60)
    print("V2 PIPELINE CLEANUP")
    print("=" * 60)
    print(f"Dry run: {args.dry_run}")

    # Get current state
    running = get_running_v2_executions()
    artifact_folders = get_v2_artifact_folders()
    split_folders = get_v2_split_folders()

    print(f"\nCurrent state:")
    print(f"  Running v2 executions: {len(running)}")
    print(f"  V2 artifact folders: {len(artifact_folders)}")
    print(f"  V2 split folders: {len(split_folders)}")

    # Stop executions
    if args.stop or args.all:
        if running:
            stop_executions(running, dry_run=args.dry_run)
        else:
            print("\nNo running v2 executions to stop")

    # Delete artifacts
    if args.delete or args.all:
        if artifact_folders:
            delete_v2_artifacts(artifact_folders, dry_run=args.dry_run)
        else:
            print("\nNo v2 artifact folders to delete")

        if split_folders:
            delete_v2_splits(split_folders, dry_run=args.dry_run)
        else:
            print("\nNo v2 split folders to delete")

    print("\n" + "=" * 60)
    if args.dry_run:
        print("DRY RUN COMPLETE - No changes made")
    else:
        print("CLEANUP COMPLETE")
    print("=" * 60)


if __name__ == '__main__':
    main()
