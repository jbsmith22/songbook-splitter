import boto3

s3 = boto3.client('s3', region_name='us-east-1')
bucket = 'jsmith-output'

# Search for Crosby folders
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=bucket, Prefix='Crosby')

print("CROSBY FOLDERS IN S3:")
print("=" * 80)

found = False
for page in pages:
    if 'Contents' not in page:
        continue
    
    for obj in page['Contents']:
        key = obj['Key']
        if 'Deja Vu' in key:
            print(key)
            found = True

if not found:
    print("No Deja Vu files found")
