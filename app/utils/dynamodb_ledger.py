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
    """Represents a processing ledger entry."""
    book_id: str
    processing_timestamp: int
    status: str  # "processing", "success", "failed", "manual_review"
    source_pdf_uri: str
    artist: str
    book_name: str
    step_function_execution_arn: Optional[str] = None
    error_message: Optional[str] = None
    manifest_uri: Optional[str] = None
    songs_extracted: Optional[int] = None
    processing_duration_seconds: Optional[float] = None
    cost_usd: Optional[float] = None
    ttl: Optional[int] = None


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
    
    def __init__(self, table_name: str = 'sheetmusic-processing-ledger', 
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
        timestamp = int(time.time())
        
        entry = LedgerEntry(
            book_id=book_id,
            processing_timestamp=timestamp,
            status='processing',
            source_pdf_uri=source_pdf_uri,
            artist=artist,
            book_name=book_name,
            step_function_execution_arn=execution_arn
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
                                   manifest_uri: Optional[str] = None,
                                   songs_extracted: Optional[int] = None,
                                   processing_duration_seconds: Optional[float] = None,
                                   cost_usd: Optional[float] = None,
                                   error_message: Optional[str] = None) -> None:
        """
        Record the completion of processing for a book.
        
        Args:
            book_id: Unique identifier for the book
            status: Final status ("success", "failed", "manual_review")
            manifest_uri: S3 URI of the manifest file
            songs_extracted: Number of songs successfully extracted
            processing_duration_seconds: Total processing time
            cost_usd: Estimated cost in USD
            error_message: Error details if status is "failed"
        """
        if status not in ['success', 'failed', 'manual_review']:
            raise ValueError(f"Invalid status: {status}. Must be 'success', 'failed', or 'manual_review'")
        
        timestamp = int(time.time())
        
        update_data = {
            'status': status,
            'processing_timestamp': timestamp
        }
        
        if manifest_uri:
            update_data['manifest_uri'] = manifest_uri
        if songs_extracted is not None:
            update_data['songs_extracted'] = songs_extracted
        if processing_duration_seconds is not None:
            update_data['processing_duration_seconds'] = processing_duration_seconds
        if cost_usd is not None:
            update_data['cost_usd'] = cost_usd
        if error_message:
            update_data['error_message'] = error_message
        
        try:
            if self.local_mode:
                # Get existing item and update it
                existing = self.db.get_item(self.table_name, {'book_id': book_id})
                if existing:
                    existing.update(update_data)
                    self.db.put_item(self.table_name, existing)
                else:
                    logger.warning(f"No existing entry found for book {book_id}")
            else:
                # Build update expression
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
