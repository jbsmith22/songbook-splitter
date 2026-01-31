"""
Fix the Bread folder structure in S3.
Target: Bread/Bread - Best Of Bread/Songs/<files>
"""
import boto3

def main():
    session = boto3.Session(profile_name='default')
    s3 = session.client('s3')
    bucket = 'jsmith-output'
    
    # List all files under Bread/
    print("🔍 Scanning Bread folder structure...")
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket, Prefix='Bread/')
    
    files_to_move = []
    files_to_delete = []
    correct_files = []
    
    for page in pages:
        if 'Contents' not in page:
            continue
        
        for obj in page['Contents']:
            key = obj['Key']
            
            # Target structure: Bread/Bread - Best Of Bread/Songs/<filename>
            if key.startswith('Bread/Bread - Best Of Bread/Songs/') and key.count('/') == 3:
                # Already in correct location
                correct_files.append(key)
            elif key.startswith('Bread/Bread - Best Of Bread/Bread - Best Of Bread/Songs/'):
                # Triple nested - need to move up one level
                filename = key.split('/')[-1]
                new_key = f'Bread/Bread - Best Of Bread/Songs/{filename}'
                files_to_move.append((key, new_key))
            elif key.startswith('Bread/Best Of Bread/Songs/'):
                # Missing artist prefix - need to move to correct location
                filename = key.split('/')[-1]
                new_key = f'Bread/Bread - Best Of Bread/Songs/{filename}'
                files_to_move.append((key, new_key))
            else:
                # Other structure - mark for review
                print(f"⚠️  Unexpected structure: {key}")
    
    print(f"\n📊 Analysis:")
    print(f"   ✅ Already correct: {len(correct_files)} files")
    print(f"   🔄 Need to move: {len(files_to_move)} files")
    
    if correct_files:
        print(f"\n✅ Correct files (sample):")
        for f in correct_files[:3]:
            print(f"   {f}")
    
    if files_to_move:
        print(f"\n🔄 Files to move:")
        for old, new in files_to_move[:5]:
            print(f"   {old}")
            print(f"   → {new}")
        if len(files_to_move) > 5:
            print(f"   ... and {len(files_to_move) - 5} more")
        
        response = input(f"\n❓ Move {len(files_to_move)} files? (yes/no): ")
        if response.lower() == 'yes':
            print("\n🚀 Moving files...")
            for old_key, new_key in files_to_move:
                try:
                    # Copy to new location
                    s3.copy_object(
                        CopySource={'Bucket': bucket, 'Key': old_key},
                        Bucket=bucket,
                        Key=new_key
                    )
                    # Delete old location
                    s3.delete_object(Bucket=bucket, Key=old_key)
                    print(f"   ✅ Moved: {old_key.split('/')[-1]}")
                except Exception as e:
                    print(f"   ❌ Error moving {old_key}: {e}")
            
            print(f"\n✅ Complete! Moved {len(files_to_move)} files")
        else:
            print("❌ Cancelled")
    else:
        print("\n✅ No files need to be moved!")

if __name__ == '__main__':
    main()
