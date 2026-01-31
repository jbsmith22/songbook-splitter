"""
Build an interactive HTML tree browser for S3 bucket with delete functionality.
"""
import boto3
import json
from collections import defaultdict

def build_tree_structure():
    """Build hierarchical tree structure from S3 bucket."""
    s3 = boto3.client('s3')
    bucket = 'jsmith-output'
    
    print(f"Scanning S3 bucket: {bucket}")
    
    # Get all objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket)
    
    tree = {}
    total_files = 0
    
    for page in pages:
        if 'Contents' not in page:
            continue
            
        for obj in page['Contents']:
            key = obj['Key']
            size = obj['Size']
            total_files += 1
            
            # Build tree structure
            parts = key.split('/')
            current = tree
            
            for i, part in enumerate(parts):
                if part not in current:
                    is_file = (i == len(parts) - 1)
                    current[part] = {
                        '_type': 'file' if is_file else 'folder',
                        '_size': size if is_file else 0,
                        '_path': '/'.join(parts[:i+1])
                    }
                    if not is_file:
                        current[part]['_children'] = {}
                
                if i < len(parts) - 1:
                    current = current[part]['_children']
            
            if total_files % 1000 == 0:
                print(f"  Processed {total_files} files...")
    
    print(f"\nTotal files: {total_files}")
    return tree, total_files

def tree_to_html_nodes(tree, level=0):
    """Convert tree structure to HTML list items."""
    html = []
    
    # Sort: folders first, then files
    items = sorted(tree.items(), key=lambda x: (x[1]['_type'] == 'file', x[0]))
    
    for name, node in items:
        if name.startswith('_'):
            continue
            
        is_file = node['_type'] == 'file'
        path = node['_path']
        
        if is_file:
            size_mb = node['_size'] / (1024 * 1024)
            html.append(f'<li class="file" data-path="{path}">')
            html.append(f'<span class="file-icon">📄</span> {name} ')
            html.append(f'<span class="file-size">({size_mb:.2f} MB)</span>')
            html.append(f'<button class="delete-btn" onclick="deleteItem(\'{path}\', false, this)">🗑️ Delete</button>')
            html.append('</li>')
        else:
            # Count children
            children = node.get('_children', {})
            child_count = len([k for k in children.keys() if not k.startswith('_')])
            
            html.append(f'<li class="folder" data-path="{path}">')
            html.append(f'<span class="folder-toggle" onclick="toggleFolder(this)">▶</span>')
            html.append(f'<span class="folder-icon">📁</span> <strong>{name}</strong> ')
            html.append(f'<span class="item-count">({child_count} items)</span>')
            html.append(f'<button class="compare-btn" onclick="selectForCompare(\'{path}\', this)">📊 Compare</button>')
            html.append(f'<button class="delete-btn delete-folder-btn" onclick="deleteItem(\'{path}\', true, this)">🗑️ Delete Folder</button>')
            html.append(f'<ul class="nested">')
            html.extend(tree_to_html_nodes(children, level + 1))
            html.append('</ul>')
            html.append('</li>')
    
    return html

def generate_html(tree, total_files):
    """Generate complete HTML page."""
    html_nodes = tree_to_html_nodes(tree)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>S3 Bucket Browser - jsmith-output (Interactive) v2.2</title>
    <script defer>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
        
        .header {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        
        .header .stats {{
            color: #666;
            font-size: 14px;
        }}
        
        .header .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            color: #856404;
        }}
        
        .controls {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .controls button {{
            padding: 8px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 4px;
            background: #007bff;
            color: white;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .controls button:hover {{
            background: #0056b3;
        }}
        
        .tree-container {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        
        ul.nested {{
            display: none;
            padding-left: 25px;
        }}
        
        ul.nested.active {{
            display: block;
        }}
        
        li {{
            margin: 5px 0;
            padding: 5px;
            border-radius: 4px;
            position: relative;
        }}
        
        li:hover {{
            background: #f8f9fa;
        }}
        
        li.deleting {{
            opacity: 0.5;
            pointer-events: none;
        }}
        
        .folder-toggle {{
            cursor: pointer;
            display: inline-block;
            width: 20px;
            user-select: none;
            transition: transform 0.2s;
        }}
        
        .folder-toggle.expanded {{
            transform: rotate(90deg);
        }}
        
        .folder-icon, .file-icon {{
            margin: 0 5px;
        }}
        
        .item-count {{
            color: #999;
            font-size: 12px;
            margin-left: 5px;
        }}
        
        .file-size {{
            color: #999;
            font-size: 12px;
            margin-left: 5px;
        }}
        
        .file {{
            color: #555;
        }}
        
        .folder {{
            color: #333;
        }}
        
        .search-box {{
            width: 300px;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        
        .delete-btn {{
            padding: 4px 8px;
            margin-left: 10px;
            border: none;
            border-radius: 4px;
            background: #dc3545;
            color: white;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        
        li:hover .delete-btn {{
            opacity: 1;
        }}
        
        .delete-btn:hover {{
            background: #c82333;
        }}
        
        .delete-folder-btn {{
            background: #ff6b6b;
        }}
        
        .delete-folder-btn:hover {{
            background: #ff5252;
        }}
        
        .compare-btn {{
            padding: 4px 8px;
            margin-left: 10px;
            border: none;
            border-radius: 4px;
            background: #17a2b8;
            color: white;
            cursor: pointer;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        
        li:hover .compare-btn {{
            opacity: 1;
        }}
        
        .compare-btn:hover {{
            background: #138496;
        }}
        
        .compare-btn.selected {{
            opacity: 1;
            background: #ffc107;
            color: #000;
        }}
        
        .compare-panel {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-top: 2px solid #007bff;
            padding: 15px;
            box-shadow: 0 -4px 6px rgba(0,0,0,0.1);
            display: none;
            z-index: 999;
        }}
        
        .compare-panel.active {{
            display: block;
        }}
        
        .compare-panel h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        
        .compare-panel .selected-folders {{
            display: flex;
            gap: 20px;
            margin-bottom: 10px;
        }}
        
        .compare-panel .folder-selection {{
            flex: 1;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        
        .compare-panel .folder-selection strong {{
            display: block;
            margin-bottom: 5px;
            color: #666;
        }}
        
        .compare-panel .folder-path {{
            color: #007bff;
            font-family: monospace;
            font-size: 14px;
        }}
        
        .compare-panel button {{
            padding: 8px 16px;
            margin-right: 10px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .compare-panel .compare-action-btn {{
            background: #28a745;
            color: white;
        }}
        
        .compare-panel .compare-action-btn:hover {{
            background: #218838;
        }}
        
        .compare-panel .compare-action-btn:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}
        
        .compare-panel .cancel-btn {{
            background: #6c757d;
            color: white;
        }}
        
        .compare-panel .cancel-btn:hover {{
            background: #5a6268;
        }}
        
        .compare-results {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 90%;
            max-height: 90%;
            overflow: auto;
            padding: 20px;
            display: none;
            z-index: 1001;
        }}
        
        .compare-results.active {{
            display: block;
        }}
        
        .compare-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: none;
            z-index: 1000;
        }}
        
        .compare-overlay.active {{
            display: block;
        }}
        
        .compare-results h2 {{
            margin: 0 0 20px 0;
            color: #333;
        }}
        
        .compare-results .close-btn {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
        }}
        
        .compare-results .stats {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }}
        
        .compare-results .stat-box {{
            padding: 15px;
            border-radius: 4px;
            text-align: center;
        }}
        
        .compare-results .stat-box.identical {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
        }}
        
        .compare-results .stat-box.different {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
        }}
        
        .compare-results .stat-box.only1 {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
        }}
        
        .compare-results .stat-box.only2 {{
            background: #d1ecf1;
            border: 1px solid #bee5eb;
        }}
        
        .compare-results .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .compare-results .stat-label {{
            font-size: 14px;
            color: #666;
        }}
        
        .compare-results .file-list {{
            margin-top: 20px;
        }}
        
        .compare-results .file-list h3 {{
            margin: 20px 0 10px 0;
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 5px;
        }}
        
        .compare-results .file-item {{
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-family: monospace;
            font-size: 13px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .compare-results .file-item:hover {{
            background: #f8f9fa;
        }}
        
        .compare-results .file-name {{
            flex: 1;
        }}
        
        .compare-results .file-actions {{
            display: flex;
            gap: 5px;
        }}
        
        .compare-results .move-btn {{
            padding: 4px 8px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            white-space: nowrap;
        }}
        
        .compare-results .move-to-1 {{
            background: #17a2b8;
            color: white;
        }}
        
        .compare-results .move-to-1:hover {{
            background: #138496;
        }}
        
        .compare-results .move-to-2 {{
            background: #28a745;
            color: white;
        }}
        
        .compare-results .move-to-2:hover {{
            background: #218838;
        }}
        
        .compare-results .copy-btn {{
            background: #6c757d;
            color: white;
        }}
        
        .compare-results .copy-btn:hover {{
            background: #5a6268;
        }}
        
        .compare-results .file-checkbox {{
            margin-right: 10px;
            cursor: pointer;
        }}
        
        .compare-results .batch-actions {{
            position: sticky;
            top: 0;
            background: white;
            padding: 15px;
            border-bottom: 2px solid #ddd;
            margin: -20px -20px 20px -20px;
            display: flex;
            gap: 10px;
            align-items: center;
            z-index: 10;
        }}
        
        .compare-results .batch-actions button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        
        .compare-results .batch-actions button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        
        .compare-results .batch-move-1 {{
            background: #17a2b8;
            color: white;
        }}
        
        .compare-results .batch-move-1:hover:not(:disabled) {{
            background: #138496;
        }}
        
        .compare-results .batch-move-2 {{
            background: #28a745;
            color: white;
        }}
        
        .compare-results .batch-move-2:hover:not(:disabled) {{
            background: #218838;
        }}
        
        .compare-results .select-all-btn {{
            background: #6c757d;
            color: white;
        }}
        
        .compare-results .select-all-btn:hover {{
            background: #5a6268;
        }}
        
        .compare-results .size-diff {{
            color: #856404;
            font-weight: bold;
            margin-left: 5px;
        }}
        
        .notification {{
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 4px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }}
        
        .notification.success {{
            background: #28a745;
            color: white;
        }}
        
        .notification.error {{
            background: #dc3545;
            color: white;
        }}
        
        @keyframes slideIn {{
            from {{
                transform: translateX(400px);
                opacity: 0;
            }}
            to {{
                transform: translateX(0);
                opacity: 1;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📦 S3 Bucket Browser (Interactive)</h1>
        <div class="stats">
            <strong>Bucket:</strong> jsmith-output<br>
            <strong>Total Files:</strong> {total_files:,}
        </div>
        <div class="warning">
            ⚠️ <strong>Warning:</strong> Delete operations are permanent and cannot be undone!
        </div>
    </div>
    
    <div class="controls">
        <button onclick="expandAll()">Expand All</button>
        <button onclick="collapseAll()">Collapse All</button>
        <button onclick="expandLevel(1)">Expand Level 1</button>
        <button onclick="expandLevel(2)">Expand Level 2</button>
        <input type="text" class="search-box" placeholder="Search folders/files..." onkeyup="searchTree(this.value)">
    </div>
    
    <div class="tree-container">
        <ul id="tree-root">
            {''.join(html_nodes)}
        </ul>
    </div>
    
    <div class="compare-panel" id="comparePanel">
        <h3>📊 Compare Folders</h3>
        <div class="selected-folders">
            <div class="folder-selection">
                <strong>Folder 1:</strong>
                <div class="folder-path" id="folder1Path">Not selected</div>
            </div>
            <div class="folder-selection">
                <strong>Folder 2:</strong>
                <div class="folder-path" id="folder2Path">Not selected</div>
            </div>
        </div>
        <button class="compare-action-btn" id="compareBtn" onclick="compareSelectedFolders()" disabled>Compare Folders</button>
        <button class="cancel-btn" onclick="cancelCompare()">Cancel</button>
    </div>
    
    <div class="compare-overlay" id="compareOverlay" onclick="closeCompareResults()"></div>
    <div class="compare-results" id="compareResults">
        <button class="close-btn" onclick="closeCompareResults()">✕ Close</button>
        <h2>Comparison Results</h2>
        <div id="compareContent"></div>
    </div>
</body>
</html>"""
    
    # Add JavaScript at the beginning, right after body tag
    js_code = """
    <script>
        let selectedFolders = {{
            folder1: null,
            folder2: null
        }};
        
        function toggleFolder(element) {{
            element.classList.toggle('expanded');
            const nested = element.parentElement.querySelector('.nested');
            if (nested) {{
                nested.classList.toggle('active');
            }}
        }}
        
        function expandAll() {{
            document.querySelectorAll('.nested').forEach(el => {{
                el.classList.add('active');
            }});
            document.querySelectorAll('.folder-toggle').forEach(el => {{
                el.classList.add('expanded');
            }});
        }}
        
        function collapseAll() {{
            document.querySelectorAll('.nested').forEach(el => {{
                el.classList.remove('active');
            }});
            document.querySelectorAll('.folder-toggle').forEach(el => {{
                el.classList.remove('expanded');
            }});
        }}
        
        function expandLevel(level) {{
            collapseAll();
            
            function expandToLevel(element, depth) {{
                if (depth >= level) return;
                
                const nested = element.querySelector(':scope > .nested');
                const toggle = element.querySelector(':scope > .folder-toggle');
                
                if (nested && toggle) {{
                    nested.classList.add('active');
                    toggle.classList.add('expanded');
                    
                    const childFolders = nested.querySelectorAll(':scope > .folder');
                    childFolders.forEach(child => {{
                        expandToLevel(child, depth + 1);
                    }});
                }}
            }}
            
            document.querySelectorAll('#tree-root > .folder').forEach(folder => {{
                expandToLevel(folder, 0);
            }});
        }}
        
        function searchTree(query) {{
            query = query.toLowerCase().trim();
            
            if (!query) {{
                document.querySelectorAll('li').forEach(el => {{
                    el.style.display = '';
                }});
                collapseAll();
                return;
            }}
            
            document.querySelectorAll('li').forEach(el => {{
                el.style.display = 'none';
            }});
            
            document.querySelectorAll('li').forEach(el => {{
                const text = el.textContent.toLowerCase();
                if (text.includes(query)) {{
                    let current = el;
                    while (current) {{
                        current.style.display = '';
                        
                        const parentUl = current.parentElement;
                        if (parentUl && parentUl.classList.contains('nested')) {{
                            parentUl.classList.add('active');
                            const parentLi = parentUl.parentElement;
                            if (parentLi) {{
                                const toggle = parentLi.querySelector(':scope > .folder-toggle');
                                if (toggle) {{
                                    toggle.classList.add('expanded');
                                }}
                            }}
                        }}
                        
                        current = current.parentElement?.closest('li');
                    }}
                }}
            }});
        }}
        
        function showNotification(message, isSuccess) {{
            const notification = document.createElement('div');
            notification.className = `notification ${{isSuccess ? 'success' : 'error'}}`;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {{
                notification.remove();
            }}, 3000);
        }}
        
        async function deleteItem(path, isFolder, button) {{
            const itemType = isFolder ? 'folder' : 'file';
            const confirmMessage = isFolder 
                ? `Are you sure you want to delete the folder "${{path}}" and ALL its contents?\\n\\nThis action cannot be undone!`
                : `Are you sure you want to delete "${{path}}"?\\n\\nThis action cannot be undone!`;
            
            if (!confirm(confirmMessage)) {{
                return;
            }}
            
            const listItem = button.closest('li');
            listItem.classList.add('deleting');
            
            try {{
                const response = await fetch('/delete', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        path: path,
                        isFolder: isFolder
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showNotification(result.message, true);
                    listItem.remove();
                }} else {{
                    showNotification(`Error: ${{result.message}}`, false);
                    listItem.classList.remove('deleting');
                }}
            }} catch (error) {{
                showNotification(`Error: ${{error.message}}`, false);
                listItem.classList.remove('deleting');
            }}
        }}
        
        function selectForCompare(path, button) {{
            const comparePanel = document.getElementById('comparePanel');
            comparePanel.classList.add('active');
            
            // Toggle selection
            if (button.classList.contains('selected')) {{
                // Deselect
                button.classList.remove('selected');
                if (selectedFolders.folder1 === path) {{
                    selectedFolders.folder1 = null;
                    document.getElementById('folder1Path').textContent = 'Not selected';
                }} else if (selectedFolders.folder2 === path) {{
                    selectedFolders.folder2 = null;
                    document.getElementById('folder2Path').textContent = 'Not selected';
                }}
            }} else {{
                // Select
                if (!selectedFolders.folder1) {{
                    selectedFolders.folder1 = path;
                    document.getElementById('folder1Path').textContent = path;
                    button.classList.add('selected');
                }} else if (!selectedFolders.folder2) {{
                    selectedFolders.folder2 = path;
                    document.getElementById('folder2Path').textContent = path;
                    button.classList.add('selected');
                }} else {{
                    showNotification('Already selected 2 folders. Deselect one first.', false);
                    return;
                }}
            }}
            
            // Enable compare button if both selected
            const compareBtn = document.getElementById('compareBtn');
            compareBtn.disabled = !(selectedFolders.folder1 && selectedFolders.folder2);
        }}
        
        function cancelCompare() {{
            // Clear selections
            document.querySelectorAll('.compare-btn.selected').forEach(btn => {{
                btn.classList.remove('selected');
            }});
            
            selectedFolders.folder1 = null;
            selectedFolders.folder2 = null;
            document.getElementById('folder1Path').textContent = 'Not selected';
            document.getElementById('folder2Path').textContent = 'Not selected';
            document.getElementById('comparePanel').classList.remove('active');
            document.getElementById('compareBtn').disabled = true;
        }}
        
        async function compareSelectedFolders() {{
            if (!selectedFolders.folder1 || !selectedFolders.folder2) {{
                showNotification('Please select two folders to compare', false);
                return;
            }}
            
            showNotification('Comparing folders... This may take a moment.', true);
            
            try {{
                const response = await fetch('/compare', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        folder1: selectedFolders.folder1,
                        folder2: selectedFolders.folder2
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    displayCompareResults(result);
                }} else {{
                    showNotification(`Error: ${{result.message}}`, false);
                }}
            }} catch (error) {{
                showNotification(`Error: ${{error.message}}`, false);
            }}
        }}
        
        function displayCompareResults(result) {{
            const content = document.getElementById('compareContent');
            
            // Determine which folder has the preferred naming format (Artist - Book)
            const folder1Parts = result.folder1.replace(/\\/g, '/').split('/').filter(p => p);
            const folder2Parts = result.folder2.replace(/\\/g, '/').split('/').filter(p => p);
            
            // Get the last part (book folder name)
            const folder1Book = folder1Parts[folder1Parts.length - 1] || '';
            const folder2Book = folder2Parts[folder2Parts.length - 1] || '';
            
            // Get the second to last part (artist folder name)
            const folder1Artist = folder1Parts[folder1Parts.length - 2] || '';
            const folder2Artist = folder2Parts[folder2Parts.length - 2] || '';
            
            console.log('Folder 1:', folder1Book, 'Artist:', folder1Artist);
            console.log('Folder 2:', folder2Book, 'Artist:', folder2Artist);
            
            // Check if folder name contains " - " (Artist - Book format)
            const folder1HasDash = folder1Book.includes(' - ');
            const folder2HasDash = folder2Book.includes(' - ');
            
            // Also check if it starts with artist name
            const folder1StartsWithArtist = folder1Book.toLowerCase().startsWith(folder1Artist.toLowerCase() + ' -');
            const folder2StartsWithArtist = folder2Book.toLowerCase().startsWith(folder2Artist.toLowerCase() + ' -');
            
            console.log('F1 has dash:', folder1HasDash, 'starts with artist:', folder1StartsWithArtist);
            console.log('F2 has dash:', folder2HasDash, 'starts with artist:', folder2StartsWithArtist);
            
            let preferredFolder = null;
            let preferredDirection = null;
            let preferredName = '';
            
            if ((folder1HasDash || folder1StartsWithArtist) && !folder2HasDash && !folder2StartsWithArtist) {{
                preferredFolder = 1;
                preferredDirection = 'toF1';
                preferredName = folder1Book;
            }} else if ((folder2HasDash || folder2StartsWithArtist) && !folder1HasDash && !folder1StartsWithArtist) {{
                preferredFolder = 2;
                preferredDirection = 'toF2';
                preferredName = folder2Book;
            }}
            
            console.log('Preferred folder:', preferredFolder, 'Direction:', preferredDirection);
            
            let html = `
                <div class="batch-actions">
                    <button class="select-all-btn" onclick="toggleSelectAll('different')">Select All Different</button>
                    <button class="select-all-btn" onclick="toggleSelectAll('only1')">Select All in F1</button>
                    <button class="select-all-btn" onclick="toggleSelectAll('only2')">Select All in F2</button>
                    <button class="select-all-btn" onclick="autoSelectSmart()" style="background: #ffc107; color: #000; font-weight: bold;">🎯 Smart Select</button>
                    <span style="margin-left: auto; color: #666; font-weight: bold;" id="selectedCount">0 selected</span>
                    <button class="batch-move-2" id="batchMoveToF2" onclick="batchMove('toF2')" disabled>Move Selected → F2</button>
                    <button class="batch-move-1" id="batchMoveToF1" onclick="batchMove('toF1')" disabled>Move Selected → F1</button>
                </div>
            `;
            
            if (preferredFolder) {{
                html += `
                    <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 4px;">
                        <strong>🎯 Smart Selection Active:</strong> Folder ${{preferredFolder}} "${{preferredName}}" has the preferred naming format (Artist - Book). 
                        Files are auto-selected to consolidate into this folder. Click "Smart Select" to reapply.
                    </div>
                `;
            }} else {{
                html += `
                    <div style="background: #e7f3ff; border: 1px solid #2196F3; padding: 15px; margin: 10px 0; border-radius: 4px;">
                        <strong>ℹ️ No Preferred Format Detected:</strong> Both folders use similar naming. 
                        Use "Select All" buttons or manually select files to move.
                    </div>
                `;
            }}
            
            html += `
                <div class="stats">
                    <div class="stat-box identical">
                        <div class="stat-number">${{result.stats.identical}}</div>
                        <div class="stat-label">Identical Files</div>
                    </div>
                    <div class="stat-box different">
                        <div class="stat-number">${{result.stats.different}}</div>
                        <div class="stat-label">Different Files</div>
                    </div>
                    <div class="stat-box only1">
                        <div class="stat-number">${{result.stats.only_in_1}}</div>
                        <div class="stat-label">Only in Folder 1</div>
                    </div>
                    <div class="stat-box only2">
                        <div class="stat-number">${{result.stats.only_in_2}}</div>
                        <div class="stat-label">Only in Folder 2</div>
                    </div>
                </div>
                
                <div class="file-list">
            `;
            
            if (result.different.length > 0) {{
                html += '<h3>⚠️ Different Files (Same name, different content)</h3>';
                result.different.forEach((file, idx) => {{
                    const size1MB = (file.size1 / (1024 * 1024)).toFixed(2);
                    const size2MB = (file.size2 / (1024 * 1024)).toFixed(2);
                    const sizeDiff = ((file.size1 - file.size2) / (1024 * 1024)).toFixed(2);
                    const sizeDiffText = sizeDiff > 0 ? `F1 is ${{sizeDiff}}MB larger` : `F2 is ${{Math.abs(sizeDiff)}}MB larger`;
                    const sourcePath1 = result.folder1 + file.path;
                    const sourcePath2 = result.folder2 + file.path;
                    const destPath1 = result.folder1 + file.path;
                    const destPath2 = result.folder2 + file.path;
                    
                    // Auto-select: move smaller file to preferred folder
                    let autoChecked = '';
                    if (preferredDirection) {{
                        if (preferredDirection === 'toF1' && file.size2 < file.size1) {{
                            autoChecked = 'data-auto-select="true"';
                        }} else if (preferredDirection === 'toF2' && file.size1 < file.size2) {{
                            autoChecked = 'data-auto-select="true"';
                        }}
                    }}
                    
                    html += `
                        <div class="file-item" data-category="different">
                            <input type="checkbox" class="file-checkbox" 
                                   data-source-f1="${{sourcePath1}}" 
                                   data-dest-f2="${{destPath2}}"
                                   data-source-f2="${{sourcePath2}}"
                                   data-dest-f1="${{destPath1}}"
                                   ${{autoChecked}}
                                   onchange="updateBatchButtons()">
                            <div class="file-name">
                                ${{file.path}}<br>
                                <span style="font-size: 11px; color: #666;">
                                    F1: ${{size1MB}}MB | F2: ${{size2MB}}MB
                                    <span class="size-diff">(${{sizeDiffText}})</span>
                                </span>
                            </div>
                            <div class="file-actions">
                                <button class="move-btn move-to-2" onclick="moveFile('${{sourcePath1}}', '${{destPath2}}', true, this)" title="Replace in Folder 2">F1→F2</button>
                                <button class="move-btn move-to-1" onclick="moveFile('${{sourcePath2}}', '${{destPath1}}', true, this)" title="Replace in Folder 1">F2→F1</button>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            if (result.only_in_1.length > 0) {{
                html += '<h3>📁 Only in Folder 1</h3>';
                result.only_in_1.forEach((file, idx) => {{
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder1 + file.path;
                    const destPath = result.folder2 + file.path;
                    
                    // Auto-select if F2 is preferred
                    const autoChecked = (preferredDirection === 'toF2') ? 'data-auto-select="true"' : '';
                    
                    html += `
                        <div class="file-item" data-category="only1">
                            <input type="checkbox" class="file-checkbox" 
                                   data-source-f1="${{sourcePath}}" 
                                   data-dest-f2="${{destPath}}"
                                   ${{autoChecked}}
                                   onchange="updateBatchButtons()">
                            <div class="file-name">${{file.path}} (${{sizeMB}}MB)</div>
                            <div class="file-actions">
                                <button class="move-btn move-to-2" onclick="moveFile('${{sourcePath}}', '${{destPath}}', true, this)">Move→F2</button>
                                <button class="move-btn copy-btn" onclick="moveFile('${{sourcePath}}', '${{destPath}}', false, this)">Copy→F2</button>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            if (result.only_in_2.length > 0) {{
                html += '<h3>📁 Only in Folder 2</h3>';
                result.only_in_2.forEach((file, idx) => {{
                    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
                    const sourcePath = result.folder2 + file.path;
                    const destPath = result.folder1 + file.path;
                    
                    // Auto-select if F1 is preferred
                    const autoChecked = (preferredDirection === 'toF1') ? 'data-auto-select="true"' : '';
                    
                    html += `
                        <div class="file-item" data-category="only2">
                            <input type="checkbox" class="file-checkbox" 
                                   data-source-f2="${{sourcePath}}" 
                                   data-dest-f1="${{destPath}}"
                                   ${{autoChecked}}
                                   onchange="updateBatchButtons()">
                            <div class="file-name">${{file.path}} (${{sizeMB}}MB)</div>
                            <div class="file-actions">
                                <button class="move-btn move-to-1" onclick="moveFile('${{sourcePath}}', '${{destPath}}', true, this)">Move→F1</button>
                                <button class="move-btn copy-btn" onclick="moveFile('${{sourcePath}}', '${{destPath}}', false, this)">Copy→F1</button>
                            </div>
                        </div>
                    `;
                }});
            }}
            
            if (result.identical.length > 0) {{
                html += `<h3>✅ Identical Files (${{result.identical.length}} files)</h3>`;
                html += '<div style="color: #666; font-size: 14px; padding: 10px;">Files are byte-for-byte identical (same size and MD5 hash)</div>';
            }}
            
            html += '</div>';
            
            content.innerHTML = html;
            document.getElementById('compareOverlay').classList.add('active');
            document.getElementById('compareResults').classList.add('active');
            
            // Auto-select smart selections on load
            autoSelectSmart();
        }}
        
        function closeCompareResults() {{
            document.getElementById('compareOverlay').classList.remove('active');
            document.getElementById('compareResults').classList.remove('active');
        }}
        
        async function moveFile(sourcePath, destPath, deleteSource, button) {{
            const action = deleteSource ? 'move' : 'copy';
            const confirmMessage = deleteSource 
                ? `Move "${{sourcePath}}" to "${{destPath}}"?\\n\\nThis will delete the source file.`
                : `Copy "${{sourcePath}}" to "${{destPath}}"?`;
            
            if (!confirm(confirmMessage)) {{
                return;
            }}
            
            button.disabled = true;
            button.textContent = deleteSource ? 'Moving...' : 'Copying...';
            
            try {{
                const response = await fetch('/move', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        sourcePath: sourcePath,
                        destPath: destPath,
                        deleteSource: deleteSource
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showNotification(result.message, true);
                    
                    // Remove the file item from the list
                    const fileItem = button.closest('.file-item');
                    fileItem.style.opacity = '0.5';
                    fileItem.style.pointerEvents = 'none';
                    
                    // Suggest re-comparing
                    setTimeout(() => {{
                        if (confirm('File ${{action}}d successfully. Re-compare folders to see updated results?')) {{
                            compareSelectedFolders();
                        }}
                    }}, 500);
                }} else {{
                    showNotification(`Error: ${{result.message}}`, false);
                    button.disabled = false;
                    button.textContent = deleteSource ? 'Move' : 'Copy';
                }}
            }} catch (error) {{
                showNotification(`Error: ${{error.message}}`, false);
                button.disabled = false;
                button.textContent = deleteSource ? 'Move' : 'Copy';
            }}
        }}
        
        function toggleSelectAll(category) {{
            const checkboxes = document.querySelectorAll(`.file-item[data-category="${{category}}"] .file-checkbox`);
            const allChecked = Array.from(checkboxes).every(cb => cb.checked);
            
            checkboxes.forEach(cb => {{
                cb.checked = !allChecked;
            }});
            
            updateBatchButtons();
        }}
        
        function updateBatchButtons() {{
            const checkboxes = document.querySelectorAll('.file-checkbox:checked');
            const count = checkboxes.length;
            
            document.getElementById('selectedCount').textContent = `${{count}} selected`;
            document.getElementById('batchMoveToF2').disabled = count === 0;
            document.getElementById('batchMoveToF1').disabled = count === 0;
        }}
        
        function autoSelectSmart() {{
            // Select all checkboxes marked for auto-selection
            const autoCheckboxes = document.querySelectorAll('.file-checkbox[data-auto-select="true"]');
            autoCheckboxes.forEach(cb => {{
                cb.checked = true;
            }});
            updateBatchButtons();
        }}
        
        async function batchMove(direction) {{
            const checkboxes = document.querySelectorAll('.file-checkbox:checked');
            
            if (checkboxes.length === 0) {{
                showNotification('No files selected', false);
                return;
            }}
            
            const operations = [];
            checkboxes.forEach(cb => {{
                if (direction === 'toF2' && cb.dataset.sourceF1) {{
                    operations.push({{
                        sourcePath: cb.dataset.sourceF1,
                        destPath: cb.dataset.destF2,
                        deleteSource: true
                    }});
                }} else if (direction === 'toF1' && cb.dataset.sourceF2) {{
                    operations.push({{
                        sourcePath: cb.dataset.sourceF2,
                        destPath: cb.dataset.destF1,
                        deleteSource: true
                    }});
                }}
            }});
            
            if (operations.length === 0) {{
                showNotification('No valid operations for selected files', false);
                return;
            }}
            
            const targetFolder = direction === 'toF2' ? 'Folder 2' : 'Folder 1';
            if (!confirm(`Move ${{operations.length}} file(s) to ${{targetFolder}}?\\n\\nThis will delete the source files.`)) {{
                return;
            }}
            
            // Disable buttons during operation
            document.getElementById('batchMoveToF2').disabled = true;
            document.getElementById('batchMoveToF1').disabled = true;
            document.getElementById('batchMoveToF2').textContent = 'Moving...';
            document.getElementById('batchMoveToF1').textContent = 'Moving...';
            
            showNotification(`Moving ${{operations.length}} files...`, true);
            
            try {{
                const response = await fetch('/batch-move', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        operations: operations
                    }})
                }});
                
                const result = await response.json();
                
                if (result.success) {{
                    showNotification(result.message, true);
                    
                    // Remove successfully moved items
                    checkboxes.forEach(cb => {{
                        const fileItem = cb.closest('.file-item');
                        fileItem.style.opacity = '0.5';
                        fileItem.style.pointerEvents = 'none';
                    }});
                    
                    // Suggest re-comparing
                    setTimeout(() => {{
                        if (confirm('Batch move complete. Re-compare folders to see updated results?')) {{
                            compareSelectedFolders();
                        }}
                    }}, 1000);
                }} else {{
                    showNotification(`Error: ${{result.message}}`, false);
                }}
            }} catch (error) {{
                showNotification(`Error: ${{error.message}}`, false);
            }} finally {{
                document.getElementById('batchMoveToF2').textContent = 'Move Selected → F2';
                document.getElementById('batchMoveToF1').textContent = 'Move Selected → F1';
            }}
        }}
        
        // Initialize: collapse all on load
        collapseAll();
    </script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            padding: 20px;
            background: #f5f5f5;
        }}
    
    return html

def main():
    print("Building S3 tree structure...")
    tree, total_files = build_tree_structure()
    
    print("Generating HTML...")
    html = generate_html(tree, total_files)
    
    output_file = 's3_bucket_browser_interactive.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ Created {output_file}")
    print(f"\nTo use the interactive browser with delete functionality:")
    print(f"   py s3_browser_server.py")

if __name__ == '__main__':
    main()
