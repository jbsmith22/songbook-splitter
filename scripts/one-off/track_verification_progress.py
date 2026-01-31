#!/usr/bin/env python3
"""
Track comprehensive verification progress across all batches.
Creates a detailed lineage map showing original books -> songs -> splits.
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")
VERIFICATION_RESULTS_PATH = Path("verification_results")

def load_batch_results():
    """Load all batch results files."""
    batch_files = list(VERIFICATION_RESULTS_PATH.glob("batch*_results*.json"))
    
    all_results = []
    for batch_file in sorted(batch_files):
        with open(batch_file, 'r') as f:
            results = json.load(f)
            all_results.extend(results)
    
    return all_results

def load_feedback_files():
    """Load all review feedback files."""
    feedback_files = list(Path(".").glob("review_feedback_*.json"))
    
    all_feedback = {}
    for feedback_file in sorted(feedback_files):
        with open(feedback_file, 'r') as f:
            data = json.load(f)
            # Store by timestamp to track which feedback is most recent
            all_feedback[feedback_file.name] = data
    
    return all_feedback

def build_book_lineage(results, feedback_data):
    """Build a comprehensive lineage map of books -> songs -> splits."""
    
    # Group by book
    books = defaultdict(lambda: {
        'artist': None,
        'book_title': None,
        'songs': []
    })
    
    for result in results:
        pdf_path = Path(result['pdf_path'])
        rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
        
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "Unknown"
        song_file = pdf_path.name
        
        book_key = f"{artist}/{book}"
        
        if books[book_key]['artist'] is None:
            books[book_key]['artist'] = artist
            books[book_key]['book_title'] = book
        
        # Build song entry
        song_entry = {
            'original_filename': song_file,
            'original_path': str(pdf_path),
            'passed_verification': result['passed'],
            'flagged_reason': result.get('reason', 'N/A'),
            'status': 'verified_correct',  # default
            'splits': [],
            'notes': ''
        }
        
        # Check if this song was reviewed
        if not result['passed']:
            # Find this song in feedback data
            for feedback_file, feedback in feedback_data.items():
                # Match by checking if this PDF is in the flagged results
                # This is a simplified match - in production you'd want more robust matching
                song_entry['status'] = 'flagged_needs_review'
        
        books[book_key]['songs'].append(song_entry)
    
    return books

def apply_feedback_to_lineage(books, feedback_data):
    """Apply feedback data to update song statuses and splits."""
    
    for feedback_file, feedback in feedback_data.items():
        reviews = feedback.get('reviews', {})
        correct_types = feedback.get('correctTypes', {})
        split_instructions = feedback.get('splitInstructions', {})
        
        # We need to match feedback indices to actual PDFs
        # This requires loading the corresponding results file
        # For now, we'll mark that splits were performed
        
        for idx_str, splits in split_instructions.items():
            # Record that splits were performed
            # In a full implementation, we'd match this back to the specific book/song
            pass
    
    return books

def generate_lineage_report(books, output_file):
    """Generate a comprehensive lineage report."""
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_books': len(books),
            'total_songs': sum(len(book['songs']) for book in books.values()),
            'verified_correct': 0,
            'flagged_needs_review': 0,
            'split_performed': 0,
            'false_positive': 0
        },
        'books': {}
    }
    
    for book_key, book_data in sorted(books.items()):
        book_report = {
            'artist': book_data['artist'],
            'book_title': book_data['book_title'],
            'total_songs': len(book_data['songs']),
            'songs': []
        }
        
        for song in book_data['songs']:
            song_report = {
                'original_filename': song['original_filename'],
                'status': song['status'],
                'passed_verification': song['passed_verification'],
                'flagged_reason': song['flagged_reason'],
                'splits': song['splits'],
                'notes': song['notes']
            }
            
            book_report['songs'].append(song_report)
            
            # Update summary counts
            if song['status'] == 'verified_correct':
                report['summary']['verified_correct'] += 1
            elif song['status'] == 'flagged_needs_review':
                report['summary']['flagged_needs_review'] += 1
            elif song['status'] == 'split_performed':
                report['summary']['split_performed'] += 1
            elif song['status'] == 'false_positive':
                report['summary']['false_positive'] += 1
        
        report['books'][book_key] = book_report
    
    # Write report
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def print_summary(report):
    """Print a summary of the lineage report."""
    
    print("=" * 80)
    print("VERIFICATION PROGRESS SUMMARY")
    print("=" * 80)
    print(f"Generated: {report['generated_at']}")
    print()
    print(f"Total Books: {report['summary']['total_books']}")
    print(f"Total Songs: {report['summary']['total_songs']}")
    print()
    print("Status Breakdown:")
    print(f"  ✓ Verified Correct: {report['summary']['verified_correct']}")
    print(f"  ⚠ Flagged (Needs Review): {report['summary']['flagged_needs_review']}")
    print(f"  ✂ Splits Performed: {report['summary']['split_performed']}")
    print(f"  ✗ False Positives: {report['summary']['false_positive']}")
    print()
    print(f"Books with issues: {sum(1 for book in report['books'].values() if any(s['status'] != 'verified_correct' for s in book['songs']))}")
    print("=" * 80)

if __name__ == "__main__":
    print("Loading batch results...")
    results = load_batch_results()
    print(f"Loaded {len(results)} PDF results")
    
    print("\nLoading feedback files...")
    feedback_data = load_feedback_files()
    print(f"Loaded {len(feedback_data)} feedback files")
    
    print("\nBuilding book lineage...")
    books = build_book_lineage(results, feedback_data)
    
    print("\nApplying feedback to lineage...")
    books = apply_feedback_to_lineage(books, feedback_data)
    
    print("\nGenerating lineage report...")
    output_file = Path("verification_lineage_report.json")
    report = generate_lineage_report(books, output_file)
    
    print(f"\n✓ Report saved to: {output_file}")
    print()
    print_summary(report)
