"""
Enable CORS on jsmith-output S3 bucket for manual split editor
"""
import boto3
import json

def enable_cors():
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'

    cors_configuration = {
        'CORSRules': [{
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'HEAD'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3000
        }]
    }

    print(f'Enabling CORS on {bucket}...')
    s3.put_bucket_cors(
        Bucket=bucket,
        CORSConfiguration=cors_configuration
    )

    print('CORS enabled successfully!')
    print('\nConfiguration:')
    print(json.dumps(cors_configuration, indent=2))
    print('\nYou can now access S3 resources from the browser.')

if __name__ == '__main__':
    enable_cors()
