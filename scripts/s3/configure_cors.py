"""
Configure CORS on the S3 bucket to allow browser access to manifest files
"""
import boto3
import json

S3_BUCKET = 'jsmith-output'

def configure_cors():
    """Add CORS configuration to S3 bucket"""
    s3 = boto3.client('s3')

    # Define CORS rules
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'HEAD'],
                'AllowedOrigins': ['*'],  # Allow from any origin (including file://)
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }
        ]
    }

    print(f"Configuring CORS on bucket: {S3_BUCKET}")
    print(f"CORS configuration:")
    print(json.dumps(cors_configuration, indent=2))
    print()

    try:
        s3.put_bucket_cors(
            Bucket=S3_BUCKET,
            CORSConfiguration=cors_configuration
        )
        print("✓ CORS configuration applied successfully!")
        print()
        print("The bucket now allows:")
        print("  - GET and HEAD requests from any origin")
        print("  - Access to manifest.json and other files from the browser")
        print()
        print("You can now refresh your HTML viewer and the manifest viewer should work.")

    except Exception as e:
        print(f"ERROR: Failed to configure CORS: {e}")
        return False

    return True

if __name__ == '__main__':
    configure_cors()
