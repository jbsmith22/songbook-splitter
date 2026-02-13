"""
Regenerate the V3 Book Index HTML page from local artifacts.

Scans SheetMusic_Artifacts for all completed books and generates
web/v3_book_index.html with current data.

Usage:
    python scripts/regenerate_v3_index.py
"""

import json
import os
from pathlib import Path
from html import escape

PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / 'SheetMusic_Artifacts'
OUTPUT_DIR = PROJECT_ROOT / 'SheetMusic_Output'
OUTPUT_HTML = PROJECT_ROOT / 'web' / 'v3_book_index.html'

EXPECTED_ARTIFACTS = [
    'toc_discovery.json', 'toc_parse.json', 'page_analysis.json',
    'page_mapping.json', 'verified_songs.json', 'output_files.json'
]


def scan_books():
    """Scan artifacts directory and collect book data."""
    books = []

    for artist_dir in sorted(ARTIFACTS_DIR.iterdir()):
        if not artist_dir.is_dir():
            continue
        artist = artist_dir.name
        # Skip batch results files at root level
        if artist.startswith('batch_results'):
            continue

        for book_dir in sorted(artist_dir.iterdir()):
            if not book_dir.is_dir():
                continue
            book_name = book_dir.name

            # Count artifacts
            artifact_count = sum(
                1 for a in EXPECTED_ARTIFACTS
                if (book_dir / a).exists()
            )

            # Load output_files.json if it exists
            output_file = book_dir / 'output_files.json'
            song_count = 0
            pdf_count = 0
            total_size_bytes = 0
            output_titles = []

            if output_file.exists():
                try:
                    with open(output_file) as f:
                        data = json.load(f)
                    files = data.get('output_files', [])
                    song_count = len(files)
                    pdf_count = len(files)
                    total_size_bytes = sum(
                        f.get('file_size_bytes', 0) for f in files
                    )
                    output_titles = [f.get('song_title', '') for f in files]
                except (json.JSONDecodeError, KeyError):
                    pass

            # TOC songs from toc_parse.json
            toc_songs = 0
            toc_titles = []
            toc_file = book_dir / 'toc_parse.json'
            if toc_file.exists():
                try:
                    with open(toc_file) as f:
                        toc_data = json.load(f)
                    entries = toc_data.get('entries', [])
                    toc_songs = len(entries)
                    toc_titles = [e.get('song_title', '') for e in entries]
                except (json.JSONDecodeError, KeyError):
                    pass

            # Vision-detected songs from page_analysis.json
            vision_titles = []
            pa_file = book_dir / 'page_analysis.json'
            if pa_file.exists():
                try:
                    with open(pa_file) as f:
                        pa_data = json.load(f)
                    for page in pa_data.get('pages', []):
                        if page.get('content_type') == 'song_start' and page.get('detected_title'):
                            vision_titles.append(page['detected_title'])
                except (json.JSONDecodeError, KeyError):
                    pass
            vision_songs = len(vision_titles)

            # Physical PDF files on local disk
            local_pdfs = 0
            disk_titles = []
            local_output_dir = OUTPUT_DIR / artist / book_name
            if local_output_dir.exists():
                for f in sorted(local_output_dir.iterdir()):
                    if f.suffix == '.pdf':
                        local_pdfs += 1
                        name = f.stem
                        # Strip "Artist - " prefix if present
                        if ' - ' in name:
                            name = name.split(' - ', 1)[1]
                        disk_titles.append(name)

            is_complete = artifact_count == 6

            books.append({
                'artist': artist,
                'book_name': book_name,
                'song_count': song_count,
                'toc_songs': toc_songs,
                'vision_songs': vision_songs,
                'local_pdfs': local_pdfs,
                'pdf_count': pdf_count,
                'total_size_mb': round(total_size_bytes / 1024 / 1024, 1),
                'artifact_count': artifact_count,
                'is_complete': is_complete,
                'output_titles': output_titles,
                'toc_titles': toc_titles,
                'vision_titles': vision_titles,
                'disk_titles': disk_titles,
            })

    return books


def generate_html(books):
    """Generate the index HTML."""
    total_artists = len(set(b['artist'] for b in books))
    total_books = len(books)
    complete_books = sum(1 for b in books if b['is_complete'])
    total_songs = sum(b['song_count'] for b in books)

    # Build details JSON for embedded song lists
    details = {}
    for i, b in enumerate(books):
        details[i] = {
            'output': sorted(b['output_titles'], key=str.casefold),
            'toc': sorted(b['toc_titles'], key=str.casefold),
            'vision': sorted(b['vision_titles'], key=str.casefold),
            'disk': sorted(b['disk_titles'], key=str.casefold),
        }
    details_json = json.dumps(details, ensure_ascii=False)

    rows = []
    for i, b in enumerate(books):
        css_class = 'complete' if b['is_complete'] else 'partial'
        artist_esc = escape(b['artist'])
        book_esc = escape(b['book_name'])
        artist_url = b['artist'].replace('&', '%26')
        book_url = b['book_name'].replace('&', '%26')

        # Color-code mismatches: green if matches song_count, orange if different
        toc_style = '' if b['toc_songs'] == 0 else (
            'color:#4CAF50;' if b['toc_songs'] == b['song_count'] else 'color:#FF9800;'
        )
        vision_style = (
            'color:#4CAF50;' if b['vision_songs'] == b['song_count'] else 'color:#FF9800;'
        )
        local_style = (
            'color:#4CAF50;' if b['local_pdfs'] == b['song_count'] else 'color:#FF9800;'
        )

        rows.append(f"""                    <tr class="book-row {css_class}" data-idx="{i}" onclick="toggleDetail({i})">
                        <td>{artist_esc}</td>
                        <td><strong>{book_esc}</strong></td>
                        <td style="text-align:center;">{b['song_count']}</td>
                        <td style="text-align:center;{toc_style}">{b['toc_songs']}</td>
                        <td style="text-align:center;{vision_style}">{b['vision_songs']}</td>
                        <td style="text-align:center;{local_style}">{b['local_pdfs']}</td>
                        <td style="text-align:center;">{b['total_size_mb']} MB</td>
                        <td style="text-align:center;">{b['artifact_count']}/6</td>
                        <td>
                            <a href="viewers/v3_provenance_viewer.html?artist={artist_url}&book={book_url}" class="link-btn viewer" onclick="event.stopPropagation()">Provenance</a>
                            <a href="editors/boundary_review.html?artist={artist_url}&book={book_url}" class="link-btn editor" onclick="event.stopPropagation()">Review</a>
                            <a href="editors/v3_split_editor.html?artist={artist_url}&book={book_url}" class="link-btn" style="background:#666;color:white;" onclick="event.stopPropagation()">Split</a>
                        </td>
                    </tr>""")

    rows_html = '\n'.join(rows)

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
            max-width: 1600px;
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
            box-sizing: border-box;
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
            cursor: pointer;
        }}
        th:hover {{
            background: #00b8d4;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #333;
        }}
        tr.book-row {{
            cursor: pointer;
        }}
        tr.book-row:hover {{
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
        tr.detail-row td {{
            background: #0a1628;
            padding: 12px 20px;
            border-bottom: 2px solid #00d9ff;
        }}
        tr.detail-row:hover {{
            background: inherit;
        }}
        .detail-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr 1fr;
            gap: 20px;
        }}
        .detail-col h4 {{
            color: #00d9ff;
            margin: 0 0 8px 0;
            font-size: 13px;
            text-transform: uppercase;
        }}
        .detail-col ol {{
            margin: 0;
            padding-left: 24px;
            font-size: 12px;
            color: #ccc;
            max-height: 300px;
            overflow-y: auto;
        }}
        .detail-col ol li {{
            padding: 2px 0;
        }}
        .detail-col ol li.mismatch {{
            color: #FF9800;
        }}
        .detail-col .empty {{
            color: #666;
            font-style: italic;
            font-size: 12px;
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

        <table id="index-table">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Artist</th>
                    <th onclick="sortTable(1)">Book</th>
                    <th onclick="sortTable(2)">Songs</th>
                    <th onclick="sortTable(3)">TOC</th>
                    <th onclick="sortTable(4)">Vision</th>
                    <th onclick="sortTable(5)">Disk PDFs</th>
                    <th onclick="sortTable(6)">Size</th>
                    <th onclick="sortTable(7)">Artifacts</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="book-table">
{rows_html}
            </tbody>
        </table>

        <div class="note">
            <strong>Regenerate:</strong> <code>python scripts/regenerate_v3_index.py</code><br>
            <strong>Serve:</strong> <code>cd d:\\\\Work\\\\songbook-splitter && python -m http.server 8000</code><br>
            Then open <code>http://localhost:8000/web/v3_book_index.html</code>
        </div>
    </div>

    <script>
        const BOOK_DETAILS = {details_json};

        function escHtml(s) {{
            return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
        }}

        function buildDetailHTML(d) {{
            var refCounts = {{}};
            if (d.output) d.output.forEach(function(t) {{
                var k = t.toLowerCase();
                refCounts[k] = (refCounts[k] || 0) + 1;
            }});
            function makeList(items, label, highlight) {{
                if (!items || items.length === 0)
                    return '<div class="detail-col"><h4>' + label + ' (0)</h4><div class="empty">None detected</div></div>';
                var remaining = {{}};
                if (highlight) {{ for (var k in refCounts) remaining[k] = refCounts[k]; }}
                var html = '<div class="detail-col"><h4>' + label + ' (' + items.length + ')</h4><ol>';
                items.forEach(function(t) {{
                    var mismatch = false;
                    if (highlight) {{
                        var k = t.toLowerCase();
                        if (remaining[k] && remaining[k] > 0) {{ remaining[k]--; }}
                        else {{ mismatch = true; }}
                    }}
                    html += '<li' + (mismatch ? ' class="mismatch"' : '') + '>' + escHtml(t) + '</li>';
                }});
                html += '</ol></div>';
                return html;
            }}
            return '<div class="detail-grid">' +
                makeList(d.output, 'Songs (Final)', false) +
                makeList(d.toc, 'TOC Detected', true) +
                makeList(d.vision, 'Vision Detected', true) +
                makeList(d.disk, 'Disk Files', true) +
                '</div>';
        }}

        function toggleDetail(idx) {{
            var detailRow = document.querySelector('tr.detail-row[data-parent="' + idx + '"]');
            if (detailRow) {{
                detailRow.style.display = detailRow.style.display === 'none' ? '' : 'none';
            }} else {{
                var d = BOOK_DETAILS[idx];
                if (!d) return;
                var bookRow = document.querySelector('tr.book-row[data-idx="' + idx + '"]');
                detailRow = document.createElement('tr');
                detailRow.className = 'detail-row';
                detailRow.dataset.parent = idx;
                var td = document.createElement('td');
                td.colSpan = 9;
                td.innerHTML = buildDetailHTML(d);
                detailRow.appendChild(td);
                bookRow.after(detailRow);
            }}
        }}

        function filterTable() {{
            var search = document.getElementById('search').value.toLowerCase();
            document.querySelectorAll('#book-table tr.book-row').forEach(function(row) {{
                var text = row.textContent.toLowerCase();
                var show = text.includes(search);
                row.style.display = show ? '' : 'none';
                var detail = document.querySelector('tr.detail-row[data-parent="' + row.dataset.idx + '"]');
                if (detail) detail.style.display = show ? detail.style.display : 'none';
            }});
        }}

        var sortDir = {{}};
        function sortTable(colIndex) {{
            var tbody = document.getElementById('book-table');
            var bookRows = Array.from(tbody.querySelectorAll('tr.book-row'));
            var dir = sortDir[colIndex] = !(sortDir[colIndex] || false);

            bookRows.sort(function(a, b) {{
                var aVal = a.cells[colIndex].textContent.trim();
                var bVal = b.cells[colIndex].textContent.trim();
                var aNum = parseFloat(aVal);
                var bNum = parseFloat(bVal);
                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return dir ? aNum - bNum : bNum - aNum;
                }}
                return dir ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }});

            bookRows.forEach(function(row) {{
                tbody.appendChild(row);
                var detail = document.querySelector('tr.detail-row[data-parent="' + row.dataset.idx + '"]');
                if (detail) tbody.appendChild(detail);
            }});
        }}
    </script>
</body>
</html>"""

    return html


def main():
    books = scan_books()
    print(f"Found {len(books)} books across {len(set(b['artist'] for b in books))} artists")
    print(f"  Complete (6/6 artifacts): {sum(1 for b in books if b['is_complete'])}")
    print(f"  Partial: {sum(1 for b in books if not b['is_complete'])}")
    print(f"  Total songs: {sum(b['song_count'] for b in books)}")

    html = generate_html(books)
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nGenerated: {OUTPUT_HTML}")
    print(f"  Size: {len(html):,} bytes")


if __name__ == '__main__':
    main()
