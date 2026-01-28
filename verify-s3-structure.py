#!/usr/bin/env python3
"""
Check the actual S3 structure to understand folder naming patterns.
"""
import boto3

def main():
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    # Sample a few artists to see the pattern
    test_artists = ['Acdc', 'Beatles', 'Billy Joel']
    
    for artist in test_artists:
        print(f"\n{artist}:")
        print("=" * 60)
        
        paginator = s3.get_paginator('list_objects_v2')
        folders = set()
        
        for page in paginator.paginate(Bucket=bucket, Prefix=f'{artist}/', Delimiter='/'):
            if 'CommonPrefixes' in page:
                for prefix in page['CommonPrefixes']:
                    folder = prefix['Prefix'].rstrip('/')
                    folders.add(folder)
        
        for folder in sorted(folders):
            print(f"  {folder}")

if __name__ == '__main__':
    main()
