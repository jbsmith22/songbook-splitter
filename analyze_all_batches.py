#!/usr/bin/env python3
"""
Analyze all batch feedback files and generate comprehensive reports.
"""

import json
from pathlib import Path
from collections import defaultdict

def load_batch_feedback(batch_num):
    """Load feedback from a batch export file."""
    # Try multiple possible filenames
    possible_files = [
        Path(f"review_feedback_batch{batch_num}.json"),
        Path(f"batch{batch_num}_feedback.json"),
        Path(f"review_feedback_2026-01-29.json"),  # Today's date
    ]
    
    for filepath in possible_files:
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    
    return None

def load_batch_results(batch_num):
    """Load verification results for a batch."""
    results_file = Path(f"verification_results/batch{batch_num}_results.json")
    if results_file.exists():
        with open(results_file, 'r') as f:
            return json.load(f)
    return None

def analyze_all_batches(num_batches=8):
    """Analyze all batch feedback and generate reports."""
    
    # Categories
    all_correct = []  # PDFs that passed verification
    missed_splits_fixed = []  # Missed splits with corrections
    multi_song_page = []  # Multiple songs on same page
    other_issues = defaultdict(list)  # Other error types
    false_positives = []  # Incorrectly flagged
    unreviewed = []  # Flagged but not reviewed
    
    total_pdfs = 0
    total_flagged = 0
    total_reviewed = 0
    
    print("Analyzing all batches...")
    print("=" * 80)
    
    for batch_num in range(1, num_batches + 1):
        print(f"\nBatch {batch_num}:")
        
        # Load results
        results = load_batch_results(batch_num)
        if not results:
            print(f"  ⚠️  No results file found")
            continue
        
        # Load feedback (optional - may not exist yet)
        feedback = load_batch_feedback(batch_num)
        
        flagged_pdfs = [r for r in results if not r['passed']]
        passed_pdfs = [r for r in results if r['passed']]
        
        total_pdfs += len(results)
        total_flagged += len(flagged_pdfs)
        
        print(f"  Total PDFs: {len(results)}")
        print(f"  Passed: {len(passed_pdfs)}")
        print(f"  Flagged: {len(flagged_pdfs)}")
        
        # Add passed PDFs to "all correct"
        for pdf in passed_pdfs:
            all_correct.append({
                'batch': batch_num,
                'path': pdf['pdf_path'],
                'name': pdf['pdf_name']
            })
        
        if feedback:
            reviews = feedback.get('reviews', {})
            correct_types = feedback.get('correctTypes', {})
            split_instructions = feedback.get('splitInstructions', {})
            
            total_reviewed += len(reviews)
            print(f"  Reviewed: {len(reviews)}")
            
            # Process each flagged PDF
            for idx, pdf in enumerate(flagged_pdfs):
                idx_str = str(idx)
                
                if idx_str not in reviews:
                    # Not reviewed yet
                    unreviewed.append({
                        'batch': batch_num,
                        'path': pdf['pdf_path'],
                        'name': pdf['pdf_name'],
                        'issues': pdf['issues']
                    })
                    continue
                
                review_status = reviews[idx_str]
                
                if review_status == 'incorrect':
                    # False positive
                    false_positives.append({
                        'batch': batch_num,
                        'path': pdf['pdf_path'],
                        'name': pdf['pdf_name'],
                        'issues': pdf['issues']
                    })
                
                elif review_status == 'correct':
                    # Real issue - categorize by type
                    if idx_str in correct_types:
                        error_type = correct_types[idx_str].get('type', 'unknown')
                        notes = correct_types[idx_str].get('notes', '')
                        
                        entry = {
                            'batch': batch_num,
                            'path': pdf['pdf_path'],
                            'name': pdf['pdf_name'],
                            'issues': pdf['issues'],
                            'notes': notes
                        }
                        
                        if error_type == 'missed-split':
                            # Check if split instructions exist
                            if idx_str in split_instructions:
                                entry['split_instructions'] = split_instructions[idx_str]
                                entry['fixed'] = True
                            else:
                                entry['fixed'] = False
                            missed_splits_fixed.append(entry)
                        
                        elif error_type == 'multi-song-page':
                            if idx_str in split_instructions:
                                entry['split_instructions'] = split_instructions[idx_str]
                                entry['fixed'] = True
                            else:
                                entry['fixed'] = False
                            multi_song_page.append(entry)
                        
                        else:
                            other_issues[error_type].append(entry)
        else:
            print(f"  ⚠️  No feedback file found - all flagged PDFs marked as unreviewed")
            for pdf in flagged_pdfs:
                unreviewed.append({
                    'batch': batch_num,
                    'path': pdf['pdf_path'],
                    'name': pdf['pdf_name'],
                    'issues': pdf['issues']
                })
    
    # Generate reports
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total PDFs processed: {total_pdfs}")
    print(f"Total flagged: {total_flagged} ({total_flagged/total_pdfs*100:.1f}%)")
    print(f"Total reviewed: {total_reviewed}")
    print(f"Passed verification: {len(all_correct)}")
    print(f"False positives: {len(false_positives)}")
    print(f"Missed splits: {len(missed_splits_fixed)} ({sum(1 for x in missed_splits_fixed if x.get('fixed')) } fixed)")
    print(f"Multi-song pages: {len(multi_song_page)} ({sum(1 for x in multi_song_page if x.get('fixed'))} fixed)")
    print(f"Unreviewed: {len(unreviewed)}")
    print()
    print("Other issues:")
    for error_type, items in other_issues.items():
        print(f"  {error_type}: {len(items)}")
    
    # Write detailed reports
    reports_dir = Path("verification_reports")
    reports_dir.mkdir(exist_ok=True)
    
    # 1. All correct files
    with open(reports_dir / "01_passed_verification.json", 'w') as f:
        json.dump(all_correct, f, indent=2)
    print(f"\n✓ Wrote: verification_reports/01_passed_verification.json ({len(all_correct)} files)")
    
    # 2. Missed splits (with corrections)
    with open(reports_dir / "02_missed_splits.json", 'w') as f:
        json.dump(missed_splits_fixed, f, indent=2)
    print(f"✓ Wrote: verification_reports/02_missed_splits.json ({len(missed_splits_fixed)} files)")
    
    # 3. Multi-song pages
    with open(reports_dir / "03_multi_song_pages.json", 'w') as f:
        json.dump(multi_song_page, f, indent=2)
    print(f"✓ Wrote: verification_reports/03_multi_song_pages.json ({len(multi_song_page)} files)")
    
    # 4. Other issues (by type)
    for error_type, items in other_issues.items():
        safe_name = error_type.replace('-', '_').replace(' ', '_')
        with open(reports_dir / f"04_{safe_name}.json", 'w') as f:
            json.dump(items, f, indent=2)
        print(f"✓ Wrote: verification_reports/04_{safe_name}.json ({len(items)} files)")
    
    # 5. False positives
    with open(reports_dir / "05_false_positives.json", 'w') as f:
        json.dump(false_positives, f, indent=2)
    print(f"✓ Wrote: verification_reports/05_false_positives.json ({len(false_positives)} files)")
    
    # 6. Unreviewed
    with open(reports_dir / "06_unreviewed.json", 'w') as f:
        json.dump(unreviewed, f, indent=2)
    print(f"✓ Wrote: verification_reports/06_unreviewed.json ({len(unreviewed)} files)")
    
    # Generate CSV summaries
    print("\nGenerating CSV summaries...")
    
    # Missed splits CSV
    with open(reports_dir / "missed_splits_summary.csv", 'w') as f:
        f.write("Batch,Original Path,Fixed,New Songs\n")
        for item in missed_splits_fixed:
            fixed = "Yes" if item.get('fixed') else "No"
            new_songs = ""
            if 'split_instructions' in item:
                songs = [s['title'] for s in item['split_instructions']]
                new_songs = "; ".join(songs)
            f.write(f"{item['batch']},\"{item['path']}\",{fixed},\"{new_songs}\"\n")
    print(f"✓ Wrote: verification_reports/missed_splits_summary.csv")
    
    # Multi-song pages CSV
    with open(reports_dir / "multi_song_pages_summary.csv", 'w') as f:
        f.write("Batch,Original Path,Fixed,Songs\n")
        for item in multi_song_page:
            fixed = "Yes" if item.get('fixed') else "No"
            songs = ""
            if 'split_instructions' in item:
                song_list = [s['title'] for s in item['split_instructions']]
                songs = "; ".join(song_list)
            f.write(f"{item['batch']},\"{item['path']}\",{fixed},\"{songs}\"\n")
    print(f"✓ Wrote: verification_reports/multi_song_pages_summary.csv")
    
    print("\n" + "=" * 80)
    print("Reports complete! Check the verification_reports/ directory")
    print("=" * 80)

if __name__ == "__main__":
    analyze_all_batches()
