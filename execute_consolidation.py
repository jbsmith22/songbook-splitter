"""
Execute the S3 consolidation plan.
Reads s3_consolidate_plan.csv and performs the moves and deletes.
"""
import boto3
import csv
from collections import defaultdict

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    # Read the plan
    csv_file = 's3_consolidate_plan.csv'
    print(f"📄 Reading plan from {csv_file}...")
    
    moves = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        moves = list(reader)
    
    print(f"📊 Plan contains {len(moves)} operations\n")
    
    # Confirm
    response = input(f"❓ Execute consolidation of {len(moves)} files? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Cancelled")
        return
    
    print("\n🚀 Starting consolidation...\n")
    
    success_count = 0
    error_count = 0
    errors = []
    
    # Group by artist for progress reporting
    by_artist = defaultdict(list)
    for move in moves:
        by_artist[move['artist']].append(move)
    
    total_artists = len(by_artist)
    current_artist = 0
    
    for artist, artist_moves in sorted(by_artist.items()):
        current_artist += 1
        print(f"\n[{current_artist}/{total_artists}] Processing {artist} ({len(artist_moves)} files)...")
        
        for move in artist_moves:
            source = move['source_path']
            target = move['target_path']
            
            try:
                # Copy to target
                s3.copy_object(
                    CopySource={'Bucket': bucket, 'Key': source},
                    Bucket=bucket,
                    Key=target
                )
                
                # Delete source
                s3.delete_object(Bucket=bucket, Key=source)
                
                success_count += 1
                
                if success_count % 100 == 0:
                    print(f"   ✅ Processed {success_count}/{len(moves)} files...")
                
            except Exception as e:
                error_count += 1
                error_msg = f"{source} -> {target}: {str(e)}"
                errors.append(error_msg)
                print(f"   ❌ Error: {move['filename']}: {str(e)}")
    
    print(f"\n{'='*80}")
    print(f"✅ Consolidation complete!")
    print(f"   Success: {success_count} files")
    print(f"   Errors: {error_count} files")
    
    if errors:
        print(f"\n❌ Errors encountered:")
        for error in errors[:10]:
            print(f"   {error}")
        if len(errors) > 10:
            print(f"   ... and {len(errors) - 10} more")
        
        # Write errors to file
        with open('consolidation_errors.txt', 'w', encoding='utf-8') as f:
            for error in errors:
                f.write(error + '\n')
        print(f"\n   Full error log written to: consolidation_errors.txt")
    
    # Now clean up empty folders
    print(f"\n🧹 Cleaning up empty folders...")
    
    # Get list of folders to check (the "other" folders without artist prefix)
    folders_to_check = set()
    for move in moves:
        # Extract the "other" folder path
        parts = move['source_path'].split('/')
        if len(parts) >= 2:
            folder_path = f"{parts[0]}/{parts[1]}/"
            folders_to_check.add(folder_path)
    
    print(f"   Checking {len(folders_to_check)} folders...")
    
    deleted_folders = 0
    for folder in sorted(folders_to_check):
        # Check if folder is empty
        response = s3.list_objects_v2(Bucket=bucket, Prefix=folder, MaxKeys=1)
        
        if 'Contents' not in response or len(response['Contents']) == 0:
            # Folder is empty - nothing to delete (S3 doesn't have folders)
            deleted_folders += 1
            print(f"   ✓ Empty: {folder}")
        else:
            print(f"   ⚠️  Not empty: {folder} ({len(response.get('Contents', []))} files remain)")
    
    print(f"\n✅ Cleanup complete!")
    print(f"   {deleted_folders} folders are now empty (will not appear in listings)")
    print(f"\n🎉 All done! Your S3 bucket is now consolidated.")

if __name__ == '__main__':
    main()
