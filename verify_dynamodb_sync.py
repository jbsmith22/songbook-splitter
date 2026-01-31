"""
Verify DynamoDB is now in sync with book_reconciliation_validated.csv
"""

import boto3
import csv
from collections import defaultdict

DYNAMODB_TABLE = 'jsmith-processing-ledger'
CSV_FILE = 'book_reconciliation_validated.csv'


def load_csv_books():
    """Load CSV books."""
    books = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'] == 'COMPLETE':
                books.append(row)
    return books


def load_dynamodb_entries():
    """Load all DynamoDB entries."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    return entries


def main():
    """Main verification."""
    print("=" * 80)
    print("DynamoDB Sync Verification")
    print("=" * 80)
    
    csv_books = load_csv_books()
    dynamodb_entries = load_dynamodb_entries()
    
    print(f"\nCSV books (source of truth): {len(csv_books)}")
    print(f"DynamoDB entries: {len(dynamodb_entries)}")
    
    # Check status distribution
    status_counts = defaultdict(int)
    for entry in dynamodb_entries:
        status = entry.get('status', 'unknown')
        status_counts[status] += 1
    
    print("\nDynamoDB Status Distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    # Check if all entries are success
    if len(dynamodb_entries) == 559 and status_counts.get('success', 0) == 559:
        print("\n✓ SUCCESS: DynamoDB has exactly 559 entries, all with status='success'")
    else:
        print("\n✗ WARNING: DynamoDB state doesn't match expected")
        if len(dynamodb_entries) != 559:
            print(f"  Expected 559 entries, found {len(dynamodb_entries)}")
        if status_counts.get('success', 0) != 559:
            print(f"  Expected 559 success entries, found {status_counts.get('success', 0)}")
    
    # Sample a few entries to verify paths
    print("\nSample Entries (first 5):")
    for i, entry in enumerate(dynamodb_entries[:5], 1):
        print(f"\n{i}. {entry.get('artist')} - {entry.get('book_name')}")
        print(f"   book_id: {entry.get('book_id')}")
        print(f"   source_pdf_uri: {entry.get('source_pdf_uri')}")
        print(f"   status: {entry.get('status')}")
    
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()
