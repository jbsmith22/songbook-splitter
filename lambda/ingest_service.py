"""
Ingest Service Lambda - Discovers PDFs and initiates Step Functions executions.

This Lambda function:
- Scans S3 for PDFs matching the pattern
- Checks DynamoDB for already-processed books
- Starts Step Functions execution for each new book
"""

import json
import os
import time
import logging
from typing import List, Dict, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
INPUT_BUCKET = os.environ.get('INPUT_BUCKET', 'jsmith-input')
INPUT_PREFIX = os.environ.get('INPUT_PREFIX', 'v3/')
STATE_MACHINE_ARN = os.environ.get('STATE_MACHINE_ARN')
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'jsmith-pipeline-ledger')

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
sfn_client = boto3.client('stepfunctions')


def lambda_handler(event, context):
    """
    Lambda handler for PDF discovery and ingestion.
    
    Triggered by:
    - CloudWatch Events (scheduled)
    - Manual invocation
    - S3 event notifications
    
    Args:
        event: Lambda event
        context: Lambda context
    
    Returns:
        Response with execution ARNs
    """
    logger.info(f"Starting PDF discovery in s3://{INPUT_BUCKET}/{INPUT_PREFIX}")
    
    try:
        # Discover PDFs
        pdfs = discover_pdfs(INPUT_BUCKET, INPUT_PREFIX)
        logger.info(f"Discovered {len(pdfs)} PDFs")
        
        # Process each PDF
        executions = []
        skipped = []
        
        for pdf in pdfs:
            # Check if already processed
            if check_already_processed(pdf['book_id']):
                logger.info(f"Skipping already processed book: {pdf['book_id']}")
                skipped.append(pdf['book_id'])
                continue
            
            # Start Step Functions execution
            execution_arn = start_step_function(pdf)
            if execution_arn:
                executions.append(execution_arn)
                logger.info(f"Started execution for {pdf['book_id']}: {execution_arn}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'pdfs_discovered': len(pdfs),
                'executions_started': len(executions),
                'books_skipped': len(skipped),
                'execution_arns': executions
            })
        }
        
    except Exception as e:
        logger.error(f"Error in ingest service: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }


def discover_pdfs(bucket: str, prefix: str) -> List[Dict[str, Any]]:
    """
    Scan S3 bucket for PDFs matching v3 pattern.

    Pattern: v3/<Artist>/<Artist> - <Book>.pdf

    Args:
        bucket: S3 bucket name
        prefix: S3 prefix to search (default: 'v3/')

    Returns:
        List of PDF metadata dictionaries
    """
    pdfs = []

    try:
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

        for page in pages:
            if 'Contents' not in page:
                continue

            for obj in page['Contents']:
                key = obj['Key']

                if not key.lower().endswith('.pdf'):
                    continue

                # v3 pattern: v3/<Artist>/<Artist> - <Book>.pdf
                parts = key.split('/')
                if len(parts) >= 3 and parts[0] == 'v3':
                    artist = parts[1]
                    filename = parts[2]
                    book_name = filename.replace('.pdf', '')

                    # Strip "Artist - " prefix from book_name if present
                    if ' - ' in book_name:
                        book_name = book_name.split(' - ', 1)[1]

                    # Generate book ID
                    s3_uri = f"s3://{bucket}/{key}"
                    book_id = generate_book_id(s3_uri)

                    pdfs.append({
                        'book_id': book_id,
                        's3_uri': s3_uri,
                        'bucket': bucket,
                        'key': key,
                        'artist': artist,
                        'book_name': book_name,
                        'size': obj.get('Size', 0)
                    })

        return pdfs

    except ClientError as e:
        logger.error(f"Error listing S3 objects: {e}")
        raise


def generate_book_id(s3_uri: str) -> str:
    """Generate unique book ID from S3 URI."""
    import hashlib
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def check_already_processed(book_id: str) -> bool:
    """
    Check if book has already been successfully processed.
    
    Args:
        book_id: Unique book identifier
    
    Returns:
        True if already processed successfully
    """
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(Key={'book_id': book_id})
        
        if 'Item' in response:
            status = response['Item'].get('status')
            if status == 'success':
                return True
        
        return False
        
    except ClientError as e:
        logger.error(f"Error checking DynamoDB: {e}")
        # On error, assume not processed to allow retry
        return False


def start_step_function(pdf_metadata: Dict[str, Any]) -> str:
    """
    Start Step Functions execution for a PDF.
    
    Args:
        pdf_metadata: PDF metadata dictionary
    
    Returns:
        Execution ARN or None if failed
    """
    if not STATE_MACHINE_ARN:
        logger.error("STATE_MACHINE_ARN not configured")
        return None
    
    try:
        # Prepare input for Step Functions
        execution_input = {
            'book_id': pdf_metadata['book_id'],
            'source_pdf_uri': pdf_metadata['s3_uri'],
            'bucket': pdf_metadata['bucket'],
            'key': pdf_metadata['key'],
            'artist': pdf_metadata['artist'],
            'book_name': pdf_metadata['book_name']
        }
        
        # Start execution
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"book-{pdf_metadata['book_id']}-{int(time.time())}",
            input=json.dumps(execution_input)
        )
        
        return response['executionArn']
        
    except ClientError as e:
        logger.error(f"Error starting Step Functions execution: {e}")
        return None


# For local testing
if __name__ == '__main__':
    import time
    
    # Mock event
    test_event = {}
    
    # Mock context
    class MockContext:
        function_name = 'ingest-service'
        memory_limit_in_mb = 512
        invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:ingest-service'
        aws_request_id = 'test-request-id'
    
    result = lambda_handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
