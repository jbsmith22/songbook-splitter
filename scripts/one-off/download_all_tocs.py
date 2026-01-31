#!/usr/bin/env python3
"""
Download all TOC files from S3 to analyze locally.
"""

import json
import boto3
from pathlib import Path

S3_BUCKET = "jsmith-output"
TOC_CACHE_DIR = Path("toc_cache")

def get_s3_client():
    """Get boto3 S3 client."""
    return boto3.client('s3', region_name='us-east-1')

def list_book_artifacts():
    """List all book artifacts in S3."""
    s3 = get_s3_client()
    
    try:
        response = s3.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix='artifacts/',
            Delimiter='/'
        )
        
        book_ids = []
        if 'CommonPrefixes' in response:
            for prefix in response['CommonPrefixes']:
                book_id = prefix['Prefix'].split('/')[-2]
                book_ids.append(book_id)
        
        return book_ids
    except Exception as e:
        print(f"Error listing S3 artifacts: {e}")
        return []

def download_toc(book_id):
    """Download TOC and output files for a book."""
    s3 = get_s3_client()
    
    # Download toc_parse.json
    toc_key = f"artifacts/{book_id}/toc_parse.json"
    output_key = f"artifacts/{book_id}/output_files.json"
    
    toc_data = None
    output_data = None
    
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=toc_key)
        toc_data = json.loads(response['Body'].read())
    except:
        pass
    
    try:
        response = s3.get_object(Bucket=S3_BUCKET, Key=output_key)
        output_data = json.loads(response['Body'].read())
    except:
        pass
    
    return toc_data, output_data

def save_toc_cache(book_id, toc_data, output_data):
    """Save TOC data to local cache."""
    TOC_CACHE_DIR.mkdir(exist_ok=True)
    
    cache_file = TOC_CACHE_DIR / f"{book_id}.json"
    
    with open(cache_file, 'w') as f:
        json.dump({
            'book_id': book_id,
            'toc': toc_data,
            'output': output_data
        }, f, indent=2)

if __name__ == "__main__":
    print("Downloading all TOC files from S3...")
    print("=" * 80)
    
    # List all book artifacts
    print("\n1. Listing book artifacts...")
    book_ids = list_book_artifacts()
    print(f"   Found {len(book_ids)} book artifacts in S3")
    
    # Download each TOC
    print("\n2. Downloading TOC files...")
    successful = 0
    failed = 0
    
    for i, book_id in enumerate(book_ids, 1):
        if i % 50 == 0:
            print(f"   Progress: {i}/{len(book_ids)} ({successful} successful, {failed} failed)")
        
        toc, output = download_toc(book_id)
        
        if toc or output:
            save_toc_cache(book_id, toc, output)
            successful += 1
        else:
            failed += 1
    
    print(f"\n✓ Downloaded {successful} TOC files")
    print(f"✗ Failed to download {failed} TOC files")
    print(f"\nTOC files saved to: {TOC_CACHE_DIR}/")
