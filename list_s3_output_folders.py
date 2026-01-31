"""
List all folders in S3 output bucket and count their files.
"""
import boto3
import csv
from collections import defaultdict

def list_s3_folders():
    """List all folders and files in S3 output bucket."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print(f"Scanning S3 bucket: {bucket}")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    folder_files = defaultdict(list)
    total_files = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            total_files += 1
            
            # Extract folder (first part of path)
            if '/' in key:
                folder = key.split('/')[0]
                folder_files[folder].append(key)
            
            if total_files % 1000 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\nTotal files: {total_files}")
    print(f"Total folders: {len(folder_files)}")
    
    # Create results
    results = []
    for folder, files in sorted(folder_files.items()):
        results.append({
            'Folder': folder,
            'FileCount': len(files)
        })
    
    # Write to CSV
    output_file = 's3_output_folders_inventory.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Folder', 'FileCount'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nExported to {output_file}")
    
    # Show summary
    print("\nTop 10 folders by file count:")
    sorted_results = sorted(results, key=lambda x: x['FileCount'], reverse=True)
    for i, result in enumerate(sorted_results[:10], 1):
        print(f"  {i}. {result['Folder']}: {result['FileCount']} files")
    
    return results

if __name__ == '__main__':
    results = list_s3_folders()
