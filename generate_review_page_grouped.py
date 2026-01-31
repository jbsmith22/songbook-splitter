#!/usr/bin/env python3
"""
Generate HTML review page from verification results, grouped by book.
"""

import json
from pathlib import Path
from collections import defaultdict

def group_by_book(flagged_pdfs):
    """Group PDFs by book (artist/book path)."""
    books = defaultdict(list)
    
    for pdf in flagged_pdfs:
        pdf_path = Path(pdf['pdf_path'])
        # Extract artist and book from path
        # Path format: ProcessedSongs/Artist/Book/Artist - Song.pdf
        parts = pdf_path.parts
        if len(parts) >= 3:
            artist = parts[-3]
            book = parts[-2]
            book_key = f"{artist}/{book}"
        else:
            book_key = "Unknown"
        
        books[book_key].append(pdf)
    
    return books

def generate_html_grouped(results_file: Path, output_file: Path):
    """Generate grouped HTML review page."""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Filter to only flagged PDFs
    flagged = [r for r in results if not r['passed']]
    
    # Group by book
    books = group_by_book(flagged)
    
    # Sort books by number of flagged PDFs (most problematic first)
    sorted_books = sorted(books.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"Grouped {len(flagged)} flagged PDFs into {len(books)} books")
    print(f"Top 5 books with most issues:")
    for book_name, pdfs in sorted_books[:5]:
        print(f"  {book_name}: {len(pdfs)} PDFs")
    
    # Start generating HTML (keeping most of the original styles)
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Verification Review (Grouped by Book)</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .book-group {
            background: white;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .book-header {
            padding: 15px 20px;
            background: #e3f2fd;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 2px solid #2196f3;
        }
        .book-header:hover {
            background: #bbdefb;
        }
        .book-header.collapsed {
            border-bottom: none;
        }
        .book-title {
            font-size: 18px;
            font-weight: bold;
            color: #1976d2;
        }
        .book-stats {
            font-size: 14px;
            color: #666;
        }
        .book-actions {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        .btn-reprocess {
            background: #ff9800;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .btn-reprocess:hover {
            background: #f57c00;
        }
        .btn-reprocess.marked {
            background: #f44336;
        }
        .collapse-icon {
            font-size: 24px;
            transition: transform 0.3s;
        }
        .collapse-icon.collapsed {
            transform: rotate(-90deg);
        }
        .book-content {
            max-height: 10000px;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }
        .book-content.collapsed {
            max-height: 0;
        }
        .pdf-card {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
        }
        .pdf-card:last-child {
            border-bottom: none;
        }
        /* Keep all the existing PDF card styles */
        .pdf-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        }
        .pdf-title {
            font-size: 16px;
            font-weight: bold;
            color: #333;
        }
        .issues {
            background: #fff3e0;
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 15px;
        }
        .issue-item {
            color: #e65100;
            font-weight: 500;
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>PDF Verification Review (Grouped by Book)</h1>
        <p>Books with systematic issues can be marked for reprocessing instead of manual review.</p>
        <div style="margin-top: 10px;">
            <strong>Total Books:</strong> """ + str(len(books)) + """ | 
            <strong>Total Flagged PDFs:</strong> """ + str(len(flagged)) + """
        </div>
    </div>
    
    <div id="book-list">
"""
    
    # Generate book groups
    global_pdf_index = 0
    for book_name, book_pdfs in sorted_books:
        book_id = book_name.replace('/', '_').replace(' ', '_')
        
        html += f"""
    <div class="book-group" id="book-{book_id}">
        <div class="book-header" onclick="toggleBook('{book_id}')">
            <div>
                <div class="book-title">{book_name}</div>
                <div class="book-stats">{len(book_pdfs)} flagged PDFs</div>
            </div>
            <div class="book-actions">
                <button class="btn-reprocess" onclick="event.stopPropagation(); markBookForReprocessing('{book_id}', '{book_name}')" id="reprocess-{book_id}">
                    Mark for Reprocessing
                </button>
                <span class="collapse-icon" id="icon-{book_id}">▼</span>
            </div>
        </div>
        <div class="book-content" id="content-{book_id}">
"""
        
        # Add PDFs for this book (simplified view)
        for pdf in book_pdfs:
            html += f"""
            <div class="pdf-card">
                <div class="pdf-header">
                    <div class="pdf-title">{pdf['pdf_name']}</div>
                </div>
                <div class="issues">
                    <strong>Detected Issues:</strong>
"""
            for issue in pdf['issues']:
                html += f'                    <div class="issue-item">• {issue}</div>\n'
            
            html += """                </div>
            </div>
"""
            global_pdf_index += 1
        
        html += """        </div>
    </div>
"""
    
    html += """
    </div>
    
    <script>
        let booksMarkedForReprocessing = new Set();
        
        function toggleBook(bookId) {
            const content = document.getElementById('content-' + bookId);
            const icon = document.getElementById('icon-' + bookId);
            const header = document.querySelector(`#book-${bookId} .book-header`);
            
            content.classList.toggle('collapsed');
            icon.classList.toggle('collapsed');
            header.classList.toggle('collapsed');
        }
        
        function markBookForReprocessing(bookId, bookName) {
            const btn = document.getElementById('reprocess-' + bookId);
            
            if (booksMarkedForReprocessing.has(bookId)) {
                // Unmark
                booksMarkedForReprocessing.delete(bookId);
                btn.classList.remove('marked');
                btn.textContent = 'Mark for Reprocessing';
            } else {
                // Mark
                booksMarkedForReprocessing.add(bookId);
                btn.classList.add('marked');
                btn.textContent = '✓ Marked for Reprocessing';
            }
            
            saveData();
        }
        
        function saveData() {
            localStorage.setItem('books-for-reprocessing', JSON.stringify(Array.from(booksMarkedForReprocessing)));
        }
        
        function exportReprocessingList() {
            const exportData = {
                booksForReprocessing: Array.from(booksMarkedForReprocessing),
                timestamp: new Date().toISOString()
            };
            
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'books_for_reprocessing_' + new Date().toISOString().split('T')[0] + '.json';
            a.click();
        }
        
        // Load saved data
        const savedBooks = localStorage.getItem('books-for-reprocessing');
        if (savedBooks) {
            booksMarkedForReprocessing = new Set(JSON.parse(savedBooks));
            booksMarkedForReprocessing.forEach(bookId => {
                const btn = document.getElementById('reprocess-' + bookId);
                if (btn) {
                    btn.classList.add('marked');
                    btn.textContent = '✓ Marked for Reprocessing';
                }
            });
        }
        
        // Add export button
        window.addEventListener('load', () => {
            const header = document.querySelector('.header');
            const exportBtn = document.createElement('button');
            exportBtn.textContent = '💾 Export Reprocessing List';
            exportBtn.style.marginTop = '10px';
            exportBtn.style.padding = '10px 20px';
            exportBtn.style.background = '#4caf50';
            exportBtn.style.color = 'white';
            exportBtn.style.border = 'none';
            exportBtn.style.borderRadius = '4px';
            exportBtn.style.cursor = 'pointer';
            exportBtn.style.fontWeight = 'bold';
            exportBtn.onclick = exportReprocessingList;
            header.appendChild(exportBtn);
        });
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✓ Grouped review page generated: {output_file}")
    print(f"  Books: {len(books)}")
    print(f"  Flagged PDFs: {len(flagged)}")
    print(f"\nOpen in browser: file:///{output_file.absolute()}")

if __name__ == "__main__":
    results_file = Path("verification_results/batch1_results.json")
    output_file = Path("verification_results/batch1_review_grouped.html")
    
    if not results_file.exists():
        print(f"Error: {results_file} not found")
    else:
        generate_html_grouped(results_file, output_file)
