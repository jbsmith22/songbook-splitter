"""
Find best matches between CSV books and DynamoDB entries using fuzzy matching.
"""

import boto3
import hashlib
import json
import csv
from typing import Dict, List, Tuple
from difflib import SequenceMatcher

DYNAMODB_TABLE = 'jsmith-processing-ledger'
CSV_FILE = 'book_reconciliation_validated.csv'


def generate_book_id(s3_uri: str) -> str:
    """Generate book_id from S3 URI."""
    return hashlib.sha256(s3_uri.encode()).hexdigest()[:16]


def normalize_for_comparison(text: str) -> str:
    """Normalize text for fuzzy comparison."""
    import re
    # Remove special chars, lowercase, remove extra spaces
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def similarity_score(str1: str, str2: str) -> float:
    """Calculate similarity between two strings (0.0 to 1.0)."""
    norm1 = normalize_for_comparison(str1)
    norm2 = normalize_for_comparison(str2)
    return SequenceMatcher(None, norm1, norm2).ratio()


def load_csv_books() -> List[Dict]:
    """Load CSV books."""
    books = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['Status'] == 'COMPLETE':
                books.append(row)
    return books


def load_dynamodb_entries() -> List[Dict]:
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


def find_best_match(csv_book: Dict, dynamodb_entries: List[Dict]) -> Tuple[Dict, float, str]:
    """
    Find best matching DynamoDB entry for a CSV book.
    
    Returns:
        (best_match_entry, score, match_reason)
    """
    csv_artist = csv_book['Artist']
    csv_book_name = csv_book['BookName']
    csv_source_path = csv_book['SourcePath']
    
    best_match = None
    best_score = 0.0
    match_reason = ""
    
    for db_entry in dynamodb_entries:
        db_artist = db_entry.get('artist', '')
        db_book_name = db_entry.get('book_name', '')
        db_source_uri = db_entry.get('source_pdf_uri', '')
        
        # Extract path from S3 URI for comparison
        db_path = db_source_uri.replace('s3://jsmith-input/SheetMusic/', '').replace('/', '\\')
        
        # Calculate multiple similarity scores
        artist_sim = similarity_score(csv_artist, db_artist)
        book_name_sim = similarity_score(csv_book_name, db_book_name)
        path_sim = similarity_score(csv_source_path, db_path)
        
        # Combined score (weighted)
        combined_score = (
            artist_sim * 0.3 +      # Artist match is important
            book_name_sim * 0.5 +   # Book name is most important
            path_sim * 0.2          # Path similarity helps
        )
        
        if combined_score > best_score:
            best_score = combined_score
            best_match = db_entry
            match_reason = f"artist:{artist_sim:.2f} book:{book_name_sim:.2f} path:{path_sim:.2f}"
    
    return best_match, best_score, match_reason


def analyze_matches():
    """Analyze all CSV books and find their best DynamoDB matches."""
    print("Loading data...")
    csv_books = load_csv_books()
    dynamodb_entries = load_dynamodb_entries()
    
    print(f"CSV books: {len(csv_books)}")
    print(f"DynamoDB entries: {len(dynamodb_entries)}")
    
    print("\nFinding best matches...")
    
    results = []
    
    for i, csv_book in enumerate(csv_books, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(csv_books)}...")
        
        best_match, score, reason = find_best_match(csv_book, dynamodb_entries)
        
        csv_artist = csv_book['Artist']
        csv_book_name = csv_book['BookName']
        csv_source_path = csv_book['SourcePath']
        
        # Generate CSV book_id
        csv_s3_uri = f"s3://jsmith-input/SheetMusic/{csv_source_path.replace(chr(92), '/')}"
        csv_book_id = generate_book_id(csv_s3_uri)
        
        result = {
            'csv_artist': csv_artist,
            'csv_book_name': csv_book_name,
            'csv_source_path': csv_source_path,
            'csv_book_id': csv_book_id,
            'csv_s3_uri': csv_s3_uri,
            'match_score': f"{score:.3f}",
            'match_reason': reason,
            'db_book_id': best_match['book_id'] if best_match else '',
            'db_artist': best_match.get('artist', '') if best_match else '',
            'db_book_name': best_match.get('book_name', '') if best_match else '',
            'db_source_uri': best_match.get('source_pdf_uri', '') if best_match else '',
            'db_status': best_match.get('status', '') if best_match else '',
            'book_id_match': 'YES' if best_match and csv_book_id == best_match['book_id'] else 'NO'
        }
        
        results.append(result)
    
    # Save results
    output_file = 'best_matches_analysis.csv'
    print(f"\nSaving results to {output_file}...")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # Print statistics
    print("\n" + "=" * 80)
    print("MATCH STATISTICS")
    print("=" * 80)
    
    score_ranges = {
        'perfect (1.00)': 0,
        'excellent (0.90-0.99)': 0,
        'good (0.80-0.89)': 0,
        'fair (0.70-0.79)': 0,
        'poor (0.60-0.69)': 0,
        'very poor (<0.60)': 0
    }
    
    for result in results:
        score = float(result['match_score'])
        if score == 1.0:
            score_ranges['perfect (1.00)'] += 1
        elif score >= 0.90:
            score_ranges['excellent (0.90-0.99)'] += 1
        elif score >= 0.80:
            score_ranges['good (0.80-0.89)'] += 1
        elif score >= 0.70:
            score_ranges['fair (0.70-0.79)'] += 1
        elif score >= 0.60:
            score_ranges['poor (0.60-0.69)'] += 1
        else:
            score_ranges['very poor (<0.60)'] += 1
    
    for range_name, count in score_ranges.items():
        print(f"  {range_name}: {count}")
    
    # Show examples of poor matches
    print("\n" + "=" * 80)
    print("EXAMPLES OF POOR MATCHES (score < 0.80)")
    print("=" * 80)
    
    poor_matches = [r for r in results if float(r['match_score']) < 0.80]
    for result in poor_matches[:10]:  # Show first 10
        print(f"\nCSV: {result['csv_artist']} / {result['csv_book_name']}")
        print(f"  Score: {result['match_score']} ({result['match_reason']})")
        print(f"  Best DB match: {result['db_artist']} / {result['db_book_name']}")
        print(f"  CSV path: {result['csv_source_path']}")
        print(f"  DB URI: {result['db_source_uri']}")
    
    if len(poor_matches) > 10:
        print(f"\n... and {len(poor_matches) - 10} more poor matches")
    
    print("\n" + "=" * 80)
    print(f"Results saved to {output_file}")
    print("Review the CSV to see all matches and their scores")
    print("=" * 80)


if __name__ == '__main__':
    analyze_matches()
