"""
Reprocess a single songbook through the pipeline

Usage:
    py reprocess_book.py <book_id>
    py reprocess_book.py --from-file incomplete_books.txt
"""
import sys
import json
import boto3
from pathlib import Path

def reprocess_book(book_id, source_pdf_path=None):
    """
    Reprocess a book through the pipeline

    This would trigger your processing pipeline with the source PDF.
    You'll need to implement the actual pipeline trigger based on your setup.
    """
    print(f'='*80)
    print(f'REPROCESSING: {book_id}')
    print(f'='*80)

    # Load book info from database
    with open('data/analysis/complete_provenance_database.json', 'r') as f:
        data = json.load(f)

    book = None
    for b in data['songbooks']:
        if b['mapping']['book_id'] == book_id:
            book = b
            break

    if not book:
        print(f'ERROR: Book ID {book_id} not found in database')
        return False

    print(f'Book: {book["source_pdf"]["path"]}')
    print(f'Current Status: {book["verification"]["status"]}')
    print(f'Issues: {", ".join(book["verification"]["issues"])}')

    # Get source PDF path
    if not source_pdf_path:
        source_pdf_path = Path('d:/Work/songbook-splitter/SheetMusic') / book['source_pdf']['path']

    if not source_pdf_path.exists():
        print(f'ERROR: Source PDF not found at {source_pdf_path}')
        return False

    print(f'\nSource PDF: {source_pdf_path}')
    print(f'Size: {source_pdf_path.stat().st_size / (1024*1024):.2f} MB')

    # TODO: Implement your pipeline trigger here
    # This depends on how your pipeline works:
    # - Lambda function invocation?
    # - Step Functions execution?
    # - Local processing script?
    # - Docker container?

    print('\nPipeline trigger options:')
    print('1. AWS Lambda: boto3.client("lambda").invoke(...)')
    print('2. Step Functions: boto3.client("stepfunctions").start_execution(...)')
    print('3. Local script: subprocess.run(["py", "process_songbook.py", ...])')
    print('4. Manual: Check for manual split points in manual_splits/{book_id}.json')

    # Check for manual split points
    manual_split_file = Path(f'data/manual_splits/{book_id}.json')
    if manual_split_file.exists():
        print(f'\n[!] Manual split points found: {manual_split_file}')
        with open(manual_split_file, 'r') as f:
            manual_splits = json.load(f)
        print(f'    {len(manual_splits.get("songs", []))} songs defined')
        print('    Use these split points instead of auto-detection')

    print('\n[TODO] Implement actual pipeline trigger')
    print('For now, this script shows what would be reprocessed.')

    return True

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage:')
        print('  py reprocess_book.py <book_id>')
        print('  py reprocess_book.py --from-file books_to_reprocess.txt')
        sys.exit(1)

    if sys.argv[1] == '--from-file':
        # Process multiple books from file
        with open(sys.argv[2], 'r') as f:
            book_ids = [line.strip() for line in f if line.strip()]

        print(f'Reprocessing {len(book_ids)} books...\n')
        for book_id in book_ids:
            reprocess_book(book_id)
            print()
    else:
        # Process single book
        book_id = sys.argv[1]
        reprocess_book(book_id)
