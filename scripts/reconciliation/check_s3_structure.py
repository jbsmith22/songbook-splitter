"""
Check if S3 files are stored under book_id path or artist/book path
"""
import boto3

s3 = boto3.client('s3')
S3_BUCKET = 'jsmith-output'

book_id = '8e5ac0bec0eeed0f'  # Adele
artist_path = 'Adele/19 [pvg Book]'

print("Checking both possible S3 structures...\n")

# Check 1: Under book_id
print(f"1. Checking output/{book_id}/...")
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f'output/{book_id}/'):
    if 'Contents' in page:
        pdf_files = [obj for obj in page['Contents'] if obj['Key'].endswith('.pdf')]
        print(f"   Found {len(pdf_files)} PDF files")
        for obj in pdf_files[:5]:
            print(f"     - {obj['Key']}")
        if len(pdf_files) > 5:
            print(f"     ... and {len(pdf_files) - 5} more")
        if len(pdf_files) == 0:
            print(f"   No PDF files found (only manifest/artifacts)")
        break
else:
    print(f"   No objects found at all")

# Check 2: Under artist/book path
print(f"\n2. Checking output/{artist_path}/...")
try:
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f'output/{artist_path}/'):
        if 'Contents' in page:
            pdf_files = [obj for obj in page['Contents'] if obj['Key'].endswith('.pdf')]
            print(f"   Found {len(pdf_files)} PDF files")
            for obj in pdf_files[:5]:
                print(f"     - {obj['Key']}")
            if len(pdf_files) > 5:
                print(f"     ... and {len(pdf_files) - 5} more")
            break
    else:
        print(f"   No objects found")
except Exception as e:
    print(f"   ERROR: {e}")

# Check 3: With Songs subfolder
print(f"\n3. Checking output/{artist_path}/Songs/...")
try:
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f'output/{artist_path}/Songs/'):
        if 'Contents' in page:
            pdf_files = [obj for obj in page['Contents'] if obj['Key'].endswith('.pdf')]
            print(f"   Found {len(pdf_files)} PDF files")
            for obj in pdf_files[:5]:
                print(f"     - {obj['Key']}")
            if len(pdf_files) > 5:
                print(f"     ... and {len(pdf_files) - 5} more")
            break
    else:
        print(f"   No objects found")
except Exception as e:
    print(f"   ERROR: {e}")
