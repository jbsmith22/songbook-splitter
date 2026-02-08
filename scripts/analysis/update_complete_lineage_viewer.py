"""
Update the complete lineage viewer with latest data.
Creates a self-contained HTML file with embedded verification data.
"""
import json
from pathlib import Path
from datetime import datetime

def main():
    # Read the complete lineage data
    data_file = Path('data/analysis/complete_lineage_data.json')
    if not data_file.exists():
        print("Error: Run generate_complete_lineage_all.py first")
        return

    with open(data_file) as f:
        data = json.load(f)

    print(f"Loaded {data['total_books']} books")

    # Calculate statistics
    successful = sum(1 for b in data['books'] if b['dynamodb']['status'] == 'success')
    failed = sum(1 for b in data['books'] if b['dynamodb']['status'] == 'failed')
    in_progress = sum(1 for b in data['books'] if b['dynamodb']['status'] == 'in_progress')
    consistent = sum(1 for b in data['books'] if b['consistency']['status'] == 'CONSISTENT')
    local_synced = sum(1 for b in data['books'] if b['local']['exists'])
    avg_completeness = sum(b['completeness']['percentage'] for b in data['books']) / len(data['books'])

    stats = {
        'total': data['total_books'],
        'successful': successful,
        'failed': failed,
        'in_progress': in_progress,
        'consistent': consistent,
        'local_synced': local_synced,
        'avg_completeness': round(avg_completeness, 1)
    }

    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")
    print(f"  In Progress: {in_progress}")
    print(f"  Consistent: {consistent}")
    print(f"  Local Synced: {local_synced}")

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Complete Sheet Music Lineage Viewer - {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
        }}
        .summary-stat {{
            text-align: center;
            padding: 10px;
        }}
        .summary-stat strong {{
            display: block;
            font-size: 32px;
            margin-bottom: 5px;
        }}
        .summary-stat span {{
            font-size: 13px;
            opacity: 0.9;
        }}
        .filters {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .filters input, .filters select {{
            padding: 8px 12px;
            margin: 5px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .filters input[type="text"] {{
            width: 300px;
        }}
        .filters button {{
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin-left: 10px;
        }}
        .filters button:hover {{
            background: #45a049;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background: #2c3e50;
            color: white;
            padding: 12px;
            text-align: left;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-success {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .status-failed {{
            color: #f44336;
            font-weight: bold;
        }}
        .status-in-progress {{
            color: #ff9800;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: bold;
            margin-right: 3px;
        }}
        .badge-success {{
            background: #4CAF50;
            color: white;
        }}
        .badge-warning {{
            background: #ff9800;
            color: white;
        }}
        .badge-error {{
            background: #f44336;
            color: white;
        }}
        .badge-info {{
            background: #2196F3;
            color: white;
        }}
        .progress-bar {{
            width: 100px;
            height: 18px;
            background: #e0e0e0;
            border-radius: 9px;
            overflow: hidden;
            display: inline-block;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s;
        }}
        .details {{
            font-size: 11px;
            color: #666;
        }}
        .expandable {{
            cursor: pointer;
            color: #2196F3;
            text-decoration: underline;
        }}
        .details-row {{
            display: none;
            background: #f9f9f9;
        }}
        .details-content {{
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }}
        #loading {{
            text-align: center;
            padding: 50px;
            font-size: 18px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Complete Sheet Music Processing Lineage</h1>
        <p>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <div class="summary-stat">
                <strong>{stats['total']}</strong>
                <span>Total Books</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['successful']}</strong>
                <span>Successful</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['failed']}</strong>
                <span>Failed</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['in_progress']}</strong>
                <span>In Progress</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['consistent']}</strong>
                <span>Consistent</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['local_synced']}</strong>
                <span>Local Synced</span>
            </div>
            <div class="summary-stat">
                <strong>{stats['avg_completeness']}%</strong>
                <span>Avg Completeness</span>
            </div>
        </div>

        <div class="filters">
            <input type="text" id="search" placeholder="Search artist or book name...">
            <select id="filter-status">
                <option value="">All Status</option>
                <option value="success">Success</option>
                <option value="failed">Failed</option>
                <option value="in_progress">In Progress</option>
            </select>
            <select id="filter-consistency">
                <option value="">All Consistency</option>
                <option value="CONSISTENT">Consistent</option>
                <option value="INCONSISTENT">Inconsistent</option>
            </select>
            <select id="filter-local">
                <option value="">All Local</option>
                <option value="true">Synced</option>
                <option value="false">Not Synced</option>
            </select>
            <button onclick="applyFilters()">Filter</button>
            <button onclick="clearFilters()">Clear</button>
        </div>

        <div id="loading">Loading data...</div>

        <table id="books-table" style="display: none;">
            <thead>
                <tr>
                    <th>Book ID</th>
                    <th>Artist</th>
                    <th>Book Name</th>
                    <th>Status</th>
                    <th>Completeness</th>
                    <th>Consistency</th>
                    <th>Songs</th>
                    <th>Local</th>
                    <th>Details</th>
                </tr>
            </thead>
            <tbody id="books-tbody">
            </tbody>
        </table>
    </div>

    <script>
        const lineageData = {json.dumps(data, indent=4)};

        let filteredBooks = lineageData.books;

        function renderBooks() {{
            const tbody = document.getElementById('books-tbody');
            tbody.innerHTML = '';

            filteredBooks.forEach((book, index) => {{
                const row = document.createElement('tr');

                const statusClass = book.dynamodb.status === 'success' ? 'status-success' :
                                    book.dynamodb.status === 'failed' ? 'status-failed' : 'status-in-progress';

                const completeness = book.completeness.percentage.toFixed(1);
                const consistency = book.consistency.status;
                const songs = book.dynamodb.songs_extracted || 0;
                const localSynced = book.local.exists;

                row.innerHTML = `
                    <td><code>${{book.book_id}}</code></td>
                    <td>${{book.dynamodb.artist || 'N/A'}}</td>
                    <td>${{book.dynamodb.book_name || 'N/A'}}</td>
                    <td class="${{statusClass}}">${{book.dynamodb.status}}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${{completeness}}%"></div>
                        </div>
                        <span class="details">${{completeness}}%</span>
                    </td>
                    <td>
                        <span class="badge badge-${{consistency === 'CONSISTENT' ? 'success' : 'warning'}}">
                            ${{consistency}}
                        </span>
                    </td>
                    <td>${{songs}}</td>
                    <td>
                        <span class="badge badge-${{localSynced ? 'success' : 'info'}}">
                            ${{localSynced ? 'YES' : 'NO'}}
                        </span>
                    </td>
                    <td>
                        <span class="expandable" onclick="toggleDetails(${{index}})">Show</span>
                    </td>
                `;

                tbody.appendChild(row);

                // Add details row
                const detailsRow = document.createElement('tr');
                detailsRow.className = 'details-row';
                detailsRow.id = `details-${{index}}`;
                detailsRow.innerHTML = `
                    <td colspan="9">
                        <div class="details-content">
                            <strong>S3 Artifacts:</strong>
                            <pre>${{JSON.stringify(book.s3_artifacts, null, 2)}}</pre>
                            <strong>S3 Output:</strong>
                            <pre>${{JSON.stringify(book.s3_output, null, 2)}}</pre>
                            <strong>Consistency Details:</strong>
                            <pre>${{JSON.stringify(book.consistency, null, 2)}}</pre>
                        </div>
                    </td>
                `;
                tbody.appendChild(detailsRow);
            }});
        }}

        function toggleDetails(index) {{
            const detailsRow = document.getElementById(`details-${{index}}`);
            detailsRow.style.display = detailsRow.style.display === 'none' ? 'table-row' : 'none';
        }}

        function applyFilters() {{
            const searchTerm = document.getElementById('search').value.toLowerCase();
            const statusFilter = document.getElementById('filter-status').value;
            const consistencyFilter = document.getElementById('filter-consistency').value;
            const localFilter = document.getElementById('filter-local').value;

            filteredBooks = lineageData.books.filter(book => {{
                const matchesSearch = !searchTerm ||
                    (book.dynamodb.artist && book.dynamodb.artist.toLowerCase().includes(searchTerm)) ||
                    (book.dynamodb.book_name && book.dynamodb.book_name.toLowerCase().includes(searchTerm));

                const matchesStatus = !statusFilter || book.dynamodb.status === statusFilter;
                const matchesConsistency = !consistencyFilter || book.consistency.status === consistencyFilter;
                const matchesLocal = !localFilter ||
                    (localFilter === 'true' && book.local.exists) ||
                    (localFilter === 'false' && !book.local.exists);

                return matchesSearch && matchesStatus && matchesConsistency && matchesLocal;
            }});

            renderBooks();
        }}

        function clearFilters() {{
            document.getElementById('search').value = '';
            document.getElementById('filter-status').value = '';
            document.getElementById('filter-consistency').value = '';
            document.getElementById('filter-local').value = '';
            filteredBooks = lineageData.books;
            renderBooks();
        }}

        // Initialize
        document.getElementById('loading').style.display = 'none';
        document.getElementById('books-table').style.display = 'table';
        renderBooks();
    </script>
</body>
</html>'''

    # Save HTML
    output_file = Path('web/viewers/complete_lineage_viewer.html')
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\n{'='*60}")
    print(f"OK Viewer updated: {output_file}")
    print(f"{'='*60}")
    print(f"Open in browser: file:///{output_file.absolute()}")

if __name__ == '__main__':
    main()
