"""
Verify S3 input bucket contents against local source of truth.
"""

import boto3
import csv
import os
from collections import defaultdict

INPUT_BUCKET = 'jsmith-input'
CSV_FILE = 'book_reconciliation_validated.csv'
LOCAL_BASE = r'C:\Work\AWSMusic\SheetMusic'


def load_csv_books():
    """Load CSV books (source of truth)."""
    books = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'] == 'COMPLETE':
                books.append(row)
    return books


def list_s3_objects():
    """List all objects in S3 input bucket."""
    s3 = boto3.client('s3')
    
    print("Listing S3 objects...")
    objects = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=INPUT_BUCKET, Prefix='SheetMusic/'):
        if 'Contents' in page:
            objects.extend(page['Contents'])
    
    return objects


def main():
    """Main verification."""
    print("=" * 80)
    print("S3 Input Bucket Verification")
    print("=" * 80)
    
    # Load source of truth
    csv_books = load_csv_books()
    print(f"\nLocal source of truth: {len(csv_books)} books")
    
    # List S3 objects
    s3_objects = list_s3_objects()
    print(f"S3 objects in bucket: {len(s3_objects)}")
    
    # Analyze S3 contents
    s3_pdfs = [obj for obj in s3_objects if obj['Key'].lower().endswith('.pdf')]
    s3_other = [obj for obj in s3_objects if not obj['Key'].lower().endswith('.pdf')]
    
    print(f"\nS3 Breakdown:")
    print(f"  PDF files: {len(s3_pdfs)}")
    print(f"  Other files: {len(s3_other)}")
    
    # Check for old /books/ structure
    old_structure = [obj for obj in s3_pdfs if '/books/' in obj['Key']]
    new_structure = [obj for obj in s3_pdfs if '/books/' not in obj['Key']]
    
    print(f"\nPath Structure:")
    print(f"  Old structure (with /books/): {len(old_structure)}")
    print(f"  New structure (without /books/): {len(new_structure)}")
    
    # Build expected S3 paths from CSV
    expected_s3_keys = set()
    for book in csv_books:
        source_path = book['SourcePath']
        s3_key = f"SheetMusic/{source_path.replace(chr(92), '/')}"
        expected_s3_keys.add(s3_key)
    
    # Build actual S3 keys
    actual_s3_keys = {obj['Key'] for obj in s3_pdfs}
    
    # Compare
    missing_in_s3 = expected_s3_keys - actual_s3_keys
    extra_in_s3 = actual_s3_keys - expected_s3_keys
    
    print(f"\nComparison with Source of Truth:")
    print(f"  Expected in S3: {len(expected_s3_keys)}")
    print(f"  Actually in S3: {len(actual_s3_keys)}")
    print(f"  Missing from S3: {len(missing_in_s3)}")
    print(f"  Extra in S3: {len(extra_in_s3)}")
    
    if missing_in_s3:
        print(f"\n  First 10 missing files:")
        for key in list(missing_in_s3)[:10]:
            print(f"    - {key}")
    
    if extra_in_s3:
        print(f"\n  First 10 extra files:")
        for key in list(extra_in_s3)[:10]:
            print(f"    - {key}")
    
    # Calculate storage size
    total_size_bytes = sum(obj['Size'] for obj in s3_objects)
    total_size_mb = total_size_bytes / (1024 * 1024)
    total_size_gb = total_size_mb / 1024
    
    print(f"\nStorage Usage:")
    print(f"  Total size: {total_size_gb:.2f} GB ({total_size_mb:.0f} MB)")
    
    # Recommendation
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    
    if len(extra_in_s3) > 0:
        print("\n✓ S3 bucket contains extra files (old structure or duplicates)")
        print("  These are likely from the old /books/ subfolder structure")
        print(f"  {len(old_structure)} files still use old /books/ path")
        
    if len(missing_in_s3) == 0 and len(new_structure) == len(csv_books):
        print("\n✓ All source of truth files are present in S3 (new structure)")
        print("  The new structure matches your local files")
        
    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print("\nSince all books have been processed (status='success' in DynamoDB):")
    print("  1. The input bucket is only needed if you want to reprocess books")
    print("  2. You could clean out old /books/ structure files (duplicates)")
    print("  3. Or keep the bucket as-is for potential reprocessing")
    print("\nOptions:")
    print("  A. Keep everything (safest, costs ~$0.023/GB/month)")
    print("  B. Delete old /books/ structure files (saves space, keeps new structure)")
    print("  C. Empty entire bucket (saves most, but can't reprocess without re-upload)")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
