"""
Lambda functions for Step Functions state machine integration.

These functions handle:
- Checking processing status
- Recording processing start/completion
- Managing DynamoDB ledger updates
"""

import json
import os
import time
import logging
from typing import Dict, Any
from decimal import Decimal
from datetime import datetime
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
DYNAMODB_TABLE = os.environ.get('DYNAMODB_TABLE', 'jsmith-pipeline-ledger')

# AWS clients
dynamodb = boto3.resource('dynamodb')


def check_processed_handler(event, context):
    """
    Lambda handler to check if book was already processed.

    Args:
        event: Contains book_id and optionally force_reprocess
        context: Lambda context

    Returns:
        Dict with already_processed boolean
    """
    book_id = event.get('book_id')
    force_reprocess = event.get('force_reprocess', False)

    # If force reprocess requested, skip the check
    if force_reprocess:
        logger.info(f"Force reprocess requested for {book_id}, skipping already-processed check")
        return {
            'already_processed': False,
            'book_id': book_id,
            'forced': True
        }

    if not book_id:
        return {
            'already_processed': False,
            'error': 'Missing book_id'
        }
    
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        response = table.get_item(Key={'book_id': book_id})
        
        if 'Item' in response:
            status = response['Item'].get('status')
            already_processed = (status == 'success')
            
            return {
                'already_processed': already_processed,
                'existing_status': status,
                'book_id': book_id
            }
        
        return {
            'already_processed': False,
            'book_id': book_id
        }
        
    except ClientError as e:
        logger.error(f"Error checking processed status: {e}")
        return {
            'already_processed': False,
            'error': str(e),
            'book_id': book_id
        }


def record_start_handler(event, context):
    """
    Lambda handler to record processing start.
    
    Args:
        event: Contains book metadata and execution ARN
        context: Lambda context
    
    Returns:
        Dict with success status
    """
    # Log the received event for debugging
    logger.info(f"Received event: {json.dumps(event)}")
    
    book_id = event.get('book_id')
    source_pdf_uri = event.get('source_pdf_uri')
    artist = event.get('artist')
    book_name = event.get('book_name')
    execution_arn = event.get('execution_arn') or (context.invoked_function_arn if context else None)
    
    if not all([book_id, source_pdf_uri, artist, book_name]):
        logger.error(f"Missing required fields. book_id={book_id}, source_pdf_uri={source_pdf_uri}, artist={artist}, book_name={book_name}")
        return {
            'success': False,
            'error': 'Missing required fields',
            'received_keys': list(event.keys())
        }
    
    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        item = {
            'book_id': book_id,
            'status': 'in_progress',
            'pipeline_version': 'v3',
            'source_pdf_uri': source_pdf_uri,
            'artist': artist,
            'book_name': book_name,
            'current_step': 'toc_discovery',
            'execution_arn': execution_arn,
            'created_at': now_iso,
            'updated_at': now_iso,
            'steps': {}
        }

        table.put_item(Item=item)

        logger.info(f"Recorded processing start for book {book_id}")

        return {
            'success': True,
            'book_id': book_id,
            'created_at': now_iso
        }
        
    except ClientError as e:
        logger.error(f"Error recording start: {e}")
        return {
            'success': False,
            'error': str(e),
            'book_id': book_id
        }


def record_success_handler(event, context):
    """
    Lambda handler to record successful completion.

    Args:
        event: Contains book_id, songs_extracted, total_duration_sec, total_cost_usd
        context: Lambda context

    Returns:
        Dict with success status
    """
    book_id = event.get('book_id')
    songs_extracted = event.get('songs_extracted', 0)
    total_duration_sec = event.get('total_duration_sec')
    total_cost_usd = event.get('total_cost_usd', 0.0)

    if not book_id:
        return {
            'success': False,
            'error': 'Missing book_id'
        }

    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        update_expr = 'SET #status = :status, updated_at = :now'
        expr_attr_names = {'#status': 'status'}
        expr_attr_values = {
            ':status': 'success',
            ':now': now_iso
        }

        if songs_extracted:
            update_expr += ', songs_extracted = :songs_extracted'
            expr_attr_values[':songs_extracted'] = songs_extracted

        if total_duration_sec:
            update_expr += ', total_duration_sec = :duration'
            expr_attr_values[':duration'] = Decimal(str(total_duration_sec))

        if total_cost_usd:
            update_expr += ', total_cost_usd = :cost'
            expr_attr_values[':cost'] = Decimal(str(total_cost_usd))

        table.update_item(
            Key={'book_id': book_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

        logger.info(f"Recorded success for book {book_id}")

        return {
            'success': True,
            'book_id': book_id,
            'status': 'success'
        }

    except ClientError as e:
        logger.error(f"Error recording success: {e}")
        return {
            'success': False,
            'error': str(e),
            'book_id': book_id
        }


def record_failure_handler(event, context):
    """
    Lambda handler to record processing failure.

    Args:
        event: Contains book_id, error_message, current_step
        context: Lambda context

    Returns:
        Dict with success status
    """
    book_id = event.get('book_id')
    error_message = event.get('error_message', 'Unknown error')
    current_step = event.get('current_step')

    if not book_id:
        return {
            'success': False,
            'error': 'Missing book_id'
        }

    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        update_expr = 'SET #status = :status, updated_at = :now, error_message = :error'
        expr_attr_names = {'#status': 'status'}
        expr_attr_values = {
            ':status': 'failed',
            ':now': now_iso,
            ':error': error_message
        }

        if current_step:
            update_expr += ', current_step = :step'
            expr_attr_values[':step'] = current_step

        table.update_item(
            Key={'book_id': book_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

        logger.info(f"Recorded failure for book {book_id}")

        return {
            'success': True,
            'book_id': book_id,
            'status': 'failed'
        }

    except ClientError as e:
        logger.error(f"Error recording failure: {e}")
        return {
            'success': False,
            'error': str(e),
            'book_id': book_id
        }


def record_manual_review_handler(event, context):
    """
    Lambda handler to record manual review status.

    Args:
        event: Contains book_id, reason, current_step
        context: Lambda context

    Returns:
        Dict with success status
    """
    book_id = event.get('book_id')
    reason = event.get('reason', 'Quality gate failed')
    current_step = event.get('current_step')

    if not book_id:
        return {
            'success': False,
            'error': 'Missing book_id'
        }

    try:
        table = dynamodb.Table(DYNAMODB_TABLE)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        update_expr = 'SET #status = :status, updated_at = :now, error_message = :reason'
        expr_attr_names = {'#status': 'status'}
        expr_attr_values = {
            ':status': 'failed',
            ':now': now_iso,
            ':reason': reason
        }

        if current_step:
            update_expr += ', current_step = :step'
            expr_attr_values[':step'] = current_step

        table.update_item(
            Key={'book_id': book_id},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

        logger.info(f"Recorded manual review for book {book_id}")

        return {
            'success': True,
            'book_id': book_id,
            'status': 'failed'
        }

    except ClientError as e:
        logger.error(f"Error recording manual review: {e}")
        return {
            'success': False,
            'error': str(e),
            'book_id': book_id
        }
