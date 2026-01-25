"""
S3 utility module with local mode support for PDF discovery and file operations.

This module provides functions for:
- Listing PDFs from S3 or local filesystem
- Pattern matching for PDF discovery
- S3 pagination handling
- Local mode support for development
"""

import os
import re
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)


@dataclass
class S3Object:
    """Represents an S3 object or local file."""
    bucket: str
    key: str
    artist: str
    book_name: str
    size: int = 0
    last_modified: Optional[str] = None


class S3Utils:
    """Utility class for S3 operations with local mode support."""
    
    def __init__(self, local_mode: bool = False, local_base_path: Optional[str] = None):
        """
        Initialize S3 utilities.
        
        Args:
            local_mode: If True, use local filesystem instead of S3
            local_base_path: Base path for local mode (default: ./test_data/input/)
        """
        self.local_mode = local_mode
        self.local_base_path = local_base_path or './test_data/input/'
        
        if not local_mode:
            self.s3_client = boto3.client('s3')
        else:
            logger.info(f"S3Utils initialized in local mode with base path: {self.local_base_path}")
    
    def list_pdfs(self, bucket: str, prefix: str = 'SheetMusic/', pattern: Optional[str] = None) -> List[S3Object]:
        """
        List all PDF files matching the pattern.
        
        Args:
            bucket: S3 bucket name (ignored in local mode)
            prefix: S3 prefix to search (default: 'SheetMusic/')
            pattern: Optional regex pattern to match (default: SheetMusic/<Artist>/books/*.pdf)
        
        Returns:
            List of S3Object instances
        """
        if pattern is None:
            pattern = r'SheetMusic/([^/]+)/books/(.+\.pdf)$'
        
        if self.local_mode:
            return self._list_pdfs_local(prefix, pattern)
        else:
            return self._list_pdfs_s3(bucket, prefix, pattern)
    
    def _list_pdfs_s3(self, bucket: str, prefix: str, pattern: str) -> List[S3Object]:
        """List PDFs from S3 with pagination support."""
        pdfs = []
        pattern_re = re.compile(pattern)
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)
            
            for page in page_iterator:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    key = obj['Key']
                    
                    # Check if key matches pattern
                    match = pattern_re.search(key)
                    if match and key.lower().endswith('.pdf'):
                        artist = match.group(1)
                        book_path = match.group(2)
                        book_name = Path(book_path).stem
                        
                        pdfs.append(S3Object(
                            bucket=bucket,
                            key=key,
                            artist=artist,
                            book_name=book_name,
                            size=obj.get('Size', 0),
                            last_modified=obj.get('LastModified', '').isoformat() if obj.get('LastModified') else None
                        ))
            
            logger.info(f"Found {len(pdfs)} PDFs in s3://{bucket}/{prefix}")
            return pdfs
            
        except ClientError as e:
            logger.error(f"Error listing S3 objects: {e}")
            raise
    
    def _list_pdfs_local(self, prefix: str, pattern: str) -> List[S3Object]:
        """List PDFs from local filesystem."""
        pdfs = []
        pattern_re = re.compile(pattern)
        
        base_path = Path(self.local_base_path)
        if not base_path.exists():
            logger.warning(f"Local base path does not exist: {base_path}")
            return pdfs
        
        # Walk through directory structure
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = Path(root) / file
                    relative_path = file_path.relative_to(base_path)
                    key = str(relative_path).replace('\\', '/')
                    
                    # Check if key matches pattern
                    match = pattern_re.search(key)
                    if match:
                        artist = match.group(1)
                        book_path = match.group(2)
                        book_name = Path(book_path).stem
                        
                        pdfs.append(S3Object(
                            bucket='local',
                            key=key,
                            artist=artist,
                            book_name=book_name,
                            size=file_path.stat().st_size,
                            last_modified=None
                        ))
        
        logger.info(f"Found {len(pdfs)} PDFs in local path: {base_path}")
        return pdfs
    
    def download_file(self, bucket: str, key: str, local_path: str) -> str:
        """
        Download file from S3 or copy from local filesystem.
        
        Args:
            bucket: S3 bucket name
            key: S3 key or relative path
            local_path: Destination path
        
        Returns:
            Path to downloaded file
        """
        if self.local_mode:
            source_path = Path(self.local_base_path) / key
            dest_path = Path(local_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source_path, dest_path)
            logger.info(f"Copied file from {source_path} to {dest_path}")
            return str(dest_path)
        else:
            dest_path = Path(local_path)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.s3_client.download_file(bucket, key, str(dest_path))
            logger.info(f"Downloaded s3://{bucket}/{key} to {dest_path}")
            return str(dest_path)
    
    def upload_file(self, local_path: str, bucket: str, key: str) -> str:
        """
        Upload file to S3 or copy to local filesystem.
        
        Args:
            local_path: Source file path
            bucket: S3 bucket name
            key: S3 key or relative path
        
        Returns:
            S3 URI or local path
        """
        if self.local_mode:
            dest_path = Path(self.local_base_path.replace('/input/', '/output/')) / key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(local_path, dest_path)
            logger.info(f"Copied file from {local_path} to {dest_path}")
            return str(dest_path)
        else:
            self.s3_client.upload_file(local_path, bucket, key)
            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Uploaded {local_path} to {s3_uri}")
            return s3_uri
    
    def write_bytes(self, data: bytes, bucket: str, key: str) -> str:
        """
        Write bytes directly to S3 or local filesystem.
        
        Args:
            data: Bytes to write
            bucket: S3 bucket name
            key: S3 key or relative path
        
        Returns:
            S3 URI or local path
        """
        if self.local_mode:
            dest_path = Path(self.local_base_path.replace('/input/', '/output/')) / key
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_bytes(data)
            logger.info(f"Wrote {len(data)} bytes to {dest_path}")
            return str(dest_path)
        else:
            self.s3_client.put_object(Bucket=bucket, Key=key, Body=data)
            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Wrote {len(data)} bytes to {s3_uri}")
            return s3_uri
    
    def read_bytes(self, bucket: str, key: str) -> bytes:
        """
        Read bytes directly from S3 or local filesystem.
        
        Args:
            bucket: S3 bucket name
            key: S3 key or relative path
        
        Returns:
            File contents as bytes
        """
        if self.local_mode:
            source_path = Path(self.local_base_path.replace('/input/', '/output/')) / key
            data = source_path.read_bytes()
            logger.info(f"Read {len(data)} bytes from {source_path}")
            return data
        else:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            data = response['Body'].read()
            logger.info(f"Read {len(data)} bytes from s3://{bucket}/{key}")
            return data
