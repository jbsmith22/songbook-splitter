#!/usr/bin/env python3
"""
Comprehensive Data Verification for All Songbooks
Physically verifies every piece of data and metadata for all 559 songbooks.
"""

import json
import os
import hashlib
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import csv

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Paths
PROJECT_ROOT = Path("D:/Work/songbook-splitter")
SHEETMUSIC_DIR = PROJECT_ROOT / "SheetMusic"
PROCESSED_DIR = PROJECT_ROOT / "ProcessedSongs_Final"
CACHE_DIR = Path("S:/SlowImageCache/pdf_verification_v2")
PRERENDER_RESULTS = PROJECT_ROOT / "prerender_results.json"
OUTPUT_DIR = PROJECT_ROOT / "data/verification"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# S3 buckets
S3_INPUT = "s3://jsmith-input"
S3_OUTPUT = "s3://jsmith-output"
DYNAMODB_TABLE = "jsmith-processing-ledger"


def get_file_md5(filepath: Path) -> Optional[str]:
    """Calculate MD5 checksum of a file."""
    try:
        md5_hash = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    except Exception as e:
        return None


def get_file_size(filepath: Path) -> Optional[int]:
    """Get file size in bytes."""
    try:
        return filepath.stat().st_size
    except:
        return None


def count_files_in_dir(dirpath: Path, pattern: str = "*") -> int:
    """Count files matching pattern in directory."""
    try:
        return len(list(dirpath.glob(pattern)))
    except:
        return 0


def run_aws_command(cmd: List[str]) -> Optional[str]:
    """Run AWS CLI command and return output."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except:
        return None


def check_s3_file(s3_uri: str) -> Optional[Dict[str, Any]]:
    """Check if S3 file exists and get metadata."""
    try:
        output = run_aws_command(["aws", "s3", "ls", s3_uri, "--recursive"])
        if output:
            # Parse output: "2026-02-03 22:47:30    2891666 path/to/file.pdf"
            lines = output.strip().split('\n')
            if lines and lines[0]:
                parts = lines[0].split()
                if len(parts) >= 3:
                    return {
                        "exists": True,
                        "size": int(parts[2]),
                        "date": f"{parts[0]} {parts[1]}"
                    }
        return {"exists": False}
    except:
        return {"exists": False}


def get_s3_folder_contents(s3_path: str) -> List[str]:
    """List contents of S3 folder."""
    try:
        output = run_aws_command(["aws", "s3", "ls", s3_path, "--recursive"])
        if output:
            return output.strip().split('\n')
        return []
    except:
        return []


def get_dynamodb_item(book_id: str) -> Optional[Dict[str, Any]]:
    """Get DynamoDB item for book_id."""
    try:
        output = run_aws_command([
            "aws", "dynamodb", "get-item",
            "--table-name", DYNAMODB_TABLE,
            "--key", json.dumps({"book_id": {"S": book_id}}),
            "--output", "json"
        ])
        if output:
            data = json.loads(output)
            return data.get("Item", {})
        return None
    except:
        return None


def read_json_file(filepath: Path) -> Optional[Dict[str, Any]]:
    """Read and parse JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def read_s3_json(s3_uri: str) -> Optional[Dict[str, Any]]:
    """Read JSON file from S3."""
    try:
        output = run_aws_command(["aws", "s3", "cp", s3_uri, "-"])
        if output:
            return json.loads(output)
        return None
    except:
        return None


def verify_songbook(book_info: Dict[str, Any]) -> Dict[str, Any]:
    """Comprehensively verify all data for a single songbook."""

    book_id = book_info["book_id"]
    artist = book_info["artist"]
    book_name = book_info["book_name"]

    print(f"Verifying: {artist} - {book_name}")

    result = {
        "book_id": book_id,
        "artist": artist,
        "book_name": book_name,
        "verification_timestamp": datetime.now().isoformat(),
        "status": "complete"
    }

    # 1. Original Source PDF
    source_path = SHEETMUSIC_DIR / artist / f"{artist} - {book_name}.pdf"
    if not source_path.exists():
        # Try without artist prefix
        source_path = SHEETMUSIC_DIR / artist / f"{book_name}.pdf"

    result["source_pdf"] = {
        "exists": source_path.exists(),
        "path": str(source_path) if source_path.exists() else None,
        "size": get_file_size(source_path) if source_path.exists() else None,
        "md5": get_file_md5(source_path) if source_path.exists() else None
    }

    # 2. Local Copy of Source PDF
    local_copy_paths = [
        PROCESSED_DIR / artist / f"{artist} - {book_name}.pdf",
        PROCESSED_DIR / artist / f"{book_name}.pdf"
    ]
    local_copy = None
    for path in local_copy_paths:
        if path.exists():
            local_copy = path
            break

    result["local_copy"] = {
        "exists": local_copy is not None,
        "path": str(local_copy) if local_copy else None,
        "size": get_file_size(local_copy) if local_copy else None,
        "md5": get_file_md5(local_copy) if local_copy else None,
        "matches_source": (get_file_md5(local_copy) == result["source_pdf"]["md5"]) if local_copy and result["source_pdf"]["md5"] else None
    }

    # 3. S3 Source PDF
    s3_source_uri = f"{S3_INPUT}/{artist}/{artist} - {book_name}.pdf"
    result["s3_source"] = check_s3_file(s3_source_uri)
    result["s3_source"]["uri"] = s3_source_uri

    # 4. Local Processed Folder
    processed_folders = [
        PROCESSED_DIR / artist / f"{artist} - {book_name}",
        PROCESSED_DIR / artist / book_name
    ]
    processed_folder = None
    for folder in processed_folders:
        if folder.exists():
            processed_folder = folder
            break

    # 5. Local Manifest
    manifest_path = processed_folder / "manifest.json" if processed_folder else None
    manifest_data = read_json_file(manifest_path) if manifest_path and manifest_path.exists() else None

    result["local_manifest"] = {
        "exists": manifest_data is not None,
        "path": str(manifest_path) if manifest_path else None,
        "song_count": manifest_data.get("total_songs") if manifest_data else None,
        "data": manifest_data
    }

    # 6. Local Page Analysis
    page_analysis_path = processed_folder / "page_analysis.json" if processed_folder else None
    page_analysis_data = read_json_file(page_analysis_path) if page_analysis_path and page_analysis_path.exists() else None

    result["local_page_analysis"] = {
        "exists": page_analysis_data is not None,
        "path": str(page_analysis_path) if page_analysis_path else None,
        "total_pages": page_analysis_data.get("total_pages") if page_analysis_data else None,
        "data": page_analysis_data
    }

    # 7. Local Extracted Songs
    local_song_count = 0
    if processed_folder and processed_folder.exists():
        local_song_count = count_files_in_dir(processed_folder, "*.pdf")

    result["local_songs"] = {
        "folder_exists": processed_folder is not None and processed_folder.exists(),
        "count": local_song_count
    }

    # 8. Cached Page Images
    cache_paths = [
        CACHE_DIR / artist / f"{artist} - {book_name}",
        CACHE_DIR / artist / book_name
    ]
    cache_folder = None
    for path in cache_paths:
        if path.exists():
            cache_folder = path
            break

    cache_count = count_files_in_dir(cache_folder, "*.jpg") if cache_folder else 0

    result["cached_images"] = {
        "folder_exists": cache_folder is not None,
        "count": cache_count,
        "expected_count": book_info.get("pages_cached", 0),
        "matches": cache_count == book_info.get("pages_cached", 0)
    }

    # 9. S3 Output Songs
    s3_output_paths = [
        f"{S3_OUTPUT}/{artist}/{artist} - {book_name}/",
        f"{S3_OUTPUT}/{artist}/{book_name}/"
    ]

    s3_output_files = []
    for path in s3_output_paths:
        files = get_s3_folder_contents(path)
        if files:
            s3_output_files = files
            break

    result["s3_output_songs"] = {
        "exists": len(s3_output_files) > 0,
        "count": len([f for f in s3_output_files if f.strip()]),
        "files": s3_output_files
    }

    # 10. S3 Manifest
    s3_manifest_uri = f"{S3_OUTPUT}/output/{book_id}/manifest.json"
    s3_manifest_data = read_s3_json(s3_manifest_uri)

    result["s3_manifest"] = {
        "exists": s3_manifest_data is not None,
        "uri": s3_manifest_uri,
        "is_complete": bool(s3_manifest_data and s3_manifest_data.get("output")) if s3_manifest_data else False,
        "data": s3_manifest_data
    }

    # 11. S3 Artifacts
    artifacts_path = f"{S3_OUTPUT}/artifacts/{book_id}/"
    artifact_files = get_s3_folder_contents(artifacts_path)

    artifacts = {
        "page_analysis": any("page_analysis.json" in f for f in artifact_files),
        "toc_discovery": any("toc_discovery.json" in f for f in artifact_files),
        "verified_songs": any("verified_songs.json" in f for f in artifact_files),
        "output_files": any("output_files.json" in f for f in artifact_files),
        "page_mapping": any("page_mapping.json" in f for f in artifact_files),
        "toc_parse": any("toc_parse.json" in f for f in artifact_files)
    }

    result["s3_artifacts"] = {
        "folder_exists": len(artifact_files) > 0,
        "files": artifacts,
        "count": sum(artifacts.values())
    }

    # 12. DynamoDB Entry
    dynamo_data = get_dynamodb_item(book_id)

    result["dynamodb"] = {
        "exists": dynamo_data is not None,
        "songs_extracted": int(dynamo_data.get("songs_extracted", {}).get("N", 0)) if dynamo_data else None,
        "status": dynamo_data.get("status", {}).get("S") if dynamo_data else None,
        "data": dynamo_data
    }

    # Calculate overall status
    issues = []
    if not result["source_pdf"]["exists"]:
        issues.append("missing_source")
    if not result["local_manifest"]["exists"]:
        issues.append("missing_manifest")
    if not result["cached_images"]["matches"]:
        issues.append("cache_mismatch")
    if result["local_songs"]["count"] != result["s3_output_songs"]["count"]:
        issues.append("song_count_mismatch")

    result["issues"] = issues
    result["has_issues"] = len(issues) > 0

    return result


def generate_html_report(results: List[Dict[str, Any]], output_path: Path):
    """Generate interactive HTML report."""

    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Songbook Data Verification Report</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
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
        h1 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value {
            font-size: 32px;
            font-weight: bold;
            color: #2196F3;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .filters {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .filter-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }
        .filter-btn {
            padding: 8px 16px;
            border: 1px solid #ddd;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s;
        }
        .filter-btn:hover {
            background: #f0f0f0;
        }
        .filter-btn.active {
            background: #2196F3;
            color: white;
            border-color: #2196F3;
        }
        .search-box {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .book-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .book-card.has-issues {
            border-left: 4px solid #f44336;
        }
        .book-card.no-issues {
            border-left: 4px solid #4CAF50;
        }
        .book-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            cursor: pointer;
        }
        .book-title {
            font-size: 18px;
            font-weight: bold;
            color: #333;
        }
        .book-id {
            font-size: 12px;
            color: #999;
            margin-top: 2px;
        }
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
        }
        .status-ok {
            background: #4CAF50;
            color: white;
        }
        .status-issues {
            background: #f44336;
            color: white;
        }
        .book-details {
            display: none;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #eee;
        }
        .book-details.expanded {
            display: block;
        }
        .detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }
        .detail-section {
            background: #f9f9f9;
            padding: 12px;
            border-radius: 4px;
        }
        .detail-title {
            font-weight: bold;
            margin-bottom: 8px;
            color: #555;
        }
        .detail-item {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 13px;
        }
        .detail-label {
            color: #666;
        }
        .detail-value {
            color: #333;
            font-weight: 500;
        }
        .check-mark {
            color: #4CAF50;
        }
        .x-mark {
            color: #f44336;
        }
        .issue-list {
            margin-top: 10px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 4px;
        }
        .issue-item {
            color: #856404;
            font-size: 13px;
        }
        .expand-icon {
            transition: transform 0.2s;
        }
        .expand-icon.expanded {
            transform: rotate(180deg);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Songbook Data Verification Report</h1>
        <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-value" id="total-books">""" + str(len(results)) + """</div>
            <div class="stat-label">Total Books</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="books-ok" style="color: #4CAF50;">0</div>
            <div class="stat-label">Complete & Verified</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="books-issues" style="color: #f44336;">0</div>
            <div class="stat-label">With Issues</div>
        </div>
    </div>

    <div class="filters">
        <input type="text" class="search-box" id="search" placeholder="Search by artist or book name...">
        <div class="filter-group">
            <button class="filter-btn active" data-filter="all">All Books</button>
            <button class="filter-btn" data-filter="no-issues">No Issues</button>
            <button class="filter-btn" data-filter="has-issues">With Issues</button>
        </div>
    </div>

    <div id="books-container">
"""

    for book in results:
        issues_class = "has-issues" if book["has_issues"] else "no-issues"
        status_class = "status-issues" if book["has_issues"] else "status-ok"
        status_text = f"{len(book['issues'])} Issues" if book["has_issues"] else "✓ Complete"

        html += f"""
        <div class="book-card {issues_class}" data-artist="{book['artist']}" data-book="{book['book_name']}">
            <div class="book-header" onclick="toggleDetails(this)">
                <div>
                    <div class="book-title">{book['artist']} - {book['book_name']}</div>
                    <div class="book-id">{book['book_id']}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="status-badge {status_class}">{status_text}</span>
                    <span class="expand-icon">▼</span>
                </div>
            </div>
            <div class="book-details">
                <div class="detail-grid">
                    <div class="detail-section">
                        <div class="detail-title">Source Files</div>
                        <div class="detail-item">
                            <span class="detail-label">Original PDF:</span>
                            <span class="detail-value">{'✓' if book['source_pdf']['exists'] else '✗'} {book['source_pdf']['size'] or 'N/A'} bytes</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Local Copy:</span>
                            <span class="detail-value">{'✓' if book['local_copy']['exists'] else '✗'} {'(matches)' if book['local_copy'].get('matches_source') else ''}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">S3 Source:</span>
                            <span class="detail-value">{'✓' if book['s3_source']['exists'] else '✗'} {book['s3_source'].get('size', 'N/A')} bytes</span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <div class="detail-title">Local Data</div>
                        <div class="detail-item">
                            <span class="detail-label">Manifest:</span>
                            <span class="detail-value">{'✓' if book['local_manifest']['exists'] else '✗'} {book['local_manifest']['song_count'] or '0'} songs</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Page Analysis:</span>
                            <span class="detail-value">{'✓' if book['local_page_analysis']['exists'] else '✗'} {book['local_page_analysis']['total_pages'] or '0'} pages</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Extracted Songs:</span>
                            <span class="detail-value">{book['local_songs']['count']} PDFs</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Cached Images:</span>
                            <span class="detail-value">{book['cached_images']['count']} / {book['cached_images']['expected_count']} {'✓' if book['cached_images']['matches'] else '✗'}</span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <div class="detail-title">S3 Data</div>
                        <div class="detail-item">
                            <span class="detail-label">Output Songs:</span>
                            <span class="detail-value">{'✓' if book['s3_output_songs']['exists'] else '✗'} {book['s3_output_songs']['count']} files</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">S3 Manifest:</span>
                            <span class="detail-value">{'✓' if book['s3_manifest']['exists'] else '✗'} {'(complete)' if book['s3_manifest'].get('is_complete') else '(minimal)'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Artifacts:</span>
                            <span class="detail-value">{book['s3_artifacts']['count']} / 6 files</span>
                        </div>
                    </div>

                    <div class="detail-section">
                        <div class="detail-title">DynamoDB</div>
                        <div class="detail-item">
                            <span class="detail-label">Entry Exists:</span>
                            <span class="detail-value">{'✓' if book['dynamodb']['exists'] else '✗'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Status:</span>
                            <span class="detail-value">{book['dynamodb']['status'] or 'N/A'}</span>
                        </div>
                        <div class="detail-item">
                            <span class="detail-label">Songs Extracted:</span>
                            <span class="detail-value">{book['dynamodb']['songs_extracted'] or '0'}</span>
                        </div>
                    </div>
                </div>
"""

        if book["has_issues"]:
            html += """
                <div class="issue-list">
                    <strong>Issues Found:</strong>
"""
            for issue in book["issues"]:
                html += f'                    <div class="issue-item">• {issue.replace("_", " ").title()}</div>\n'
            html += """
                </div>
"""

        html += """
            </div>
        </div>
"""

    html += """
    </div>

    <script>
        // Calculate stats
        const books = document.querySelectorAll('.book-card');
        const booksWithIssues = document.querySelectorAll('.book-card.has-issues').length;
        const booksOk = books.length - booksWithIssues;

        document.getElementById('books-ok').textContent = booksOk;
        document.getElementById('books-issues').textContent = booksWithIssues;

        // Toggle details
        function toggleDetails(header) {
            const details = header.nextElementSibling;
            const icon = header.querySelector('.expand-icon');
            details.classList.toggle('expanded');
            icon.classList.toggle('expanded');
        }

        // Filter functionality
        const filterBtns = document.querySelectorAll('.filter-btn');
        filterBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                filterBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const filter = btn.dataset.filter;
                books.forEach(book => {
                    if (filter === 'all') {
                        book.style.display = 'block';
                    } else if (filter === 'no-issues' && book.classList.contains('no-issues')) {
                        book.style.display = 'block';
                    } else if (filter === 'has-issues' && book.classList.contains('has-issues')) {
                        book.style.display = 'block';
                    } else {
                        book.style.display = 'none';
                    }
                });
            });
        });

        // Search functionality
        const searchBox = document.getElementById('search');
        searchBox.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            books.forEach(book => {
                const artist = book.dataset.artist.toLowerCase();
                const bookName = book.dataset.book.toLowerCase();
                if (artist.includes(query) || bookName.includes(query)) {
                    book.style.display = 'block';
                } else {
                    book.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_markdown_report(results: List[Dict[str, Any]], output_path: Path):
    """Generate markdown summary report."""

    total = len(results)
    with_issues = sum(1 for r in results if r["has_issues"])
    without_issues = total - with_issues

    md = f"""# Songbook Data Verification Report

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics

- **Total Books:** {total}
- **Complete & Verified:** {without_issues} ({without_issues/total*100:.1f}%)
- **With Issues:** {with_issues} ({with_issues/total*100:.1f}%)

## Books with Issues

"""

    for book in results:
        if book["has_issues"]:
            md += f"""### {book['artist']} - {book['book_name']}
**Book ID:** `{book['book_id']}`

**Issues:**
"""
            for issue in book["issues"]:
                md += f"- {issue.replace('_', ' ').title()}\n"

            md += f"""
**Data Status:**
- Source PDF: {'✓' if book['source_pdf']['exists'] else '✗'}
- Local Manifest: {'✓' if book['local_manifest']['exists'] else '✗'} ({book['local_manifest']['song_count'] or 0} songs)
- Cached Images: {book['cached_images']['count']} / {book['cached_images']['expected_count']}
- S3 Output Songs: {book['s3_output_songs']['count']}
- S3 Artifacts: {book['s3_artifacts']['count']} / 6
- DynamoDB: {'✓' if book['dynamodb']['exists'] else '✗'} ({book['dynamodb']['status'] or 'N/A'})

---

"""

    md += f"""
## Complete Books

{without_issues} books have complete and verified data with no issues.

"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md)


def generate_csv_report(results: List[Dict[str, Any]], output_path: Path):
    """Generate CSV report for data analysis."""

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            'Book ID', 'Artist', 'Book Name',
            'Source PDF Exists', 'Source PDF Size',
            'Local Copy Exists', 'Local Copy Matches',
            'S3 Source Exists', 'S3 Source Size',
            'Local Manifest Exists', 'Local Songs Count',
            'Local Page Analysis Exists',
            'Cached Images Count', 'Cached Images Match',
            'S3 Output Songs Count',
            'S3 Manifest Exists', 'S3 Manifest Complete',
            'S3 Artifacts Count',
            'DynamoDB Exists', 'DynamoDB Status', 'DynamoDB Songs Count',
            'Has Issues', 'Issues'
        ])

        # Data rows
        for book in results:
            writer.writerow([
                book['book_id'],
                book['artist'],
                book['book_name'],
                book['source_pdf']['exists'],
                book['source_pdf']['size'] or '',
                book['local_copy']['exists'],
                book['local_copy'].get('matches_source', ''),
                book['s3_source']['exists'],
                book['s3_source'].get('size', ''),
                book['local_manifest']['exists'],
                book['local_songs']['count'],
                book['local_page_analysis']['exists'],
                book['cached_images']['count'],
                book['cached_images']['matches'],
                book['s3_output_songs']['count'],
                book['s3_manifest']['exists'],
                book['s3_manifest'].get('is_complete', False),
                book['s3_artifacts']['count'],
                book['dynamodb']['exists'],
                book['dynamodb']['status'] or '',
                book['dynamodb']['songs_extracted'] or '',
                book['has_issues'],
                '; '.join(book['issues'])
            ])


def main():
    """Main verification process."""

    print("=" * 80)
    print("COMPREHENSIVE SONGBOOK DATA VERIFICATION")
    print("=" * 80)
    print()

    # Load prerender results
    print("Loading songbook list...")
    with open(PRERENDER_RESULTS, 'r') as f:
        prerender_data = json.load(f)

    books = prerender_data["books"]
    total = len(books)

    print(f"Found {total} songbooks to verify")
    print()

    # Verify each book
    results = []
    checkpoint_interval = 10

    for i, book in enumerate(books, 1):
        print(f"[{i}/{total}] ", end="", flush=True)
        try:
            result = verify_songbook(book)
            results.append(result)

            # Save checkpoint every 10 books
            if i % checkpoint_interval == 0:
                checkpoint_path = OUTPUT_DIR / f"checkpoint_{i}.json"
                with open(checkpoint_path, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2)
                print(f"\nCheckpoint saved at {i} books", flush=True)

        except Exception as e:
            print(f"ERROR: {e}", flush=True)
            results.append({
                "book_id": book.get("book_id", "unknown"),
                "artist": book.get("artist", "unknown"),
                "book_name": book.get("book_name", "unknown"),
                "status": "error",
                "error": str(e),
                "has_issues": True,
                "issues": ["verification_error"]
            })

    print()
    print("=" * 80)
    print("GENERATING REPORTS")
    print("=" * 80)
    print()

    # Save detailed JSON
    json_path = OUTPUT_DIR / "verification_results_full.json"
    print(f"Saving detailed JSON: {json_path}")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

    # Generate HTML report
    html_path = OUTPUT_DIR / "verification_report.html"
    print(f"Generating HTML report: {html_path}")
    generate_html_report(results, html_path)

    # Generate Markdown report
    md_path = OUTPUT_DIR / "verification_report.md"
    print(f"Generating Markdown report: {md_path}")
    generate_markdown_report(results, md_path)

    # Generate CSV report
    csv_path = OUTPUT_DIR / "verification_report.csv"
    print(f"Generating CSV report: {csv_path}")
    generate_csv_report(results, csv_path)

    print()
    print("=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Total books: {total}")
    print(f"With issues: {sum(1 for r in results if r['has_issues'])}")
    print(f"Complete: {sum(1 for r in results if not r['has_issues'])}")
    print()
    print(f"Reports saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
