"""
Analyze current DynamoDB ledger to understand what's recorded.

This script helps you understand:
- What paths are stored in DynamoDB
- What the book_ids map to
- Status breakdown
"""

import boto3
import hashlib
import json
from collections import Counter
from typing import List, Dict
import csv

DYNAMODB_TABLE = 'jsmith-processing-ledger'


def generate_book_id(s3_uri: str) -> str:
    """Generate book_id from S3 URI (same as pipeline)."""
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def analyze_ledger():
    """Analyze current DynamoDB ledger."""
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(DYNAMODB_TABLE)
    
    print("Fetching all DynamoDB entries...")
    
    entries = []
    response = table.scan()
    entries.extend(response.get('Items', []))
    
    # Handle pagination
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        entries.extend(response.get('Items', []))
    
    print(f"\nTotal entries: {len(entries)}")
    
    # Status breakdown
    statuses = Counter(entry.get('status', 'unknown') for entry in entries)
    print("\nStatus breakdown:")
    for status, count in statuses.most_common():
        print(f"  {status}: {count}")
    
    # Analyze paths
    print("\nPath analysis:")
    artists = Counter(entry.get('artist', 'unknown') for entry in entries)
    print(f"  Unique artists: {len(artists)}")
    
    # Show sample entries
    print("\nSample entries (first 5):")
    for i, entry in enumerate(entries[:5], 1):
        print(f"\n  Entry {i}:")
        print(f"    book_id: {entry.get('book_id', 'N/A')}")
        print(f"    source_pdf_uri: {entry.get('source_pdf_uri', 'N/A')}")
        print(f"    artist: {entry.get('artist', 'N/A')}")
        print(f"    book_name: {entry.get('book_name', 'N/A')}")
        print(f"    status: {entry.get('status', 'N/A')}")
        print(f"    songs_extracted: {entry.get('songs_extracted', 'N/A')}")
    
    # Export to CSV for easier review
    csv_file = 'dynamodb_ledger_analysis.csv'
    print(f"\nExporting to {csv_file}...")
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        if entries:
            # Select key fields
            fieldnames = ['book_id', 'status', 'artist', 'book_name', 'source_pdf_uri', 
                         'songs_extracted', 'manifest_uri', 'error_message']
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(entries)
    
    print(f"Analysis complete. Review {csv_file} for full details.")
    
    return entries


def verify_book_id_generation():
    """Verify how book_ids are generated with examples."""
    print("\n" + "=" * 80)
    print("Book ID Generation Examples")
    print("=" * 80)
    
    examples = [
        "s3://jsmith-input/SheetMusic/Billy Joel/books/Billy Joel - 52nd Street.pdf",
        "s3://jsmith-input/SheetMusic/Billy_Joel/books/52nd_Street.pdf",
        "s3://jsmith-input/SheetMusic/Beatles/books/Abbey Road.pdf",
    ]
    
    for uri in examples:
        book_id = generate_book_id(uri)
        print(f"\nURI: {uri}")
        print(f"book_id: {book_id}")
    
    print("\nNote: Even small changes in the URI produce completely different book_ids!")


def find_entry_by_artist_book(artist: str, book_name: str, entries: List[Dict]) -> List[Dict]:
    """Find DynamoDB entries matching artist and book name."""
    matches = []
    for entry in entries:
        if entry.get('artist') == artist and entry.get('book_name') == book_name:
            matches.append(entry)
    return matches


def interactive_lookup(entries: List[Dict]):
    """Interactive lookup of entries."""
    print("\n" + "=" * 80)
    print("Interactive Lookup")
    print("=" * 80)
    
    while True:
        print("\nOptions:")
        print("  1. Look up by artist and book name")
        print("  2. Look up by book_id")
        print("  3. Show all failed entries")
        print("  4. Show all processing entries")
        print("  5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            artist = input("Enter artist name: ").strip()
            book_name = input("Enter book name: ").strip()
            matches = find_entry_by_artist_book(artist, book_name, entries)
            
            if matches:
                print(f"\nFound {len(matches)} match(es):")
                for match in matches:
                    print(json.dumps(match, indent=2, default=str))
            else:
                print("\nNo matches found.")
        
        elif choice == '2':
            book_id = input("Enter book_id: ").strip()
            matches = [e for e in entries if e.get('book_id') == book_id]
            
            if matches:
                print(f"\nFound entry:")
                print(json.dumps(matches[0], indent=2, default=str))
            else:
                print("\nNo match found.")
        
        elif choice == '3':
            failed = [e for e in entries if e.get('status') == 'failed']
            print(f"\nFound {len(failed)} failed entries:")
            for entry in failed:
                print(f"  - {entry.get('artist')} / {entry.get('book_name')}")
                if entry.get('error_message'):
                    print(f"    Error: {entry.get('error_message')}")
        
        elif choice == '4':
            processing = [e for e in entries if e.get('status') == 'processing']
            print(f"\nFound {len(processing)} processing entries:")
            for entry in processing:
                print(f"  - {entry.get('artist')} / {entry.get('book_name')}")
        
        elif choice == '5':
            break
        
        else:
            print("Invalid choice.")


def main():
    """Main execution."""
    print("=" * 80)
    print("DynamoDB Ledger Analysis")
    print("=" * 80)
    
    # Analyze ledger
    entries = analyze_ledger()
    
    # Show book_id generation examples
    verify_book_id_generation()
    
    # Interactive lookup
    interactive_lookup(entries)


if __name__ == '__main__':
    main()
