"""
List all book folders in S3 output bucket with their file counts.
This goes one level deeper to show Artist/Book structure.
"""
import boto3
import csv
from collections import defaultdict

def list_s3_book_folders():
    """List all book folders and files in S3 output bucket."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print(f"Scanning S3 bucket: {bucket}")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    book_files = defaultdict(list)
    total_files = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            total_files += 1
            
            # Extract book folder (Artist/Book or just Artist if no subfolder)
            parts = key.split('/')
            if len(parts) >= 2:
                # Artist/Book format
                book_folder = f"{parts[0]}/{parts[1]}"
            elif len(parts) == 1:
                # Just artist folder
                book_folder = parts[0]
            else:
                continue
                
            book_files[book_folder].append(key)
            
            if total_files % 1000 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\nTotal files: {total_files}")
    print(f"Total book folders: {len(book_files)}")
    
    # Create results
    results = []
    for book_folder, files in sorted(book_files.items()):
        # Count only PDF files (not artifacts)
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        
        results.append({
            'BookFolder': book_folder,
            'PDFCount': len(pdf_files),
            'TotalFiles': len(files)
        })
    
    # Write to CSV
    output_file = 's3_book_folders_inventory.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['BookFolder', 'PDFCount', 'TotalFiles'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nExported to {output_file}")
    
    # Show summary
    total_pdfs = sum(r['PDFCount'] for r in results)
    print(f"\nTotal PDF files: {total_pdfs}")
    print(f"Total book folders: {len(results)}")
    
    print("\nTop 20 book folders by PDF count:")
    sorted_results = sorted(results, key=lambda x: x['PDFCount'], reverse=True)
    for i, result in enumerate(sorted_results[:20], 1):
        print(f"  {i}. {result['BookFolder']}: {result['PDFCount']} PDFs")
    
    return results

if __name__ == '__main__':
    results = list_s3_book_folders()
