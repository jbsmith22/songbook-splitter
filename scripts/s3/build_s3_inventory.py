"""
Build a complete CSV inventory of all folders and files in S3 bucket.
"""
import boto3
import csv
from datetime import datetime

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    print("🔍 Building complete S3 inventory...")
    print(f"   Bucket: {bucket}\n")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    all_objects = []
    file_count = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
        
        for obj in page['Contents']:
            key = obj['Key']
            size = obj['Size']
            last_modified = obj['LastModified']
            
            # Parse path
            parts = key.split('/')
            depth = len(parts)
            
            artist = parts[0] if len(parts) > 0 else ''
            book = parts[1] if len(parts) > 1 else ''
            filename = parts[-1] if len(parts) > 0 else ''
            
            # Determine if it's a PDF
            is_pdf = key.lower().endswith('.pdf')
            
            all_objects.append({
                'full_path': key,
                'artist': artist,
                'book': book,
                'filename': filename,
                'depth': depth,
                'size_bytes': size,
                'size_mb': round(size / (1024 * 1024), 2),
                'last_modified': last_modified.isoformat(),
                'is_pdf': is_pdf
            })
            
            file_count += 1
            if file_count % 1000 == 0:
                print(f"   Processed {file_count} objects...")
    
    print(f"\n📊 Total objects: {len(all_objects)}")
    
    # Write CSV
    csv_file = 's3_complete_inventory.csv'
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['full_path', 'artist', 'book', 'filename', 'depth', 
                     'size_bytes', 'size_mb', 'last_modified', 'is_pdf']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_objects)
    
    print(f"📄 Inventory written to: {csv_file}")
    
    # Statistics
    pdf_count = sum(1 for obj in all_objects if obj['is_pdf'])
    total_size_gb = sum(obj['size_bytes'] for obj in all_objects) / (1024 * 1024 * 1024)
    
    # Count by depth
    depth_counts = {}
    for obj in all_objects:
        depth = obj['depth']
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    # Count by artist
    artist_counts = {}
    for obj in all_objects:
        if obj['is_pdf']:
            artist = obj['artist']
            artist_counts[artist] = artist_counts.get(artist, 0) + 1
    
    print(f"\n📊 Statistics:")
    print(f"   Total objects: {len(all_objects):,}")
    print(f"   PDF files: {pdf_count:,}")
    print(f"   Total size: {total_size_gb:.2f} GB")
    
    print(f"\n📁 Files by depth:")
    for depth in sorted(depth_counts.keys()):
        print(f"   Depth {depth}: {depth_counts[depth]:,} files")
    
    print(f"\n🎵 Top 20 artists by file count:")
    for artist, count in sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
        print(f"   {artist:<40} {count:>6} files")
    
    print(f"\n✅ Complete inventory saved to {csv_file}")

if __name__ == '__main__':
    main()
