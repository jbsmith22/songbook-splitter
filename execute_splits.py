#!/usr/bin/env python3
"""
Execute PDF splits based on saved split instructions from the review interface.
"""

import json
import shutil
from pathlib import Path
import PyPDF2

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def split_pdf(source_pdf: Path, output_dir: Path, song_title: str, page_range: str, artist: str):
    """Split a PDF into a new file with the specified page range."""
    
    # Parse page range (e.g., "1-3" or "4")
    if '-' in page_range:
        start, end = page_range.split('-')
        start_page = int(start) - 1  # 0-indexed
        end_page = int(end)
    else:
        start_page = int(page_range) - 1
        end_page = int(page_range)
    
    # Create output filename
    output_filename = f"{artist} - {song_title}.pdf"
    output_path = output_dir / output_filename
    
    # Read source PDF
    with open(source_pdf, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        writer = PyPDF2.PdfWriter()
        
        # Add specified pages
        for page_num in range(start_page, end_page):
            if page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])
        
        # Write output PDF
        with open(output_path, 'wb') as out_f:
            writer.write(out_f)
    
    return output_path


def execute_splits(feedback_file: Path, results_file: Path = None, dry_run: bool = True):
    """Execute splits based on feedback file."""
    
    with open(feedback_file, 'r') as f:
        data = json.load(f)
    
    split_instructions = data.get('splitInstructions', {})
    
    if not split_instructions:
        print("No split instructions found in feedback file.")
        return
    
    print(f"Found split instructions for {len(split_instructions)} PDFs")
    print("=" * 80)
    
    # Load results to get PDF paths
    if results_file is None:
        # Try filtered results first, then fall back to regular results
        if Path("verification_results/batch1_results_filtered.json").exists():
            results_file = Path("verification_results/batch1_results_filtered.json")
        else:
            results_file = Path("verification_results/bedrock_results.json")
    
    print(f"Using results file: {results_file}")
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    flagged = [r for r in results if not r['passed']]
    
    for idx_str, songs in split_instructions.items():
        idx = int(idx_str)
        
        if idx >= len(flagged):
            print(f"Warning: Index {idx} out of range, skipping")
            continue
        
        result = flagged[idx]
        source_pdf = Path(result['pdf_path'])
        
        if not source_pdf.exists():
            print(f"✗ Source PDF not found: {source_pdf}")
            continue
        
        # Get artist and book from path
        rel_path = source_pdf.relative_to(PROCESSED_SONGS_PATH)
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "Unknown"
        
        output_dir = source_pdf.parent
        
        print(f"\n📄 {source_pdf.name}")
        print(f"   Artist: {artist}")
        print(f"   Book: {book}")
        print(f"   Splitting into {len(songs)} songs:")
        
        for i, song in enumerate(songs, 1):
            title = song['title']
            pages = song['pages']
            output_filename = f"{artist} - {title}.pdf"
            
            print(f"   {i}. {title} (pages {pages}) → {output_filename}")
            
            if not dry_run:
                try:
                    output_path = split_pdf(source_pdf, output_dir, title, pages, artist)
                    print(f"      ✓ Created: {output_path}")
                except Exception as e:
                    print(f"      ✗ Error: {e}")
        
        if not dry_run:
            # Optionally delete or rename original
            backup_path = source_pdf.with_suffix('.pdf.original')
            shutil.move(source_pdf, backup_path)
            print(f"   ✓ Original backed up to: {backup_path.name}")
    
    print("\n" + "=" * 80)
    if dry_run:
        print("DRY RUN - No files were modified")
        print("Run with --execute to actually perform the splits")
    else:
        print("COMPLETE - All splits executed")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: py execute_splits.py <feedback_json_file> [--results <results_file>] [--execute]")
        print("\nExample:")
        print("  py execute_splits.py review_feedback_2026-01-29.json")
        print("  py execute_splits.py review_feedback_2026-01-29.json --execute")
        print("  py execute_splits.py review_feedback_2026-01-29.json --results verification_results/batch1_results_filtered.json --execute")
        print("\nWithout --execute, runs in dry-run mode (shows what would happen)")
        sys.exit(1)
    
    feedback_file = Path(sys.argv[1])
    if not feedback_file.exists():
        print(f"Error: {feedback_file} not found")
        sys.exit(1)
    
    # Parse optional results file
    results_file = None
    if '--results' in sys.argv:
        idx = sys.argv.index('--results')
        if idx + 1 < len(sys.argv):
            results_file = Path(sys.argv[idx + 1])
            if not results_file.exists():
                print(f"Error: {results_file} not found")
                sys.exit(1)
    
    dry_run = '--execute' not in sys.argv
    
    if dry_run:
        print("=" * 80)
        print("DRY RUN MODE - No files will be modified")
        print("=" * 80)
    else:
        print("=" * 80)
        print("EXECUTE MODE - Files will be split and originals backed up")
        print("=" * 80)
    
    execute_splits(feedback_file, results_file, dry_run=dry_run)
