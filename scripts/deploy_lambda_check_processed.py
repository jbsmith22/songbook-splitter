"""
Deploy the updated check-processed Lambda function

This updates the jsmith-sheetmusic-splitter-check-processed function
with the force_reprocess flag support.
"""
import boto3
import zipfile
import os
from pathlib import Path
import tempfile

FUNCTION_NAME = 'jsmith-sheetmusic-splitter-check-processed'
SOURCE_FILE = 'lambda/state_machine_helpers.py'

def create_deployment_package():
    """Create a ZIP file with the Lambda code"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        zip_path = tmp.name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add the state_machine_helpers.py file
        zipf.write(SOURCE_FILE, 'state_machine_helpers.py')

        print(f'Created deployment package: {zip_path}')
        print(f'  - Added: {SOURCE_FILE}')

    return zip_path

def deploy_lambda(zip_path):
    """Deploy the ZIP to Lambda"""
    client = boto3.client('lambda')

    with open(zip_path, 'rb') as f:
        zip_content = f.read()

    print(f'\nDeploying to Lambda function: {FUNCTION_NAME}')
    print(f'Package size: {len(zip_content) / 1024:.2f} KB')

    response = client.update_function_code(
        FunctionName=FUNCTION_NAME,
        ZipFile=zip_content
    )

    print(f'\nDeployment successful!')
    print(f'Function ARN: {response["FunctionArn"]}')
    print(f'Last Modified: {response["LastModified"]}')
    print(f'Code Size: {response["CodeSize"]} bytes')

    # Clean up
    os.unlink(zip_path)

if __name__ == '__main__':
    print('='*80)
    print('DEPLOYING LAMBDA FUNCTION: check-processed')
    print('='*80)
    print()
    print('This will update the Lambda function to support force_reprocess flag.')
    print()

    # Create deployment package
    zip_path = create_deployment_package()

    # Deploy
    try:
        deploy_lambda(zip_path)
        print()
        print('='*80)
        print('DEPLOYMENT COMPLETE')
        print('='*80)
        print()
        print('The Lambda function now supports force_reprocess.')
        print('Next time you click "Reprocess" in the viewer, it will actually reprocess!')
    except Exception as e:
        print(f'\nError deploying: {e}')
        os.unlink(zip_path)
        raise
