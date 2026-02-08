"""
DynamoDB ledger module for tracking processing state and idempotency.

This module provides functions for:
- Checking if a book has already been processed
- Recording processing start, completion, and failure states
- Supporting local mode with mock DynamoDB
"""

import hashlib
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


@dataclass
class LedgerEntry:
    """Represents a v3 processing ledger entry."""
    book_id: str
    artist: str
    book_name: str
    pipeline_version: str  # "v3"
    status: str  # "pending", "in_progress", "success", "failed"
    source_pdf_uri: str
    current_step: Optional[str] = None  # Which step is active or failed at
    source_pdf_hash: Optional[str] = None  # MD5 of original PDF
    source_pdf_size: Optional[int] = None  # File size in bytes
    source_pdf_pages: Optional[int] = None  # Total page count
    songs_extracted: Optional[int] = None  # Final actual count (null until complete)
    total_cost_usd: Optional[float] = None  # Sum of all step costs
    total_duration_sec: Optional[float] = None  # Sum of all step durations
    execution_arn: Optional[str] = None  # Step Function execution ARN
    error_message: Optional[str] = None  # Top-level error if failed
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    steps: Optional[Dict[str, Any]] = None  # Per-step tracking map


class MockDynamoDB:
    """Mock DynamoDB implementation for local mode."""
    
    def __init__(self):
        self._data: Dict[str, LedgerEntry] = {}
        logger.info("MockDynamoDB initialized")
    
    def put_item(self, table_name: str, item: Dict[str, Any]) -> None:
        """Mock put_item operation."""
        book_id = item['book_id']
        self._data[book_id] = item
        logger.info(f"MockDynamoDB: Stored item with book_id={book_id}")
    
    def get_item(self, table_name: str, key: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Mock get_item operation."""
        book_id = key['book_id']
        item = self._data.get(book_id)
        if item:
            logger.info(f"MockDynamoDB: Retrieved item with book_id={book_id}")
        else:
            logger.info(f"MockDynamoDB: No item found with book_id={book_id}")
        return item
    
    def query(self, table_name: str, key_condition: str, **kwargs) -> list:
        """Mock query operation."""
        # Simple implementation - return all items matching status if provided
        results = []
        filter_status = kwargs.get('filter_status')
        
        for item in self._data.values():
            if filter_status is None or item.get('status') == filter_status:
                results.append(item)
        
        logger.info(f"MockDynamoDB: Query returned {len(results)} items")
        return results


class DynamoDBLedger:
    """DynamoDB ledger for tracking book processing state."""
    
    def __init__(self, table_name: str = 'jsmith-pipeline-ledger',
                 local_mode: bool = False):
        """
        Initialize DynamoDB ledger.
        
        Args:
            table_name: Name of the DynamoDB table
            local_mode: If True, use mock DynamoDB instead of real service
        """
        self.table_name = table_name
        self.local_mode = local_mode
        
        if local_mode:
            self.db = MockDynamoDB()
            logger.info(f"DynamoDBLedger initialized in local mode")
        else:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"DynamoDBLedger initialized with table: {table_name}")
    
    def generate_book_id(self, s3_uri: str) -> str:
        """
        Generate unique book ID from S3 URI.
        
        Args:
            s3_uri: S3 URI of the source PDF
        
        Returns:
            SHA256 hash of the S3 URI
        """
        return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]
    
    def check_already_processed(self, book_id: str) -> bool:
        """
        Check if a book has already been successfully processed.
        
        Args:
            book_id: Unique identifier for the book
        
        Returns:
            True if book was already processed successfully
        """
        try:
            if self.local_mode:
                item = self.db.get_item(self.table_name, {'book_id': book_id})
            else:
                response = self.table.get_item(Key={'book_id': book_id})
                item = response.get('Item')
            
            if item and item.get('status') == 'success':
                logger.info(f"Book {book_id} already processed successfully")
                return True
            
            logger.info(f"Book {book_id} not yet processed or failed previously")
            return False
            
        except ClientError as e:
            logger.error(f"Error checking processing status: {e}")
            # On error, assume not processed to allow retry
            return False
    
    def record_processing_start(self, source_pdf_uri: str, artist: str,
                                book_name: str, execution_arn: Optional[str] = None) -> str:
        """
        Record the start of processing for a book.

        Args:
            source_pdf_uri: S3 URI of the source PDF
            artist: Artist name
            book_name: Book name
            execution_arn: Step Functions execution ARN (optional)

        Returns:
            Generated book_id
        """
        book_id = self.generate_book_id(source_pdf_uri)
        now_iso = datetime.utcnow().isoformat() + 'Z'

        entry = LedgerEntry(
            book_id=book_id,
            artist=artist,
            book_name=book_name,
            pipeline_version='v3',
            status='in_progress',
            source_pdf_uri=source_pdf_uri,
            current_step='toc_discovery',
            execution_arn=execution_arn,
            created_at=now_iso,
            updated_at=now_iso,
            steps={}
        )

        try:
            item = asdict(entry)
            # Remove None values
            item = {k: v for k, v in item.items() if v is not None}

            if self.local_mode:
                self.db.put_item(self.table_name, item)
            else:
                self.table.put_item(Item=item)

            logger.info(f"Recorded processing start for book {book_id}")
            return book_id

        except ClientError as e:
            logger.error(f"Error recording processing start: {e}")
            raise
    
    def record_processing_complete(self, book_id: str, status: str,
                                   songs_extracted: Optional[int] = None,
                                   total_duration_sec: Optional[float] = None,
                                   total_cost_usd: Optional[float] = None,
                                   error_message: Optional[str] = None) -> None:
        """
        Record the completion of processing for a book.

        Args:
            book_id: Unique identifier for the book
            status: Final status ("success", "failed")
            songs_extracted: Number of songs successfully extracted
            total_duration_sec: Total processing time across all steps
            total_cost_usd: Total estimated cost in USD
            error_message: Error details if status is "failed"
        """
        if status not in ['success', 'failed']:
            raise ValueError(f"Invalid status: {status}. Must be 'success' or 'failed'")

        now_iso = datetime.utcnow().isoformat() + 'Z'

        update_data = {
            'status': status,
            'updated_at': now_iso
        }

        if songs_extracted is not None:
            update_data['songs_extracted'] = songs_extracted
        if total_duration_sec is not None:
            update_data['total_duration_sec'] = total_duration_sec
        if total_cost_usd is not None:
            update_data['total_cost_usd'] = total_cost_usd
        if error_message:
            update_data['error_message'] = error_message

        try:
            if self.local_mode:
                existing = self.db.get_item(self.table_name, {'book_id': book_id})
                if existing:
                    existing.update(update_data)
                    self.db.put_item(self.table_name, existing)
                else:
                    logger.warning(f"No existing entry found for book {book_id}")
            else:
                update_expr = 'SET ' + ', '.join([f'#{k} = :{k}' for k in update_data.keys()])
                expr_attr_names = {f'#{k}': k for k in update_data.keys()}
                expr_attr_values = {f':{k}': v for k, v in update_data.items()}

                self.table.update_item(
                    Key={'book_id': book_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_attr_names,
                    ExpressionAttributeValues=expr_attr_values
                )

            logger.info(f"Recorded processing completion for book {book_id} with status {status}")

        except ClientError as e:
            logger.error(f"Error recording processing completion: {e}")
            raise

    def update_step(self, book_id: str, step_name: str, step_data: Dict[str, Any],
                    current_step: Optional[str] = None) -> None:
        """
        Update per-step tracking data in the ledger.

        Args:
            book_id: Unique identifier for the book
            step_name: Step name (e.g. 'toc_discovery', 'toc_parse')
            step_data: Step data dict (status, started_at, completed_at, etc.)
            current_step: Optionally update current_step field
        """
        now_iso = datetime.utcnow().isoformat() + 'Z'

        try:
            if self.local_mode:
                existing = self.db.get_item(self.table_name, {'book_id': book_id})
                if existing:
                    if 'steps' not in existing:
                        existing['steps'] = {}
                    existing['steps'][step_name] = step_data
                    existing['updated_at'] = now_iso
                    if current_step:
                        existing['current_step'] = current_step
                    self.db.put_item(self.table_name, existing)
            else:
                update_expr = 'SET steps.#step = :step_data, updated_at = :now'
                expr_attr_names = {'#step': step_name}
                expr_attr_values = {':step_data': step_data, ':now': now_iso}

                if current_step:
                    update_expr += ', current_step = :current_step'
                    expr_attr_values[':current_step'] = current_step

                self.table.update_item(
                    Key={'book_id': book_id},
                    UpdateExpression=update_expr,
                    ExpressionAttributeNames=expr_attr_names,
                    ExpressionAttributeValues=expr_attr_values
                )

            logger.info(f"Updated step {step_name} for book {book_id}")

        except ClientError as e:
            logger.error(f"Error updating step {step_name}: {e}")
            raise
    
    def get_entry(self, book_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a ledger entry by book_id.
        
        Args:
            book_id: Unique identifier for the book
        
        Returns:
            Ledger entry dict or None if not found
        """
        try:
            if self.local_mode:
                return self.db.get_item(self.table_name, {'book_id': book_id})
            else:
                response = self.table.get_item(Key={'book_id': book_id})
                return response.get('Item')
                
        except ClientError as e:
            logger.error(f"Error retrieving ledger entry: {e}")
            return None
    
    def query_by_status(self, status: str) -> list:
        """
        Query ledger entries by status.
        
        Args:
            status: Status to filter by
        
        Returns:
            List of ledger entries
        """
        try:
            if self.local_mode:
                return self.db.query(self.table_name, '', filter_status=status)
            else:
                # Note: This requires a GSI on status in the real table
                response = self.table.query(
                    IndexName='status-index',
                    KeyConditionExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status}
                )
                return response.get('Items', [])
                
        except ClientError as e:
            logger.error(f"Error querying by status: {e}")
            return []
