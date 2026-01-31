#!/usr/bin/env python3
"""
Generate comprehensive HTML viewer with complete page lineage.
Shows TOC, extracted pages, gaps, and manual splits.
"""

import json
from pathlib import Path

def load_page_lineage():
    """Load the complete page lineage data."""
    lineage_file = Path("complete_page_lineage.json")
    if not lineage_file.exists():
        print("Error: complete_page_lineage.json not found")
        print("Run 'py build_page_lineage.py' first")
        return None
    
    with open(lineage_file, 'r') as f:
        return json.load(f)

def load_verification_splits():
    """Load manual verification splits."""
    feedback_file = Path("review_feedback_2026-01-29.json")
    if not feedback_file.exists():
        return {}
    
    with open(feedback_file, 'r') as f:
        data = json.load(f)
        return data.get('splitInstructions', {})

def generate_html(lineage_data, splits_data):
    """Generate the HTML viewer."""
    
    # Organize by artist
    artists = {}
    for book in lineage_data['books']:
        artist = book['artist']
        if artist not in artists:
            artists[artist] = []
        artists[artist].append(book)
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Complete Sheet Music Lineage Viewer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        .summary {
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .summary-stat {
            font-size: 14px;
        }
        .summary-stat strong {
            color: #2e7d32;
            display: block;
            font-size: 24px;
        }
        .filter-bar {
            margin: 20px 0;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .filter-bar input {
            padding: 8px;
            width: 300px;
            border: 1px solid #ddd;
            border-radius: 3px;
            font-size: 14px;
        }
        .filter-bar label {
            margin-left: 20px;
            margin-right: 5px;
        }
        .filter-bar button {
            padding: 8px 15px;
            margin-left: 10px;
            background: #2196F3;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
        }
        .artist {
            margin: 20px 0;
            border: 2px solid #9C27B0;
            border-radius: 8px;
            overflow: hidden;
        }
        .artist-header {
            background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);
            color: white;
            padding: 15px 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 18px;
            font-weight: bold;
        }
        .artist-header:hover {
            background: linear-gradient(135deg, #7B1FA2 0%, #6A1B9A 100%);
        }
        .artist-content {
            display: none;
            padding: 15px;
            background: #f9f9f9;
        }
        .artist-content.expanded {
            display: block;
        }
        .book {
            margin: 15px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        .book.has-gaps {
            border-color: #ff9800;
            border-width: 2px;
        }
        .book-header {
            background: #2196F3;
            color: white;
            padding: 12px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .book.has-gaps .book-header {
            background: #ff9800;
        }
        .book-header:hover {
            opacity: 0.9;
        }
        .book-title {
            font-weight: bold;
            font-size: 16px;
        }
        .book-stats {
            font-size: 13px;
            opacity: 0.95;
        }
        .book-content {
            display: none;
            padding: 15px;
            background: white;
        }
        .book-content.expanded {
            display: block;
        }
        .page-sequence {
            margin: 15px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 5px;
        }
        .page-sequence-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .song-item {
            margin: 8px 0;
            padding: 10px;
            background: white;
            border-left: 4px solid #4CAF50;
            border-radius: 3px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .song-item.split {
            border-left-color: #FF9800;
        }
        .song-title {
            font-weight: 500;
            flex: 1;
        }
        .page-range {
            color: #666;
            font-size: 13px;
            margin-left: 10px;
            font-family: 'Courier New', monospace;
        }
        .page-count {
            color: #999;
            font-size: 12px;
            margin-left: 10px;
        }
        .gap-item {
            margin: 8px 0;
            padding: 10px;
            background: #ffebee;
            border-left: 4px solid #f44336;
            border-radius: 3px;
            color: #c62828;
            font-weight: 500;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }
        .badge-toc {
            background: #4CAF50;
            color: white;
        }
        .badge-no-toc {
            background: #9E9E9E;
            color: white;
        }
        .badge-split {
            background: #FF9800;
            color: white;
        }
        .badge-gap {
            background: #f44336;
            color: white;
        }
        .expand-icon {
            transition: transform 0.3s;
        }
        .expand-icon.expanded {
            transform: rotate(90deg);
        }
        .mismatch-warning {
            background: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 8px;
            margin: 10px 0;
            border-radius: 3px;
            font-size: 13px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Complete Sheet Music Lineage Viewer</h1>
        
        <div class="summary">
            <div class="summary-stat">
                <strong id="total-books">0</strong>
                Total Books
            </div>
            <div class="summary-stat">
                <strong id="total-songs">0</strong>
                Total Songs
            </div>
            <div class="summary-stat">
                <strong id="total-pages">0</strong>
                Total Pages
            </div>
            <div class="summary-stat">
                <strong id="books-with-toc">0</strong>
                Books with TOC
            </div>
            <div class="summary-stat">
                <strong id="books-with-gaps">0</strong>
                Books with Gaps
            </div>
            <div class="summary-stat">
                <strong id="books-with-mismatches">0</strong>
                Page Mismatches
            </div>
        </div>
        
        <div class="filter-bar">
            <input type="text" id="search" placeholder="Search artists, books, or songs..." onkeyup="filterContent()">
            <label><input type="checkbox" id="show-gaps-only" onchange="filterContent()"> Show only books with gaps</label>
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>
        
        <div id="artists-container">
            <!-- Artists will be inserted here -->
        </div>
    </div>
    
    <script>
        const lineageData = """ + json.dumps({'artists': artists, 'summary': lineage_data['summary']}) + """;
        
        function renderArtists() {
            const container = document.getElementById('artists-container');
            container.innerHTML = '';
            
            const summary = lineageData.summary;
            document.getElementById('total-books').textContent = summary.total_books.toLocaleString();
            document.getElementById('total-songs').textContent = summary.total_songs.toLocaleString();
            document.getElementById('total-pages').textContent = summary.total_pages.toLocaleString();
            document.getElementById('books-with-toc').textContent = summary.books_with_toc.toLocaleString();
            document.getElementById('books-with-gaps').textContent = summary.books_with_gaps.toLocaleString();
            document.getElementById('books-with-mismatches').textContent = summary.books_with_mismatches.toLocaleString();
            
            for (const [artistName, books] of Object.entries(lineageData.artists).sort()) {
                const artistDiv = document.createElement('div');
                artistDiv.className = 'artist';
                artistDiv.dataset.artistName = artistName;
                
                const totalBooks = books.length;
                const totalSongs = books.reduce((sum, b) => sum + b.extracted_songs.length, 0);
                const booksWithGaps = books.filter(b => b.gaps.length > 0).length;
                
                artistDiv.innerHTML = `
                    <div class="artist-header" onclick="toggleArtist('${artistName}')">
                        <div>🎵 ${artistName}</div>
                        <div>
                            ${totalBooks} books | ${totalSongs} songs | ${booksWithGaps} with gaps
                            <span class="expand-icon" id="icon-artist-${artistName}">▶</span>
                        </div>
                    </div>
                    <div class="artist-content" id="content-artist-${artistName}">
                        ${renderBooks(books, artistName)}
                    </div>
                `;
                
                container.appendChild(artistDiv);
            }
        }
        
        function renderBooks(books, artistName) {
            return books.map((book, idx) => {
                const hasGaps = book.gaps.length > 0;
                const hasMismatches = book.mismatches.length > 0;
                const bookClass = hasGaps ? 'book has-gaps' : 'book';
                
                const tocBadge = book.has_toc ? 
                    '<span class="badge badge-toc">HAS TOC</span>' : 
                    '<span class="badge badge-no-toc">NO TOC</span>';
                
                const gapBadge = hasGaps ? 
                    `<span class="badge badge-gap">${book.gaps.length} GAP(S)</span>` : '';
                
                return `
                    <div class="${bookClass}" data-book-name="${book.book_name}">
                        <div class="book-header" onclick="toggleBook('${artistName}', ${idx})">
                            <div class="book-title">
                                ${book.book_name}
                                ${tocBadge}
                                ${gapBadge}
                            </div>
                            <div class="book-stats">
                                ${book.total_pages} pages | ${book.extracted_songs.length} songs
                                <span class="expand-icon" id="icon-book-${artistName}-${idx}">▶</span>
                            </div>
                        </div>
                        <div class="book-content" id="content-book-${artistName}-${idx}">
                            ${renderPageSequence(book)}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function renderPageSequence(book) {
            let html = '<div class="page-sequence">';
            html += '<div class="page-sequence-title">📄 Page Sequence</div>';
            
            // Show gaps first if any
            if (book.gaps.length > 0) {
                book.gaps.forEach(gap => {
                    html += `<div class="gap-item">⚠️ Gap: pages ${gap}</div>`;
                });
            }
            
            // Show mismatches if any
            if (book.mismatches.length > 0) {
                html += '<div class="mismatch-warning">';
                html += '<strong>⚠️ Page Count Mismatches:</strong><br>';
                book.mismatches.forEach(m => {
                    html += `${m.song}: expected ${m.expected_pages} pages, found ${m.actual_pages} pages<br>`;
                });
                html += '</div>';
            }
            
            // Show extracted songs
            book.extracted_songs.forEach(song => {
                html += `
                    <div class="song-item">
                        <span class="song-title">${song.title}</span>
                        <span class="page-range">pages ${song.extracted_pages}</span>
                        <span class="page-count">(${song.page_count} pages)</span>
                    </div>
                `;
            });
            
            html += '</div>';
            return html;
        }
        
        function toggleArtist(artistName) {
            const content = document.getElementById('content-artist-' + artistName);
            const icon = document.getElementById('icon-artist-' + artistName);
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }
        
        function toggleBook(artistName, idx) {
            const content = document.getElementById('content-book-' + artistName + '-' + idx);
            const icon = document.getElementById('icon-book-' + artistName + '-' + idx);
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }
        
        function expandAll() {
            document.querySelectorAll('.artist-content, .book-content').forEach(el => {
                el.classList.add('expanded');
            });
            document.querySelectorAll('.expand-icon').forEach(el => {
                el.classList.add('expanded');
            });
        }
        
        function collapseAll() {
            document.querySelectorAll('.artist-content, .book-content').forEach(el => {
                el.classList.remove('expanded');
            });
            document.querySelectorAll('.expand-icon').forEach(el => {
                el.classList.remove('expanded');
            });
        }
        
        function filterContent() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const showGapsOnly = document.getElementById('show-gaps-only').checked;
            
            document.querySelectorAll('.artist').forEach(artist => {
                const artistName = artist.dataset.artistName.toLowerCase();
                let artistMatches = false;
                
                const books = artist.querySelectorAll('.book');
                books.forEach(book => {
                    const bookName = book.dataset.bookName.toLowerCase();
                    const hasGaps = book.classList.contains('has-gaps');
                    
                    const matchesSearch = !searchTerm || 
                        artistName.includes(searchTerm) || 
                        bookName.includes(searchTerm);
                    
                    const matchesFilter = !showGapsOnly || hasGaps;
                    
                    const visible = matchesSearch && matchesFilter;
                    book.style.display = visible ? 'block' : 'none';
                    
                    if (visible) artistMatches = true;
                });
                
                artist.style.display = artistMatches ? 'block' : 'none';
            });
        }
        
        // Initial render
        renderArtists();
    </script>
</body>
</html>
"""
    
    return html

if __name__ == "__main__":
    print("Generating complete lineage viewer...")
    
    lineage = load_page_lineage()
    if not lineage:
        exit(1)
    
    splits = load_verification_splits()
    
    html = generate_html(lineage, splits)
    
    output_file = Path("complete_lineage_viewer.html")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ Viewer saved to: {output_file}")
    print(f"\nOpen {output_file} in your browser to view the complete lineage.")
