#!/usr/bin/env python3
"""
Rename files in S3 with special characters to sanitized names, then download them.
Uses boto3 which handles Unicode properly.
"""

import boto3
import csv
import os
import sys
from pathlib import Path
from datetime import datetime

def sanitize_filename(filename):
    """Replace special characters with ASCII equivalents."""
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'á': 'a', 'à': 'a', 'â': 'a', 'ä': 'a',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'ö': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ü': 'u',
        'ñ': 'n', 'ç': 'c', 'ï': 'i', 'í': 'i',
        '?': 'e'  # Question marks are often placeholders
    }
    
    result = filename
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    return result

def main():
    csv_file = "missing-files-fresh-20260127-113716.csv"
    bucket_name = "jsmith-output"
    
    log_file = f"rename-s3-boto3-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"
    
    def log(message, color=None):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    log("=== Rename in S3 and Download (boto3) ===")
    log(f"CSV File: {csv_file}")
    log(f"Bucket: {bucket_name}")
    log("")
    
    # Initialize boto3 client
    try:
        s3 = boto3.client('s3')
        log("boto3 S3 client initialized")
    except Exception as e:
        log(f"ERROR: Failed to initialize boto3: {e}")
        return 1
    
    # Read CSV
    if not os.path.exists(csv_file):
        log(f"ERROR: CSV file not found: {csv_file}")
        return 1
    
    files_to_process = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        files_to_process = list(reader)
    
    log(f"Found {len(files_to_process)} files to process")
    log("")
    
    renamed = 0
    downloaded = 0
    errors = 0
    
    for file_info in files_to_process:
        try:
            s3_key = file_info['S3Key']
            expected_local_path = file_info['ExpectedLocalPath']
            
            # Sanitize both S3 key and local path
            sanitized_s3_key = sanitize_filename(s3_key)
            sanitized_local_path = sanitize_filename(expected_local_path)
            
            log(f"Processing: {s3_key}")
            
            # Step 1: Copy to new sanitized name in S3
            log(f"  Copying in S3: {s3_key} -> {sanitized_s3_key}")
            try:
                s3.copy_object(
                    Bucket=bucket_name,
                    CopySource={'Bucket': bucket_name, 'Key': s3_key},
                    Key=sanitized_s3_key
                )
                log(f"  SUCCESS: Copied in S3")
            except Exception as e:
                log(f"  ERROR: Failed to copy in S3: {e}")
                errors += 1
                continue
            
            # Step 2: Delete old file in S3
            log(f"  Deleting old S3 file: {s3_key}")
            try:
                s3.delete_object(Bucket=bucket_name, Key=s3_key)
                log(f"  SUCCESS: Deleted old file")
                renamed += 1
            except Exception as e:
                log(f"  WARNING: Failed to delete old file: {e}")
            
            # Step 3: Download the sanitized file
            local_dir = os.path.dirname(sanitized_local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            log(f"  Downloading: {sanitized_s3_key}")
            try:
                s3.download_file(bucket_name, sanitized_s3_key, sanitized_local_path)
                log(f"  SUCCESS: Downloaded to {sanitized_local_path}")
                downloaded += 1
            except Exception as e:
                log(f"  ERROR: Failed to download: {e}")
                errors += 1
            
            if downloaded % 10 == 0 and downloaded > 0:
                log("")
                log(f"Progress: {renamed} renamed, {downloaded} downloaded, {errors} errors")
                log("")
        
        except Exception as e:
            log(f"ERROR processing {file_info.get('S3Key', 'unknown')}: {e}")
            errors += 1
    
    log("")
    log("=== Process Complete ===")
    log(f"Files renamed in S3: {renamed}")
    log(f"Files downloaded: {downloaded}")
    log(f"Errors: {errors}")
    log("")
    
    if downloaded > 0:
        log(f"Successfully processed {downloaded} files!")
    
    log(f"Log file: {log_file}")
    
    return 0 if errors == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
