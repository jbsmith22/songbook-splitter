"""
Generate V3 Book Index HTML page.

Scans SheetMusic_Artifacts for processed books and creates an index page
with links to the provenance viewer and split editor for each book.

Usage:
    python scripts/generate_v3_index.py
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
OUTPUT_FILE = PROJECT_ROOT / 'web' / 'v3_book_index.html'

EXPECTED_ARTIFACTS = [
    'toc_discovery.json', 'toc_parse.json', 'page_analysis.json',
    'page_mapping.json', 'verified_songs.json', 'output_files.json'
]


def scan_books():
    """Scan SheetMusic_Artifacts for all processed books."""
    books = []
    if not ARTIFACTS_DIR.exists():
        return books

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book = book_dir.name

            # Check which artifacts exist
            artifact_count = sum(
                1 for a in EXPECTED_ARTIFACTS
                if (book_dir / a).exists()
            )

            # Load verified_songs for song count
            song_count = 0
            vs_file = book_dir / 'verified_songs.json'
            if vs_file.exists():
                try:
                    with open(vs_file) as f:
                        vs_data = json.load(f)
                    song_list = vs_data.get('verified_songs', vs_data)
                    if isinstance(song_list, list):
                        song_count = len(song_list)
                except Exception:
                    pass

            # Load output_files for total size
            total_size = 0
            of_file = book_dir / 'output_files.json'
            if of_file.exists():
                try:
                    with open(of_file) as f:
                        of_data = json.load(f)
                    files = of_data.get('output_files', of_data)
                    if isinstance(files, list):
                        total_size = sum(f.get('file_size_bytes', 0) for f in files)
                except Exception:
                    pass

            # Count output PDFs
            output_book_dir = OUTPUT_DIR / artist / book
            pdf_count = len(list(output_book_dir.glob('*.pdf'))) if output_book_dir.exists() else 0

            books.append({
                'artist': artist,
                'book': book,
                'artifact_count': artifact_count,
                'song_count': song_count,
                'pdf_count': pdf_count,
                'total_size_mb': round(total_size / 1024 / 1024, 1) if total_size else 0,
                'complete': artifact_count == 6,
            })

    return books


def generate_html(books):
    """Generate the index HTML page."""
    artists = {}
    for b in books:
        artists.setdefault(b['artist'], []).append(b)

    total_songs = sum(b['song_count'] for b in books)
    total_books = len(books)
    total_artists = len(artists)
    complete_books = sum(1 for b in books if b['complete'])

    book_rows = []
    for b in books:
        status_class = 'complete' if b['complete'] else 'partial'
        status_text = f"{b['artifact_count']}/6"
        viewer_url = f"viewers/v3_provenance_viewer.html?artist={b['artist']}&book={b['book']}"
        editor_url = f"editors/v3_split_editor.html?artist={b['artist']}&book={b['book']}"
        book_rows.append(f"""
                    <tr class="{status_class}">
                        <td>{b['artist']}</td>
                        <td><strong>{b['book']}</strong></td>
                        <td style="text-align:center;">{b['song_count']}</td>
                        <td style="text-align:center;">{b['pdf_count']}</td>
                        <td style="text-align:center;">{b['total_size_mb']} MB</td>
                        <td style="text-align:center;">{status_text}</td>
                        <td>
                            <a href="{viewer_url}" class="link-btn viewer">Provenance</a>
                            <a href="{editor_url}" class="link-btn editor">Split Editor</a>
                        </td>
                    </tr>""")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>V3 Processed Books Index</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: #1a1a2e;
            color: #eee;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: #16213e;
            padding: 30px;
            border-radius: 8px;
        }}
        h1 {{
            color: #00d9ff;
            border-bottom: 3px solid #00d9ff;
            padding-bottom: 10px;
        }}
        .stats-bar {{
            display: flex;
            gap: 30px;
            margin: 20px 0;
            padding: 15px 20px;
            background: #0f3460;
            border-radius: 5px;
        }}
        .stats-bar .stat {{
            text-align: center;
        }}
        .stats-bar .stat-value {{
            font-size: 28px;
            font-weight: bold;
            color: #00d9ff;
        }}
        .stats-bar .stat-label {{
            font-size: 12px;
            color: #888;
            text-transform: uppercase;
        }}
        .search-box {{
            padding: 10px;
            width: 100%;
            border: 1px solid #333;
            border-radius: 3px;
            font-size: 14px;
            background: #1a1a2e;
            color: #eee;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th {{
            background: #00d9ff;
            color: #1a1a2e;
            padding: 10px 8px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #333;
        }}
        tr:hover {{
            background: #0f3460;
        }}
        tr.partial td:first-child {{
            border-left: 3px solid #FF9800;
        }}
        tr.complete td:first-child {{
            border-left: 3px solid #4CAF50;
        }}
        .link-btn {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 3px;
            text-decoration: none;
            font-size: 12px;
            font-weight: bold;
            margin-right: 4px;
        }}
        .link-btn.viewer {{
            background: #2196F3;
            color: white;
        }}
        .link-btn.editor {{
            background: #FF9800;
            color: white;
        }}
        .link-btn:hover {{
            opacity: 0.8;
        }}
        .note {{
            margin-top: 20px;
            padding: 15px;
            background: #0f3460;
            border-radius: 5px;
            font-size: 13px;
            color: #aaa;
        }}
        .note code {{
            background: #1a1a2e;
            padding: 2px 6px;
            border-radius: 3px;
            color: #00d9ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>V3 Processed Books Index</h1>

        <div class="stats-bar">
            <div class="stat"><div class="stat-value">{total_artists}</div><div class="stat-label">Artists</div></div>
            <div class="stat"><div class="stat-value">{total_books}</div><div class="stat-label">Books</div></div>
            <div class="stat"><div class="stat-value">{complete_books}</div><div class="stat-label">Complete</div></div>
            <div class="stat"><div class="stat-value">{total_songs}</div><div class="stat-label">Total Songs</div></div>
        </div>

        <input type="text" class="search-box" id="search" placeholder="Search by artist or book name..." oninput="filterTable()">

        <table>
            <thead>
                <tr>
                    <th>Artist</th>
                    <th>Book</th>
                    <th>Songs</th>
                    <th>PDFs</th>
                    <th>Size</th>
                    <th>Artifacts</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="book-table">{''.join(book_rows)}
            </tbody>
        </table>

        <div class="note">
            <strong>Usage:</strong> Serve this project via HTTP to enable artifact loading:<br>
            <code>cd d:\\Work\\songbook-splitter && python -m http.server 8000</code><br>
            Then open <code>http://localhost:8000/web/v3_book_index.html</code>
        </div>
    </div>

    <script>
        function filterTable() {{
            const search = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('#book-table tr').forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(search) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""
    return html


def main():
    books = scan_books()
    print(f"Found {len(books)} processed books")

    html = generate_html(books)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Generated: {OUTPUT_FILE}")
    print(f"  Artists: {len(set(b['artist'] for b in books))}")
    print(f"  Books:   {len(books)}")
    print(f"  Songs:   {sum(b['song_count'] for b in books)}")


if __name__ == '__main__':
    main()
