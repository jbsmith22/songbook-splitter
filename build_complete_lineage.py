#!/usr/bin/env python3
"""
Build complete lineage tracking for all PDFs from original books through splits.
Tracks: Original Book -> Songs -> Verification -> Splits -> Final Files
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def check_if_split_executed(pdf_path):
    """Check if a PDF was actually split by looking for .original backup."""
    backup_path = pdf_path.with_suffix('.pdf.original')
    return backup_path.exists()

def count_split_results(pdf_path, artist):
    """Count how many split files were created from this PDF."""
    # Look for files in the same directory that were created from splits
    # This is approximate - we look for files with the same artist prefix
    # that don't have .original backups
    parent_dir = pdf_path.parent
    
    if not parent_dir.exists():
        return []
    
    split_files = []
    for file in parent_dir.glob(f"{artist} - *.pdf"):
        # Skip if it has a backup (meaning it was an original that got split)
        if file.with_suffix('.pdf.original').exists():
            continue
        # Skip if it's the original file itself
        if file == pdf_path:
            continue
        split_files.append(file.name)
    
    return split_files

def build_complete_lineage():
    """Build comprehensive lineage from all available data sources."""
    
    lineage = {
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_books': 0,
            'total_original_songs': 0,
            'songs_verified_correct': 0,
            'songs_flagged': 0,
            'songs_split': 0,
            'total_final_songs': 0
        },
        'books': {}
    }
    
    # Load batch 1 results (filtered)
    batch1_results_file = Path("verification_results/batch1_results_filtered.json")
    if batch1_results_file.exists():
        with open(batch1_results_file, 'r') as f:
            batch1_results = json.load(f)
    else:
        batch1_results = []
    
    # Load batch 1 feedback
    feedback_file = Path("review_feedback_2026-01-29.json")
    if feedback_file.exists():
        with open(feedback_file, 'r') as f:
            feedback = json.load(f)
    else:
        feedback = {'reviews': {}, 'splitInstructions': {}, 'correctTypes': {}}
    
    # Build book structure from results
    # Only process flagged PDFs since those are what we reviewed
    flagged_pdfs = [r for r in batch1_results if not r['passed']]
    
    print(f"Processing {len(flagged_pdfs)} flagged PDFs from batch 1...")
    
    for idx, result in enumerate(flagged_pdfs):
        pdf_path = Path(result['pdf_path'])
        
        if not pdf_path.exists() and not pdf_path.with_suffix('.pdf.original').exists():
            continue
        
        # Use .original if the file was split
        if pdf_path.with_suffix('.pdf.original').exists():
            original_path = pdf_path.with_suffix('.pdf.original')
        else:
            original_path = pdf_path
        
        rel_path = original_path.relative_to(PROCESSED_SONGS_PATH)
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "Unknown"
        
        book_key = f"{artist}/{book}"
        
        if book_key not in lineage['books']:
            lineage['books'][book_key] = {
                'artist': artist,
                'book_title': book,
                'songs': []
            }
            lineage['summary']['total_books'] += 1
        
        # Determine song status
        song_entry = {
            'original_filename': original_path.name,
            'original_path': str(original_path),
            'passed_verification': result['passed'],
            'verification_reason': result.get('reason', 'N/A'),
            'review_status': 'not_reviewed',
            'final_disposition': 'unchanged',
            'splits': [],
            'notes': ''
        }
        
        # Check if reviewed (use index in flagged list)
        flagged_idx_str = str(idx)
        
        if flagged_idx_str in feedback['reviews']:
            review = feedback['reviews'][flagged_idx_str]
            song_entry['review_status'] = review
            
            if review == 'correct':
                correct_type = feedback['correctTypes'].get(flagged_idx_str, {})
                song_entry['correct_type'] = correct_type.get('type', 'unknown')
                song_entry['notes'] = correct_type.get('notes', '')
                
                # Check if split
                if flagged_idx_str in feedback['splitInstructions']:
                    # Check if split was actually executed
                    was_split = check_if_split_executed(pdf_path)
                    
                    if was_split:
                        song_entry['final_disposition'] = 'split_executed'
                        splits = feedback['splitInstructions'][flagged_idx_str]
                        
                        for split in splits:
                            split_entry = {
                                'title': split['title'],
                                'pages': split['pages'],
                                'output_filename': f"{artist} - {split['title']}.pdf",
                                'status': 'created'
                            }
                            song_entry['splits'].append(split_entry)
                        
                        lineage['summary']['songs_split'] += 1
                        lineage['summary']['total_final_songs'] += len(splits)
                    else:
                        song_entry['final_disposition'] = 'split_planned'
                        splits = feedback['splitInstructions'][flagged_idx_str]
                        
                        for split in splits:
                            split_entry = {
                                'title': split['title'],
                                'pages': split['pages'],
                                'output_filename': f"{artist} - {split['title']}.pdf",
                                'status': 'planned'
                            }
                            song_entry['splits'].append(split_entry)
                        
                        lineage['summary']['total_final_songs'] += 1  # Still counts as original
                else:
                    song_entry['final_disposition'] = 'confirmed_correct'
                    lineage['summary']['songs_verified_correct'] += 1
                    lineage['summary']['total_final_songs'] += 1
            
            elif review == 'incorrect':
                song_entry['final_disposition'] = 'false_positive'
                feedback_reasons = feedback.get('feedback', {}).get(flagged_idx_str, {})
                song_entry['feedback_reasons'] = feedback_reasons.get('reasons', [])
                song_entry['notes'] = feedback_reasons.get('notes', '')
                lineage['summary']['total_final_songs'] += 1
            
            elif review == 'skip':
                song_entry['final_disposition'] = 'skipped'
                lineage['summary']['total_final_songs'] += 1
        
        else:
            song_entry['review_status'] = 'pending_review'
            lineage['summary']['songs_flagged'] += 1
            lineage['summary']['total_final_songs'] += 1
        
        lineage['books'][book_key]['songs'].append(song_entry)
        lineage['summary']['total_original_songs'] += 1
    
    return lineage

def generate_book_report(lineage, book_key):
    """Generate a detailed report for a single book."""
    
    book = lineage['books'][book_key]
    
    print(f"\n{'=' * 80}")
    print(f"BOOK: {book['book_title']}")
    print(f"Artist: {book['artist']}")
    print(f"{'=' * 80}")
    print(f"Total Songs: {len(book['songs'])}")
    print()
    
    for i, song in enumerate(book['songs'], 1):
        print(f"{i}. {song['original_filename']}")
        print(f"   Status: {song['final_disposition']}")
        
        if song['splits']:
            print(f"   Split into {len(song['splits'])} songs:")
            for j, split in enumerate(song['splits'], 1):
                print(f"      {j}. {split['title']} (pages {split['pages']})")
                print(f"         → {split['output_filename']}")
        
        if song['notes']:
            print(f"   Notes: {song['notes']}")
        
        print()

def save_lineage(lineage, output_file):
    """Save lineage to JSON file."""
    with open(output_file, 'w') as f:
        json.dump(lineage, f, indent=2)

def print_summary(lineage):
    """Print summary statistics."""
    
    summary = lineage['summary']
    
    print("\n" + "=" * 80)
    print("VERIFICATION LINEAGE SUMMARY")
    print("=" * 80)
    print(f"Generated: {lineage['generated_at']}")
    print()
    print(f"Total Books Processed: {summary['total_books']}")
    print(f"Total Original Songs: {summary['total_original_songs']}")
    print()
    print("Disposition:")
    print(f"  ✓ Verified Correct (No Changes): {summary['songs_verified_correct']}")
    print(f"  ✂ Split into Multiple Songs: {summary['songs_split']}")
    print(f"  ⚠ Flagged (Pending Review): {summary['songs_flagged']}")
    print()
    print(f"Total Final Song Files: {summary['total_final_songs']}")
    print(f"Net Change: +{summary['total_final_songs'] - summary['total_original_songs']} songs")
    print("=" * 80)

if __name__ == "__main__":
    import sys
    
    print("Building complete lineage...")
    lineage = build_complete_lineage()
    
    output_file = Path("verification_complete_lineage.json")
    save_lineage(lineage, output_file)
    print(f"✓ Saved to: {output_file}")
    
    print_summary(lineage)
    
    # If book key provided, show detailed report
    if len(sys.argv) > 1:
        book_key = sys.argv[1]
        if book_key in lineage['books']:
            generate_book_report(lineage, book_key)
        else:
            print(f"\nBook '{book_key}' not found.")
            print("\nAvailable books:")
            for key in sorted(lineage['books'].keys()):
                print(f"  - {key}")
