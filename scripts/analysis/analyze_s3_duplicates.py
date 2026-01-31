"""
Analyze S3 book folders to identify duplicates with different naming conventions.
"""
import boto3
import csv
from collections import defaultdict

def normalize_book_name(book_folder):
    """
    Normalize book folder name by removing artist prefix.
    E.g., "Elton John/Elton John - Greatest Hits" -> "Elton John/Greatest Hits"
    """
    parts = book_folder.split('/')
    if len(parts) != 2:
        return book_folder
    
    artist, book = parts
    
    # Remove "Artist - " prefix from book name
    prefix = f"{artist} - "
    if book.startswith(prefix):
        normalized_book = book[len(prefix):]
        return f"{artist}/{normalized_book}"
    
    return book_folder

def list_s3_with_duplicates():
    """List all book folders and identify duplicates."""
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
            
            # Extract book folder (Artist/Book)
            parts = key.split('/')
            if len(parts) >= 2:
                book_folder = f"{parts[0]}/{parts[1]}"
            else:
                continue
                
            book_files[book_folder].append(key)
            
            if total_files % 1000 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\nTotal files: {total_files}")
    print(f"Total book folders (with duplicates): {len(book_files)}")
    
    # Group by normalized name to find duplicates
    normalized_groups = defaultdict(list)
    for book_folder in book_files.keys():
        normalized = normalize_book_name(book_folder)
        normalized_groups[normalized].append(book_folder)
    
    # Find duplicates
    duplicates = {k: v for k, v in normalized_groups.items() if len(v) > 1}
    unique_books = len(normalized_groups)
    
    print(f"Unique books (after normalization): {unique_books}")
    print(f"Books with duplicates: {len(duplicates)}")
    
    # Create results
    results = []
    for book_folder, files in sorted(book_files.items()):
        pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        normalized = normalize_book_name(book_folder)
        is_duplicate = len(normalized_groups[normalized]) > 1
        
        results.append({
            'BookFolder': book_folder,
            'NormalizedName': normalized,
            'PDFCount': len(pdf_files),
            'TotalFiles': len(files),
            'IsDuplicate': 'Yes' if is_duplicate else 'No',
            'DuplicateCount': len(normalized_groups[normalized])
        })
    
    # Write to CSV
    output_file = 's3_books_with_duplicates.csv'
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['BookFolder', 'NormalizedName', 'PDFCount', 'TotalFiles', 'IsDuplicate', 'DuplicateCount'])
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\nExported to {output_file}")
    
    # Show duplicate examples
    print("\nExample duplicates (first 10):")
    for i, (normalized, folders) in enumerate(sorted(duplicates.items())[:10], 1):
        print(f"\n{i}. {normalized}")
        for folder in folders:
            pdf_count = len([f for f in book_files[folder] if f.lower().endswith('.pdf')])
            print(f"   - {folder} ({pdf_count} PDFs)")
    
    return results, unique_books

if __name__ == '__main__':
    results, unique_books = list_s3_with_duplicates()
    print(f"\n=== SUMMARY ===")
    print(f"Total book folders in S3: {len(results)}")
    print(f"Unique books (normalized): {unique_books}")
    print(f"Duplicate folders: {len(results) - unique_books}")
