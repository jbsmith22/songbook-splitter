"""
Empty an S3 bucket of all object versions and delete markers using boto3.
Reliable, no PowerShell/JSON-file-path quoting issues.

Usage:
    python empty_s3_bucket.py jsmith-input
    python empty_s3_bucket.py jsmith-output
"""
import sys
import boto3
from botocore.exceptions import ClientError

def empty_bucket(bucket_name, region='us-east-1'):
    s3 = boto3.client('s3', region_name=region)
    
    print(f"Emptying s3://{bucket_name}/")
    
    total_deleted = 0
    
    # Use the paginator for clean pagination
    paginator = s3.get_paginator('list_object_versions')
    
    try:
        for page in paginator.paginate(Bucket=bucket_name):
            objects_to_delete = []
            
            for v in page.get('Versions', []):
                objects_to_delete.append({'Key': v['Key'], 'VersionId': v['VersionId']})
            
            for m in page.get('DeleteMarkers', []):
                objects_to_delete.append({'Key': m['Key'], 'VersionId': m['VersionId']})
            
            if not objects_to_delete:
                continue
            
            # delete-objects accepts up to 1000 per call; each page is already <= 1000
            response = s3.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': objects_to_delete, 'Quiet': True}
            )
            
            deleted_count = len(objects_to_delete)
            total_deleted += deleted_count
            
            errors = response.get('Errors', [])
            if errors:
                print(f"  Batch had {len(errors)} errors:")
                for e in errors[:3]:
                    print(f"    {e.get('Code')}: {e.get('Key')} - {e.get('Message')}")
            
            print(f"  Deleted batch of {deleted_count} items (total: {total_deleted:,})")
    
    except ClientError as e:
        code = e.response.get('Error', {}).get('Code', '?')
        if code == 'NoSuchBucket':
            print(f"  Bucket does not exist (already deleted?)")
            return 0
        raise
    
    print(f"\nDone. Total deleted from {bucket_name}: {total_deleted:,}")
    return total_deleted


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python empty_s3_bucket.py <bucket-name>")
        sys.exit(1)
    
    bucket = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    empty_bucket(bucket, region)
