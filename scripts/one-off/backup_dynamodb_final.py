"""
Create final backup of DynamoDB after successful sync.
"""

import boto3
import json
from datetime import datetime

DYNAMODB_TABLE = 'jsmith-processing-ledger'


def backup_dynamodb():
    """Create backup of DynamoDB table."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print(f"Backing up DynamoDB table: {DYNAMODB_TABLE}")
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'dynamodb_backup_final_{timestamp}.json'
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, default=str)
    
    print(f"Backup saved: {filename}")
    print(f"Total entries: {len(entries)}")
    
    return filename


if __name__ == '__main__':
    backup_dynamodb()
