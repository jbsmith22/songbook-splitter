#!/usr/bin/env python3
"""
Generate an interactive HTML viewer showing complete book lineage:
- Original books
- First-level splits (from AWS/Claude processing)
- Second-level splits (from manual verification corrections)
- Page numbers and gaps
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import PyPDF2

PROCESSED_SONGS_PATH = Path("c:/Work/AWSMusic/ProcessedSongs")

def load_aws_execution_results():
    """Load AWS execution results to get original book -> song mappings."""
    # Look for execution result files
    result_files = list(Path(".").glob("*-execution-results.json"))
    
    all_executions = {}
    for result_file in result_files:
        try:
            with open(result_file, 'r') as f:
                data = json.load(f)
                # Store by book name
                for execution in data:
                    book_name = execution.get('book_name', 'Unknown')
                    all_executions[book_name] = execution
        except:
            pass
    
    return all_executions

def get_pdf_page_count(pdf_path):
    """Get the number of pages in a PDF."""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            return len(reader.pages)
    except:
        return 0

def scan_processed_songs():
    """Scan ProcessedSongs directory to build artist -> book structure with page info."""
    artists = defaultdict(lambda: {
        'artist_name': None,
        'books': {}
    })
    
    if not PROCESSED_SONGS_PATH.exists():
        return artists
    
    for artist_dir in PROCESSED_SONGS_PATH.iterdir():
        if not artist_dir.is_dir():
            continue
        
        artist = artist_dir.name
        artists[artist]['artist_name'] = artist
        
        for book_dir in artist_dir.iterdir():
            if not book_dir.is_dir():
                continue
            
            book = book_dir.name
            
            artists[artist]['books'][book] = {
                'book_title': book,
                'original_songs': [],
                'total_pages': 0
            }
            
            # Count PDFs (original songs from AWS processing)
            for pdf_file in book_dir.glob("*.pdf"):
                # Skip .original backups
                if pdf_file.suffix == '.original':
                    continue
                
                # Check if this is an original (has .original backup) or a split result
                has_backup = pdf_file.with_suffix('.pdf.original').exists()
                
                # Get page count
                if has_backup:
                    page_count = get_pdf_page_count(pdf_file.with_suffix('.pdf.original'))
                else:
                    page_count = get_pdf_page_count(pdf_file)
                
                song_entry = {
                    'filename': pdf_file.name,
                    'path': str(pdf_file),
                    'page_count': page_count,
                    'is_original_from_aws': not has_backup,
                    'was_split': has_backup,
                    'splits': []
                }
                
                artists[artist]['books'][book]['original_songs'].append(song_entry)
                artists[artist]['books'][book]['total_pages'] += page_count
    
    return artists

def load_verification_data():
    """Load verification results and feedback."""
    # Load batch results
    batch1_results_file = Path("verification_results/batch1_results_filtered.json")
    if batch1_results_file.exists():
        with open(batch1_results_file, 'r') as f:
            batch1_results = json.load(f)
    else:
        batch1_results = []
    
    # Load feedback
    feedback_file = Path("review_feedback_2026-01-29.json")
    if feedback_file.exists():
        with open(feedback_file, 'r') as f:
            feedback = json.load(f)
    else:
        feedback = {'reviews': {}, 'splitInstructions': {}, 'correctTypes': {}}
    
    return batch1_results, feedback

def apply_verification_splits(artists, batch1_results, feedback):
    """Apply verification split data to artist/book structure."""
    
    flagged_pdfs = [r for r in batch1_results if not r['passed']]
    
    for idx, result in enumerate(flagged_pdfs):
        pdf_path = Path(result['pdf_path'])
        
        # Check for .original version
        if pdf_path.with_suffix('.pdf.original').exists():
            pdf_path = pdf_path.with_suffix('.pdf.original')
        
        if not pdf_path.exists():
            continue
        
        rel_path = pdf_path.relative_to(PROCESSED_SONGS_PATH)
        artist = rel_path.parts[0]
        book = rel_path.parts[1] if len(rel_path.parts) > 1 else "Unknown"
        
        if artist not in artists or book not in artists[artist]['books']:
            continue
        
        # Find this song in the book
        song_filename = pdf_path.name
        song_entry = None
        for song in artists[artist]['books'][book]['original_songs']:
            if song['filename'] == song_filename or song['filename'] + '.original' == song_filename:
                song_entry = song
                break
        
        if not song_entry:
            continue
        
        # Check if split
        idx_str = str(idx)
        if idx_str in feedback.get('splitInstructions', {}):
            splits = feedback['splitInstructions'][idx_str]
            song_entry['was_split'] = True
            
            for split in splits:
                split_entry = {
                    'title': split['title'],
                    'pages': split['pages'],
                    'filename': f"{artist} - {split['title']}.pdf"
                }
                song_entry['splits'].append(split_entry)
    
    return artists

def generate_html_viewer(artists, output_file):
    """Generate interactive HTML viewer with artist grouping."""
    
    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Sheet Music Book Lineage Viewer</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
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
        }
        .summary-stat {
            display: inline-block;
            margin-right: 30px;
            font-size: 16px;
        }
        .summary-stat strong {
            color: #2e7d32;
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
        .artist-stats {
            font-size: 14px;
            opacity: 0.95;
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
        .book-header {
            background: #2196F3;
            color: white;
            padding: 12px 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .book-header:hover {
            background: #1976D2;
        }
        .book-title {
            font-weight: bold;
            font-size: 16px;
        }
        .book-stats {
            font-size: 13px;
            opacity: 0.9;
        }
        .book-content {
            display: none;
            padding: 15px;
            background: white;
        }
        .book-content.expanded {
            display: block;
        }
        .song {
            margin: 10px 0;
            padding: 10px;
            background: #fafafa;
            border-left: 4px solid #4CAF50;
            border-radius: 3px;
        }
        .song.split {
            border-left-color: #FF9800;
        }
        .song-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        .song-filename {
            font-weight: 500;
            color: #333;
        }
        .song-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-left: 10px;
        }
        .badge-aws {
            background: #4CAF50;
            color: white;
        }
        .badge-split {
            background: #FF9800;
            color: white;
        }
        .splits-container {
            display: none;
            margin-top: 10px;
            padding-left: 20px;
            border-left: 2px solid #FF9800;
        }
        .splits-container.expanded {
            display: block;
        }
        .split-item {
            padding: 8px;
            margin: 5px 0;
            background: #fff3e0;
            border-radius: 3px;
            font-size: 14px;
        }
        .split-title {
            font-weight: 500;
            color: #e65100;
        }
        .split-pages {
            color: #666;
            font-size: 12px;
            margin-left: 10px;
        }
        .expand-icon {
            transition: transform 0.3s;
        }
        .expand-icon.expanded {
            transform: rotate(90deg);
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
            font-size: 14px;
        }
        .filter-bar button:hover {
            background: #1976D2;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Sheet Music Book Lineage Viewer</h1>
        
        <div class="summary">
            <div class="summary-stat"><strong>Total Artists:</strong> <span id="total-artists">0</span></div>
            <div class="summary-stat"><strong>Total Books:</strong> <span id="total-books">0</span></div>
            <div class="summary-stat"><strong>Total Songs:</strong> <span id="total-songs">0</span></div>
            <div class="summary-stat"><strong>Songs Split:</strong> <span id="songs-split">0</span></div>
            <div class="summary-stat"><strong>Final Song Count:</strong> <span id="final-songs">0</span></div>
        </div>
        
        <div class="filter-bar">
            <input type="text" id="search" placeholder="Search artists, books, or songs..." onkeyup="filterContent()">
            <label><input type="checkbox" id="show-split-only" onchange="filterContent()"> Show only items with splits</label>
            <button onclick="expandAll()">Expand All</button>
            <button onclick="collapseAll()">Collapse All</button>
        </div>
        
        <div id="artists-container">
            <!-- Artists will be inserted here -->
        </div>
    </div>
    
    <script>
        const artistsData = """ + json.dumps(artists) + """;
        
        function renderArtists() {
            const container = document.getElementById('artists-container');
            container.innerHTML = '';
            
            let totalArtists = 0;
            let totalBooks = 0;
            let totalSongs = 0;
            let songsSplit = 0;
            let finalSongs = 0;
            
            for (const [artistName, artistData] of Object.entries(artistsData).sort()) {
                totalArtists++;
                
                const artistDiv = document.createElement('div');
                artistDiv.className = 'artist';
                artistDiv.dataset.artistName = artistName;
                
                let booksInArtist = Object.keys(artistData.books).length;
                let songsInArtist = 0;
                let splitsInArtist = 0;
                let finalInArtist = 0;
                
                for (const [bookName, bookData] of Object.entries(artistData.books)) {
                    totalBooks++;
                    let songsInBook = bookData.original_songs.length;
                    let splitsInBook = bookData.original_songs.filter(s => s.splits && s.splits.length > 0).length;
                    let finalInBook = bookData.original_songs.reduce((sum, s) => {
                        return sum + (s.splits && s.splits.length > 0 ? s.splits.length : 1);
                    }, 0);
                    
                    songsInArtist += songsInBook;
                    splitsInArtist += splitsInBook;
                    finalInArtist += finalInBook;
                }
                
                totalSongs += songsInArtist;
                songsSplit += splitsInArtist;
                finalSongs += finalInArtist;
                
                artistDiv.innerHTML = `
                    <div class="artist-header" onclick="toggleArtist('${artistName}')">
                        <div>🎵 ${artistName}</div>
                        <div class="artist-stats">
                            ${booksInArtist} books | ${songsInArtist} songs | ${splitsInArtist} split | ${finalInArtist} final
                            <span class="expand-icon" id="icon-artist-${artistName}">▶</span>
                        </div>
                    </div>
                    <div class="artist-content" id="content-artist-${artistName}">
                        ${renderBooks(artistData.books, artistName)}
                    </div>
                `;
                
                container.appendChild(artistDiv);
            }
            
            document.getElementById('total-artists').textContent = totalArtists;
            document.getElementById('total-books').textContent = totalBooks;
            document.getElementById('total-songs').textContent = totalSongs;
            document.getElementById('songs-split').textContent = songsSplit;
            document.getElementById('final-songs').textContent = finalSongs;
        }
        
        function renderBooks(books, artistName) {
            return Object.entries(books).sort().map(([bookName, bookData]) => {
                const hasSplits = bookData.original_songs.some(s => s.splits && s.splits.length > 0);
                
                let songsInBook = bookData.original_songs.length;
                let splitsInBook = bookData.original_songs.filter(s => s.splits && s.splits.length > 0).length;
                let finalInBook = bookData.original_songs.reduce((sum, s) => {
                    return sum + (s.splits && s.splits.length > 0 ? s.splits.length : 1);
                }, 0);
                let totalPages = bookData.total_pages || 0;
                
                return `
                    <div class="book" data-book-name="${bookName}">
                        <div class="book-header" onclick="toggleBook('${artistName}', '${bookName}')">
                            <div class="book-title">${bookData.book_title}</div>
                            <div class="book-stats">
                                ${totalPages} pages | ${songsInBook} songs | ${splitsInBook} split | ${finalInBook} final
                                <span class="expand-icon" id="icon-book-${artistName}-${bookName}">▶</span>
                            </div>
                        </div>
                        <div class="book-content" id="content-book-${artistName}-${bookName}">
                            ${renderSongs(bookData.original_songs, artistName, bookName)}
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        function renderSongs(songs, artistName, bookName) {
            return songs.map((song, idx) => {
                const hasSplits = song.splits && song.splits.length > 0;
                const songClass = hasSplits ? 'song split' : 'song';
                const badge = hasSplits ? 
                    '<span class="song-badge badge-split">SPLIT</span>' : 
                    '<span class="song-badge badge-aws">AWS</span>';
                
                const songId = `${artistName}-${bookName}-${idx}`;
                
                const pageInfo = song.page_count ? 
                    `<span style="color: #666; font-size: 13px; margin-left: 10px;">(${song.page_count} pages)</span>` : '';
                
                const splitsHtml = hasSplits ? `
                    <div class="splits-container" id="splits-${songId}">
                        ${song.splits.map(split => `
                            <div class="split-item">
                                <span class="split-title">${split.title}</span>
                                <span class="split-pages">pages ${split.pages}</span>
                                <div style="font-size: 12px; color: #666; margin-top: 3px;">→ ${split.filename}</div>
                            </div>
                        `).join('')}
                    </div>
                ` : '';
                
                return `
                    <div class="${songClass}">
                        <div class="song-header" ${hasSplits ? `onclick="toggleSplits('${songId}')"` : ''}>
                            <div>
                                <span class="song-filename">${song.filename}</span>
                                ${badge}
                                ${pageInfo}
                                ${hasSplits ? `<span style="margin-left: 10px; color: #666; font-size: 13px;">(${song.splits.length} splits)</span>` : ''}
                            </div>
                            ${hasSplits ? '<span class="expand-icon" id="icon-splits-' + songId + '">▶</span>' : ''}
                        </div>
                        ${splitsHtml}
                    </div>
                `;
            }).join('');
        }
        
        function toggleArtist(artistName) {
            const content = document.getElementById('content-artist-' + artistName);
            const icon = document.getElementById('icon-artist-' + artistName);
            
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }
        
        function toggleBook(artistName, bookName) {
            const content = document.getElementById('content-book-' + artistName + '-' + bookName);
            const icon = document.getElementById('icon-book-' + artistName + '-' + bookName);
            
            content.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }
        
        function toggleSplits(songId) {
            const splits = document.getElementById('splits-' + songId);
            const icon = document.getElementById('icon-splits-' + songId);
            
            if (splits && icon) {
                splits.classList.toggle('expanded');
                icon.classList.toggle('expanded');
            }
        }
        
        function expandAll() {
            document.querySelectorAll('.artist-content, .book-content, .splits-container').forEach(el => {
                el.classList.add('expanded');
            });
            document.querySelectorAll('.expand-icon').forEach(el => {
                el.classList.add('expanded');
            });
        }
        
        function collapseAll() {
            document.querySelectorAll('.artist-content, .book-content, .splits-container').forEach(el => {
                el.classList.remove('expanded');
            });
            document.querySelectorAll('.expand-icon').forEach(el => {
                el.classList.remove('expanded');
            });
        }
        
        function filterContent() {
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const showSplitOnly = document.getElementById('show-split-only').checked;
            
            const artists = document.querySelectorAll('.artist');
            
            artists.forEach(artist => {
                const artistName = artist.dataset.artistName;
                const artistData = artistsData[artistName];
                
                let artistMatches = false;
                
                // Check if artist name matches
                if (artistName.toLowerCase().includes(searchTerm)) {
                    artistMatches = true;
                }
                
                // Check books and songs
                for (const [bookName, bookData] of Object.entries(artistData.books)) {
                    const bookMatches = bookName.toLowerCase().includes(searchTerm) ||
                        bookData.original_songs.some(s => s.filename.toLowerCase().includes(searchTerm));
                    
                    const hasSplits = bookData.original_songs.some(s => s.splits && s.splits.length > 0);
                    
                    if (bookMatches || artistMatches) {
                        if (!showSplitOnly || hasSplits) {
                            artistMatches = true;
                        }
                    }
                }
                
                artist.style.display = artistMatches ? 'block' : 'none';
            });
        }
        
        // Initial render
        renderArtists();
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

if __name__ == "__main__":
    print("Scanning ProcessedSongs directory...")
    artists = scan_processed_songs()
    print(f"Found {len(artists)} artists")
    
    print("\nLoading verification data...")
    batch1_results, feedback = load_verification_data()
    print(f"Loaded {len(batch1_results)} results, {len(feedback.get('splitInstructions', {}))} split instructions")
    
    print("\nApplying verification splits...")
    artists = apply_verification_splits(artists, batch1_results, feedback)
    
    output_file = Path("book_lineage_viewer.html")
    print(f"\nGenerating HTML viewer...")
    generate_html_viewer(dict(artists), output_file)
    
    print(f"✓ Viewer saved to: {output_file}")
    print(f"\nOpen {output_file} in your browser to view the interactive lineage.")
