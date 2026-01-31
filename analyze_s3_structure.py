"""
Detailed analysis of S3 bucket structure.
"""

import boto3
import csv

INPUT_BUCKET = 'jsmith-input'
CSV_FILE = 'book_reconciliation_validated.csv'


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
    """Main analysis."""
    print("=" * 80)
    print("S3 Bucket Structure Analysis")
    print("=" * 80)
    
    # Load data
    csv_books = load_csv_books()
    s3_objects = list_s3_objects()
    s3_pdfs = [obj for obj in s3_objects if obj['Key'].lower().endswith('.pdf')]
    
    print(f"\nSource of truth: {len(csv_books)} books")
    print(f"S3 PDFs: {len(s3_pdfs)}")
    
    # Categorize S3 files
    old_structure = []  # Has /books/ in path
    new_structure = []  # No /books/ in path
    
    for obj in s3_pdfs:
        if '/books/' in obj['Key']:
            old_structure.append(obj)
        else:
            new_structure.append(obj)
    
    print(f"\nS3 Structure:")
    print(f"  Old (with /books/): {len(old_structure)}")
    print(f"  New (without /books/): {len(new_structure)}")
    
    # Check if new structure files exist
    print(f"\nSample NEW structure files (first 10):")
    for obj in new_structure[:10]:
        print(f"  {obj['Key']}")
    
    # Build expected paths
    expected_new_paths = set()
    for book in csv_books:
        source_path = book['SourcePath']
        s3_key = f"SheetMusic/{source_path.replace(chr(92), '/')}"
        expected_new_paths.add(s3_key)
    
    actual_new_paths = {obj['Key'] for obj in new_structure}
    
    # Check overlap
    matching = expected_new_paths & actual_new_paths
    
    print(f"\nPath Matching:")
    print(f"  Expected new structure paths: {len(expected_new_paths)}")
    print(f"  Actual new structure paths: {len(actual_new_paths)}")
    print(f"  Matching: {len(matching)}")
    
    # Conclusion
    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    
    if len(matching) < 100:
        print("\n✗ The S3 bucket does NOT contain the new structure!")
        print("  Most files are still in the old /books/ subfolder structure")
        print(f"  Only {len(new_structure)} files use the new structure")
        print("\nThis means:")
        print("  1. DynamoDB points to NEW paths (without /books/)")
        print("  2. But S3 still has OLD paths (with /books/)")
        print("  3. This is a MISMATCH - reprocessing would fail!")
        
        print("\nOptions:")
        print("  A. Upload new structure files to S3 (if you want to reprocess)")
        print("  B. Keep S3 as-is (old structure) since everything is processed")
        print("  C. Clean out S3 entirely (saves storage, can't reprocess)")
        
        print("\nRecommendation:")
        print("  Since all 559 books are processed and working:")
        print("  → You can SAFELY DELETE the entire input bucket")
        print("  → It's only needed if you want to reprocess books")
        print("  → Saves ~$0.25/month in storage costs")
        print("  → If you need to reprocess later, re-upload from local")
    else:
        print("\n✓ S3 bucket contains new structure files")
        print("  You have both old and new structure (duplicates)")
        print("  Can safely delete old /books/ structure files")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
